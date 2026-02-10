"""
Anthropic Claude Client for LCS Engine

Wrapper around the Anthropic SDK for personalized AI tutoring.
Includes retry logic with exponential backoff for resilience.
"""

import asyncio
import logging
from typing import AsyncGenerator, Optional

import anthropic

from ..settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class AnthropicClient:
    """Wrapper around Anthropic SDK for LCS Engine AI chat with retry logic."""

    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 2, 4]  # Exponential backoff seconds

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.anthropic_api_key
        self.model = settings.anthropic_model
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None

    def is_configured(self) -> bool:
        """Check if the client is properly configured with an API key."""
        return bool(self.api_key and self.client)

    def _is_permanent_error(self, error) -> bool:
        """Errors that should NOT be retried."""
        error_name = type(error).__name__
        return error_name in [
            "AuthenticationError",
            "BadRequestError",
            "PermissionDeniedError",
        ]

    def _get_retry_delay(self, error, attempt: int) -> float:
        """Get delay before next retry. Respect rate limit headers."""
        if hasattr(error, "response") and error.response is not None:
            retry_after = getattr(error.response, "headers", {}).get("retry-after")
            if retry_after:
                try:
                    return float(retry_after)
                except (ValueError, TypeError):
                    pass
        return self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)]

    async def chat_stream(
        self,
        messages: list[dict],
        system_prompt: str,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response token by token with retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: The system prompt for personalization
            max_tokens: Maximum tokens in response

        Yields:
            Text chunks as they arrive from the API
        """
        if not self.is_configured():
            yield "I apologize, but the AI service is not currently configured. Please contact support."
            return

        last_error = None

        for attempt in range(self.MAX_RETRIES):
            try:
                # Use the synchronous streaming API (Anthropic SDK handles this well)
                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=messages
                ) as stream:
                    for text in stream.text_stream:
                        yield text
                return  # Success - exit retry loop

            except Exception as e:
                last_error = e
                error_type = type(e).__name__

                # Don't retry on permanent errors
                if self._is_permanent_error(e):
                    logger.error(f"Permanent API error: {error_type}: {e}")
                    raise

                # Retry on transient errors
                if attempt < self.MAX_RETRIES - 1:
                    delay = self._get_retry_delay(e, attempt)
                    logger.warning(
                        f"API attempt {attempt + 1} failed ({error_type}), retrying in {delay}s"
                    )
                    await asyncio.sleep(delay)

        # All retries exhausted
        logger.error(f"API failed after {self.MAX_RETRIES} attempts: {last_error}")
        raise last_error

    async def chat(
        self,
        messages: list[dict],
        system_prompt: str,
        max_tokens: int = 1024
    ) -> str:
        """
        Non-streaming chat for internal use (e.g., title generation) with retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: The system prompt
            max_tokens: Maximum tokens in response

        Returns:
            The complete response text
        """
        if not self.is_configured():
            return "Untitled Conversation"

        last_error = None

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=messages
                )
                return response.content[0].text if response.content else ""

            except Exception as e:
                last_error = e
                error_type = type(e).__name__

                # Don't retry on permanent errors
                if self._is_permanent_error(e):
                    logger.error(f"Permanent API error: {error_type}: {e}")
                    raise

                # Retry on transient errors
                if attempt < self.MAX_RETRIES - 1:
                    delay = self._get_retry_delay(e, attempt)
                    logger.warning(
                        f"API attempt {attempt + 1} failed ({error_type}), retrying in {delay}s"
                    )
                    await asyncio.sleep(delay)

        # All retries exhausted
        logger.error(f"API failed after {self.MAX_RETRIES} attempts: {last_error}")
        raise last_error

    async def generate_title(self, first_message: str, first_response: str) -> str:
        """
        Generate a short title for a conversation based on the first exchange.

        Args:
            first_message: The user's first message
            first_response: The AI's first response

        Returns:
            A 3-5 word title for the conversation
        """
        if not self.is_configured():
            return "New Conversation"

        prompt = f"""Generate a very short title (3-5 words max) for this conversation.
The title should capture the main topic. No quotes, no punctuation at the end.

User: {first_message[:200]}
Assistant: {first_response[:200]}

Title:"""

        try:
            # Use the chat method which has retry logic built in
            title = await self.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a helpful assistant that generates short conversation titles.",
                max_tokens=20
            )
            # Clean up the title
            title = title.strip().replace('"', '').replace("'", "").strip()
            # Limit length
            if len(title) > 50:
                title = title[:47] + "..."
            return title if title else "New Conversation"
        except Exception as e:
            logger.warning(f"Failed to generate title: {e}")
            return "New Conversation"

    async def chat_json(
        self,
        messages: list[dict],
        system_prompt: str,
        max_tokens: int = 2048
    ) -> dict:
        """
        Chat expecting JSON response. Used by strategy engine.
        Retries once if JSON is malformed.

        Args:
            messages: List of message dicts
            system_prompt: System prompt (should request JSON output)
            max_tokens: Maximum tokens

        Returns:
            Parsed JSON response as dict
        """
        import json

        response = await self.chat(messages, system_prompt, max_tokens)
        cleaned = self._clean_json_response(response)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Retry once with stronger instruction
            logger.warning("JSON parse failed, retrying with stronger instruction")
            retry_messages = messages + [
                {"role": "assistant", "content": response},
                {"role": "user", "content": "That was not valid JSON. Please respond with ONLY valid JSON, no other text."}
            ]
            retry_response = await self.chat(retry_messages, system_prompt, max_tokens)
            cleaned = self._clean_json_response(retry_response)
            return json.loads(cleaned)

    def _clean_json_response(self, response: str) -> str:
        """Clean up JSON response by removing markdown code blocks."""
        cleaned = response.strip()
        if cleaned.startswith("```"):
            # Remove opening fence (possibly with language identifier)
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            # Remove closing fence
            if "```" in cleaned:
                cleaned = cleaned.rsplit("```", 1)[0]
        return cleaned.strip()

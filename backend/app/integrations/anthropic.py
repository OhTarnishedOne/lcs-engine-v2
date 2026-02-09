"""
Anthropic Claude Client for LCS Engine

Wrapper around the Anthropic SDK for personalized AI tutoring.
"""

from typing import AsyncGenerator, Optional
import anthropic

from ..settings import get_settings

settings = get_settings()


class AnthropicClient:
    """Wrapper around Anthropic SDK for LCS Engine AI chat."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.anthropic_api_key
        self.model = settings.anthropic_model
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None

    def is_configured(self) -> bool:
        """Check if the client is properly configured with an API key."""
        return bool(self.api_key and self.client)

    async def chat_stream(
        self,
        messages: list[dict],
        system_prompt: str,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response token by token.

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

        # Use the synchronous streaming API (Anthropic SDK handles this well)
        with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages
        ) as stream:
            for text in stream.text_stream:
                yield text

    async def chat(
        self,
        messages: list[dict],
        system_prompt: str,
        max_tokens: int = 1024
    ) -> str:
        """
        Non-streaming chat for internal use (e.g., title generation).

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: The system prompt
            max_tokens: Maximum tokens in response

        Returns:
            The complete response text
        """
        if not self.is_configured():
            return "Untitled Conversation"

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages
        )

        return response.content[0].text if response.content else ""

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

        response = self.client.messages.create(
            model=self.model,
            max_tokens=20,
            messages=[{"role": "user", "content": prompt}]
        )

        title = response.content[0].text.strip() if response.content else "New Conversation"
        # Clean up the title
        title = title.replace('"', '').replace("'", "").strip()
        # Limit length
        if len(title) > 50:
            title = title[:47] + "..."

        return title

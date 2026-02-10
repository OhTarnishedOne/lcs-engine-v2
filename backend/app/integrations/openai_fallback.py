"""
Emergency fallback to OpenAI if Anthropic is completely down.
Only used after all Anthropic retries are exhausted.
Uses the same interface as AnthropicClient so it's a drop-in swap.
"""

import logging
from typing import AsyncGenerator, Optional

import openai

logger = logging.getLogger(__name__)


class OpenAIFallbackClient:
    """Minimal OpenAI client matching AnthropicClient interface."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o"

    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        return bool(self.api_key)

    async def chat_stream(
        self,
        messages: list[dict],
        system_prompt: str,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """Stream response from OpenAI."""
        try:
            openai_messages = [{"role": "system", "content": system_prompt}]
            openai_messages.extend(messages)

            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI fallback streaming failed: {e}")
            raise

    async def chat(
        self,
        messages: list[dict],
        system_prompt: str,
        max_tokens: int = 1024
    ) -> str:
        """Non-streaming response from OpenAI."""
        try:
            openai_messages = [{"role": "system", "content": system_prompt}]
            openai_messages.extend(messages)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                max_tokens=max_tokens,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"OpenAI fallback chat failed: {e}")
            raise

    async def generate_title(self, first_message: str, first_response: str) -> str:
        """Generate a conversation title using OpenAI."""
        prompt = f"""Generate a very short title (3-5 words max) for this conversation.
The title should capture the main topic. No quotes, no punctuation at the end.

User: {first_message[:200]}
Assistant: {first_response[:200]}

Title:"""

        try:
            title = await self.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a helpful assistant that generates short conversation titles.",
                max_tokens=20
            )
            title = title.strip().replace('"', '').replace("'", "").strip()
            if len(title) > 50:
                title = title[:47] + "..."
            return title if title else "New Conversation"
        except Exception as e:
            logger.warning(f"OpenAI title generation failed: {e}")
            return "New Conversation"

    async def chat_json(
        self,
        messages: list[dict],
        system_prompt: str,
        max_tokens: int = 2048
    ) -> dict:
        """Chat expecting JSON response."""
        import json

        response = await self.chat(messages, system_prompt, max_tokens)
        cleaned = response.strip()

        # Handle markdown code blocks
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]

        return json.loads(cleaned)

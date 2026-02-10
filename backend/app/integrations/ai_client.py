"""
Resilient AI client that tries Anthropic first, falls back to OpenAI.

Primary: Anthropic (Claude)
Fallback: OpenAI (GPT-4o) — only if configured and Anthropic exhausts retries
"""

import logging
from typing import AsyncGenerator, Optional

from .anthropic import AnthropicClient
from .openai_fallback import OpenAIFallbackClient

logger = logging.getLogger(__name__)


class ResilientAIClient:
    """
    Resilient AI client with automatic fallback.

    Uses Anthropic Claude as the primary provider.
    Falls back to OpenAI if configured and primary fails.
    """

    def __init__(
        self,
        anthropic_client: AnthropicClient,
        openai_client: Optional[OpenAIFallbackClient] = None,
    ):
        self.primary = anthropic_client
        self.fallback = openai_client

    def is_configured(self) -> bool:
        """Check if at least the primary client is configured."""
        return self.primary.is_configured()

    async def chat_stream(
        self,
        messages: list[dict],
        system_prompt: str,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """Stream with automatic fallback."""
        try:
            async for chunk in self.primary.chat_stream(messages, system_prompt, max_tokens):
                yield chunk
        except Exception as primary_error:
            if self.fallback is None:
                raise primary_error

            logger.warning(f"Primary (Claude) failed, falling back to OpenAI: {primary_error}")

            try:
                async for chunk in self.fallback.chat_stream(messages, system_prompt, max_tokens):
                    yield chunk
            except Exception as fallback_error:
                logger.error(f"Fallback (OpenAI) also failed: {fallback_error}")
                # Raise the original error — it's more informative
                raise primary_error

    async def chat(
        self,
        messages: list[dict],
        system_prompt: str,
        max_tokens: int = 1024
    ) -> str:
        """Non-streaming with automatic fallback."""
        try:
            return await self.primary.chat(messages, system_prompt, max_tokens)
        except Exception as primary_error:
            if self.fallback is None:
                raise primary_error

            logger.warning(f"Primary (Claude) failed, falling back to OpenAI: {primary_error}")

            try:
                return await self.fallback.chat(messages, system_prompt, max_tokens)
            except Exception as fallback_error:
                logger.error(f"Fallback (OpenAI) also failed: {fallback_error}")
                raise primary_error

    async def generate_title(self, first_message: str, first_response: str) -> str:
        """Generate conversation title with fallback."""
        try:
            return await self.primary.generate_title(first_message, first_response)
        except Exception as primary_error:
            if self.fallback is None:
                return "New Conversation"

            logger.warning(f"Primary title generation failed, trying fallback: {primary_error}")

            try:
                return await self.fallback.generate_title(first_message, first_response)
            except Exception:
                return "New Conversation"

    async def chat_json(
        self,
        messages: list[dict],
        system_prompt: str,
        max_tokens: int = 2048
    ) -> dict:
        """JSON mode with fallback (used by strategy engine)."""
        try:
            return await self.primary.chat_json(messages, system_prompt, max_tokens)
        except Exception as primary_error:
            if self.fallback is None:
                raise primary_error

            logger.warning(f"Primary JSON call failed, falling back to OpenAI: {primary_error}")

            try:
                return await self.fallback.chat_json(messages, system_prompt, max_tokens)
            except Exception as fallback_error:
                logger.error(f"Fallback JSON call also failed: {fallback_error}")
                raise primary_error

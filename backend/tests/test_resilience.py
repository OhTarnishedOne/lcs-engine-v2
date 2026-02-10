"""
Tests for API resilience and fallback logic.

Tests retry behavior, fallback to OpenAI, and graceful error handling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.integrations.anthropic import AnthropicClient
from app.integrations.openai_fallback import OpenAIFallbackClient
from app.integrations.ai_client import ResilientAIClient


class MockRateLimitError(Exception):
    """Mock rate limit error."""
    pass


class MockAuthenticationError(Exception):
    """Mock authentication error."""
    pass


class MockServerError(Exception):
    """Mock server error."""
    pass


# --- Anthropic Client Retry Tests ---

@pytest.mark.asyncio
async def test_retry_on_rate_limit():
    """Mock 429 → 429 → success. Verify 3 attempts made."""
    client = AnthropicClient(api_key="test-key")
    client.client = MagicMock()

    call_count = 0

    def mock_stream(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise MockRateLimitError("Rate limit exceeded")
        # Success on 3rd attempt
        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=mock_context)
        mock_context.__exit__ = MagicMock(return_value=False)
        mock_context.text_stream = iter(["Hello", " world"])
        return mock_context

    client.client.messages.stream = mock_stream

    # Patch sleep to avoid waiting
    with patch("asyncio.sleep", new_callable=AsyncMock):
        chunks = []
        async for chunk in client.chat_stream(
            messages=[{"role": "user", "content": "test"}],
            system_prompt="test"
        ):
            chunks.append(chunk)

    assert call_count == 3
    assert chunks == ["Hello", " world"]


@pytest.mark.asyncio
async def test_no_retry_on_auth_error():
    """Mock 401. Verify only 1 attempt (no retry)."""
    client = AnthropicClient(api_key="test-key")
    client.client = MagicMock()

    call_count = 0

    def mock_stream(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        error = Exception("Auth failed")
        error.__class__.__name__ = "AuthenticationError"
        raise error

    client.client.messages.stream = mock_stream

    # Create a custom AuthenticationError class for the test
    class AuthenticationError(Exception):
        pass

    def mock_stream_auth(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise AuthenticationError("Invalid API key")

    client.client.messages.stream = mock_stream_auth
    client._is_permanent_error = lambda e: isinstance(e, AuthenticationError)

    with pytest.raises(AuthenticationError):
        async for _ in client.chat_stream(
            messages=[{"role": "user", "content": "test"}],
            system_prompt="test"
        ):
            pass

    assert call_count == 1  # Only 1 attempt, no retries


@pytest.mark.asyncio
async def test_retry_respects_backoff():
    """Verify delays between retries use exponential backoff."""
    client = AnthropicClient(api_key="test-key")
    client.client = MagicMock()

    sleep_times = []

    async def mock_sleep(seconds):
        sleep_times.append(seconds)

    call_count = 0

    def mock_stream(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise MockServerError("Server error")
        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=mock_context)
        mock_context.__exit__ = MagicMock(return_value=False)
        mock_context.text_stream = iter(["Success"])
        return mock_context

    client.client.messages.stream = mock_stream

    with patch("asyncio.sleep", side_effect=mock_sleep):
        chunks = []
        async for chunk in client.chat_stream(
            messages=[{"role": "user", "content": "test"}],
            system_prompt="test"
        ):
            chunks.append(chunk)

    # Should have slept twice (after 1st and 2nd failure)
    assert len(sleep_times) == 2
    # Exponential backoff: 1s, 2s
    assert sleep_times == [1, 2]


# --- ResilientAIClient Fallback Tests ---

@pytest.mark.asyncio
async def test_fallback_to_openai():
    """Mock Anthropic failure → OpenAI success."""
    # Create mock clients
    anthropic = MagicMock(spec=AnthropicClient)
    openai = MagicMock(spec=OpenAIFallbackClient)

    async def failing_stream(*args, **kwargs):
        raise Exception("Anthropic is down")
        yield  # Make it a generator

    async def successful_stream(*args, **kwargs):
        yield "Fallback "
        yield "response"

    anthropic.chat_stream = failing_stream
    openai.chat_stream = successful_stream

    client = ResilientAIClient(anthropic_client=anthropic, openai_client=openai)

    chunks = []
    async for chunk in client.chat_stream(
        messages=[{"role": "user", "content": "test"}],
        system_prompt="test"
    ):
        chunks.append(chunk)

    assert chunks == ["Fallback ", "response"]


@pytest.mark.asyncio
async def test_fallback_disabled_if_no_key():
    """No OPENAI_API_KEY → raises original error."""
    anthropic = MagicMock(spec=AnthropicClient)

    async def failing_stream(*args, **kwargs):
        raise Exception("Anthropic is down")
        yield

    anthropic.chat_stream = failing_stream

    # No fallback client
    client = ResilientAIClient(anthropic_client=anthropic, openai_client=None)

    with pytest.raises(Exception) as exc_info:
        async for _ in client.chat_stream(
            messages=[{"role": "user", "content": "test"}],
            system_prompt="test"
        ):
            pass

    assert "Anthropic is down" in str(exc_info.value)


@pytest.mark.asyncio
async def test_both_fail_raises_primary_error():
    """Both fail → raises Claude error (not OpenAI)."""
    anthropic = MagicMock(spec=AnthropicClient)
    openai = MagicMock(spec=OpenAIFallbackClient)

    async def anthropic_failing_stream(*args, **kwargs):
        raise Exception("Anthropic specific error")
        yield

    async def openai_failing_stream(*args, **kwargs):
        raise Exception("OpenAI also failed")
        yield

    anthropic.chat_stream = anthropic_failing_stream
    openai.chat_stream = openai_failing_stream

    client = ResilientAIClient(anthropic_client=anthropic, openai_client=openai)

    with pytest.raises(Exception) as exc_info:
        async for _ in client.chat_stream(
            messages=[{"role": "user", "content": "test"}],
            system_prompt="test"
        ):
            pass

    # Should raise the primary (Anthropic) error, not OpenAI
    assert "Anthropic specific error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_resilient_client_streams_primary():
    """Normal flow uses Claude (primary)."""
    anthropic = MagicMock(spec=AnthropicClient)
    openai = MagicMock(spec=OpenAIFallbackClient)

    async def successful_stream(*args, **kwargs):
        yield "Primary "
        yield "response"

    anthropic.chat_stream = successful_stream
    openai.chat_stream = AsyncMock()  # Should not be called

    client = ResilientAIClient(anthropic_client=anthropic, openai_client=openai)

    chunks = []
    async for chunk in client.chat_stream(
        messages=[{"role": "user", "content": "test"}],
        system_prompt="test"
    ):
        chunks.append(chunk)

    assert chunks == ["Primary ", "response"]
    openai.chat_stream.assert_not_called()


@pytest.mark.asyncio
async def test_resilient_client_chat_primary():
    """Non-streaming uses Claude (primary)."""
    anthropic = MagicMock(spec=AnthropicClient)
    openai = MagicMock(spec=OpenAIFallbackClient)

    anthropic.chat = AsyncMock(return_value="Primary response")
    openai.chat = AsyncMock()  # Should not be called

    client = ResilientAIClient(anthropic_client=anthropic, openai_client=openai)

    result = await client.chat(
        messages=[{"role": "user", "content": "test"}],
        system_prompt="test"
    )

    assert result == "Primary response"
    openai.chat.assert_not_called()


# --- Streaming Error Handler Tests ---

def test_streaming_error_sends_user_message():
    """SSE stream sends friendly error event on failure."""
    from app.chat.router import _get_user_friendly_error

    # Test various error types
    class AuthenticationError(Exception):
        pass

    class RateLimitError(Exception):
        pass

    auth_error = AuthenticationError("Invalid API key")
    auth_error.__class__.__name__ = "AuthenticationError"
    assert "trouble connecting" in _get_user_friendly_error(auth_error)

    rate_error = RateLimitError("429 Too Many Requests")
    rate_error.__class__.__name__ = "RateLimitError"
    assert "a lot of questions" in _get_user_friendly_error(rate_error)

    overload_error = Exception("Service is overloaded")
    assert "overloaded" in _get_user_friendly_error(overload_error)

    generic_error = Exception("Something unexpected")
    assert "Something went wrong" in _get_user_friendly_error(generic_error)


@pytest.mark.asyncio
async def test_resilient_client_generate_title_fallback():
    """Title generation falls back on failure."""
    anthropic = MagicMock(spec=AnthropicClient)
    openai = MagicMock(spec=OpenAIFallbackClient)

    anthropic.generate_title = AsyncMock(side_effect=Exception("Title gen failed"))
    openai.generate_title = AsyncMock(return_value="Fallback Title")

    client = ResilientAIClient(anthropic_client=anthropic, openai_client=openai)

    result = await client.generate_title("Hello", "Hi there")

    assert result == "Fallback Title"


@pytest.mark.asyncio
async def test_resilient_client_chat_fallback():
    """Non-streaming chat falls back on failure."""
    anthropic = MagicMock(spec=AnthropicClient)
    openai = MagicMock(spec=OpenAIFallbackClient)

    anthropic.chat = AsyncMock(side_effect=Exception("Chat failed"))
    openai.chat = AsyncMock(return_value="Fallback response")

    client = ResilientAIClient(anthropic_client=anthropic, openai_client=openai)

    result = await client.chat(
        messages=[{"role": "user", "content": "test"}],
        system_prompt="test"
    )

    assert result == "Fallback response"

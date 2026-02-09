"""
Tests for Chat endpoints and service.

Uses mocked Anthropic client - no real API calls.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations import AnthropicClient
from app.chat.service import ChatService


class MockAnthropicClient:
    """Mock Anthropic client for testing."""

    def __init__(self):
        self.model = "claude-sonnet-4-20250514"

    def is_configured(self) -> bool:
        return True

    async def chat_stream(self, messages, system_prompt, max_tokens=1024):
        """Yield mock response tokens."""
        response = "This is a helpful response about investing."
        for word in response.split():
            yield word + " "

    async def chat(self, messages, system_prompt, max_tokens=1024):
        return "Mock response"

    async def generate_title(self, first_message, first_response):
        return "Investment Basics"


@pytest.fixture
def mock_anthropic():
    """Provide mock Anthropic client."""
    return MockAnthropicClient()


def get_token(client):
    """Helper to register and get auth token."""
    import uuid
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    reg_response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "testpass123"},
    )
    return reg_response.json()["access_token"]


def test_send_message_creates_conversation(client, mock_anthropic):
    """POST /api/chat/messages with no conversation_id creates new conversation."""
    token = get_token(client)

    # Override the anthropic client dependency
    from app.deps import get_anthropic_client
    from app.main import app
    app.dependency_overrides[get_anthropic_client] = lambda: mock_anthropic

    # Send message (SSE response)
    response = client.post(
        "/api/chat/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "What is a stock?"}
    )
    assert response.status_code == 200

    # Parse SSE events
    events = []
    for line in response.text.strip().split("\n"):
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))

    # Should have start, tokens, and done events
    assert any(e["type"] == "start" for e in events)
    assert any(e["type"] == "done" for e in events)

    # Get conversation_id from start event
    start_event = next(e for e in events if e["type"] == "start")
    assert "conversation_id" in start_event

    # Clean up
    app.dependency_overrides.clear()


def test_continue_conversation(client, mock_anthropic):
    """POST /api/chat/messages with existing conversation_id adds to it."""
    token = get_token(client)

    from app.deps import get_anthropic_client
    from app.main import app
    app.dependency_overrides[get_anthropic_client] = lambda: mock_anthropic

    # First message
    response1 = client.post(
        "/api/chat/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "What is a stock?"}
    )
    events1 = [json.loads(l[6:]) for l in response1.text.strip().split("\n") if l.startswith("data: ")]
    conversation_id = next(e for e in events1 if e["type"] == "start")["conversation_id"]

    # Second message to same conversation
    response2 = client.post(
        "/api/chat/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "How do I buy one?", "conversation_id": conversation_id}
    )
    events2 = [json.loads(l[6:]) for l in response2.text.strip().split("\n") if l.startswith("data: ")]

    # Should use same conversation
    start_event2 = next(e for e in events2 if e["type"] == "start")
    assert start_event2["conversation_id"] == conversation_id

    # Verify conversation has both messages
    conv_response = client.get(
        f"/api/chat/conversations/{conversation_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert conv_response.status_code == 200
    messages = conv_response.json()["messages"]
    assert len(messages) == 4  # 2 user + 2 assistant

    app.dependency_overrides.clear()


def test_list_conversations(client, mock_anthropic):
    """GET /api/chat/conversations returns user's conversations."""
    token = get_token(client)

    from app.deps import get_anthropic_client
    from app.main import app
    app.dependency_overrides[get_anthropic_client] = lambda: mock_anthropic

    # Create a conversation
    client.post(
        "/api/chat/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Hello"}
    )

    # List conversations
    response = client.get(
        "/api/chat/conversations",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["conversations"]) >= 1

    app.dependency_overrides.clear()


def test_get_conversation_detail(client, mock_anthropic):
    """GET /api/chat/conversations/{id} returns messages."""
    token = get_token(client)

    from app.deps import get_anthropic_client
    from app.main import app
    app.dependency_overrides[get_anthropic_client] = lambda: mock_anthropic

    # Create conversation
    response = client.post(
        "/api/chat/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Tell me about bonds"}
    )
    events = [json.loads(l[6:]) for l in response.text.strip().split("\n") if l.startswith("data: ")]
    conversation_id = next(e for e in events if e["type"] == "start")["conversation_id"]

    # Get detail
    detail_response = client.get(
        f"/api/chat/conversations/{conversation_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert detail_response.status_code == 200
    data = detail_response.json()
    assert data["id"] == conversation_id
    assert len(data["messages"]) == 2  # user + assistant

    app.dependency_overrides.clear()


def test_delete_conversation(client, mock_anthropic):
    """DELETE removes conversation and messages."""
    token = get_token(client)

    from app.deps import get_anthropic_client
    from app.main import app
    app.dependency_overrides[get_anthropic_client] = lambda: mock_anthropic

    # Create conversation
    response = client.post(
        "/api/chat/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Test message"}
    )
    events = [json.loads(l[6:]) for l in response.text.strip().split("\n") if l.startswith("data: ")]
    conversation_id = next(e for e in events if e["type"] == "start")["conversation_id"]

    # Delete
    delete_response = client.delete(
        f"/api/chat/conversations/{conversation_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    # Verify deleted
    get_response = client.get(
        f"/api/chat/conversations/{conversation_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 404

    app.dependency_overrides.clear()


def test_update_conversation_title(client, mock_anthropic):
    """PATCH updates title."""
    token = get_token(client)

    from app.deps import get_anthropic_client
    from app.main import app
    app.dependency_overrides[get_anthropic_client] = lambda: mock_anthropic

    # Create conversation
    response = client.post(
        "/api/chat/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Test message"}
    )
    events = [json.loads(l[6:]) for l in response.text.strip().split("\n") if l.startswith("data: ")]
    conversation_id = next(e for e in events if e["type"] == "start")["conversation_id"]

    # Update title
    update_response = client.patch(
        f"/api/chat/conversations/{conversation_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "My Custom Title"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "My Custom Title"

    app.dependency_overrides.clear()


def test_conversation_isolation(client, mock_anthropic):
    """User A can't see User B's conversations."""
    from app.deps import get_anthropic_client
    from app.main import app
    app.dependency_overrides[get_anthropic_client] = lambda: mock_anthropic

    # User A creates conversation
    token_a = get_token(client)
    response_a = client.post(
        "/api/chat/messages",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"message": "User A message"}
    )
    events_a = [json.loads(l[6:]) for l in response_a.text.strip().split("\n") if l.startswith("data: ")]
    conv_id_a = next(e for e in events_a if e["type"] == "start")["conversation_id"]

    # User B tries to access User A's conversation
    token_b = get_token(client)
    response_b = client.get(
        f"/api/chat/conversations/{conv_id_a}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert response_b.status_code == 404

    app.dependency_overrides.clear()


def test_unauthenticated_rejected(client):
    """No token = 401."""
    response = client.post(
        "/api/chat/messages",
        json={"message": "Hello"}
    )
    assert response.status_code == 401


def test_streaming_response_format(client, mock_anthropic):
    """Verify SSE format (start, token, done events)."""
    token = get_token(client)

    from app.deps import get_anthropic_client
    from app.main import app
    app.dependency_overrides[get_anthropic_client] = lambda: mock_anthropic

    response = client.post(
        "/api/chat/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Hello"}
    )

    # Parse events
    events = []
    for line in response.text.strip().split("\n"):
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))

    # Check event types
    event_types = [e["type"] for e in events]
    assert "start" in event_types
    assert "token" in event_types
    assert "done" in event_types

    # start should be first
    assert events[0]["type"] == "start"
    # done should be last
    assert events[-1]["type"] == "done"

    app.dependency_overrides.clear()


def test_messages_saved_after_stream(client, mock_anthropic):
    """Both user and assistant messages saved to DB."""
    token = get_token(client)

    from app.deps import get_anthropic_client
    from app.main import app
    app.dependency_overrides[get_anthropic_client] = lambda: mock_anthropic

    # Send message
    response = client.post(
        "/api/chat/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "What is an ETF?"}
    )
    events = [json.loads(l[6:]) for l in response.text.strip().split("\n") if l.startswith("data: ")]
    conversation_id = next(e for e in events if e["type"] == "start")["conversation_id"]

    # Get conversation
    conv_response = client.get(
        f"/api/chat/conversations/{conversation_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    messages = conv_response.json()["messages"]

    # Should have both user and assistant messages
    roles = [m["role"] for m in messages]
    assert "user" in roles
    assert "assistant" in roles

    # User message should match
    user_msg = next(m for m in messages if m["role"] == "user")
    assert user_msg["content"] == "What is an ETF?"

    app.dependency_overrides.clear()


def test_system_prompt_includes_persona(client, db):
    """Verify system prompt is personalized based on profile."""
    from app.chat.service import ChatService
    from app.db.models import UserProfile

    # Create a mock profile
    profile = UserProfile(
        user_id="test-user-id",
        persona="cautious_beginner",
        experience_level="never",
        biggest_barrier="fear_of_losing_money",
        primary_goal="learn_basics",
        risk_tolerance="very_conservative",
        learning_preference="read",
        onboarding_completed=True
    )

    service = ChatService(db, MockAnthropicClient())
    prompt = service.build_system_prompt(profile)

    # Check personalization
    assert "cautious_beginner" in prompt
    assert "never" in prompt
    assert "fear_of_losing_money" in prompt or "afraid of losing money" in prompt.lower()


def test_system_prompt_includes_barrier(client, db):
    """Verify barrier-specific sensitivity notes."""
    from app.chat.service import ChatService
    from app.db.models import UserProfile

    profile = UserProfile(
        user_id="test-user-id",
        persona="eager_learner",
        biggest_barrier="too_complicated",
        onboarding_completed=True
    )

    service = ChatService(db, MockAnthropicClient())
    prompt = service.build_system_prompt(profile)

    # Check barrier sensitivity note
    assert "analogies" in prompt.lower() or "complicated" in prompt.lower()


def test_default_system_prompt_when_no_profile(client, db):
    """Works with default prompt if no onboarding profile."""
    from app.chat.service import ChatService

    service = ChatService(db, MockAnthropicClient())
    prompt = service.build_system_prompt(None)

    # Should still have a valid prompt
    assert "LCS Engine" in prompt
    assert "tutor" in prompt.lower() or "guide" in prompt.lower()

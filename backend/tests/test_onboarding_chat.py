"""
Tests for conversational AI onboarding:
- Coverage computation
- Completion status logic
- Extraction endpoint (mock AI)
- Skip endpoint
- Chat endpoint (mock AI, SSE stream)
"""

import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.onboarding.coverage import compute_coverage, get_completion_status, REQUIRED_TOPICS
from app.onboarding.schemas import ExtractedProfile


# ============================================
# Unit tests: coverage state machine
# ============================================

class TestComputeCoverage:
    def test_empty_messages_returns_all_false(self):
        result = compute_coverage([])
        assert all(v is False for v in result.values())
        assert set(result.keys()) == set(REQUIRED_TOPICS)

    def test_experience_detected(self):
        messages = [
            {"role": "user", "content": "I've never invested before, I'm a total beginner"},
        ]
        result = compute_coverage(messages)
        assert result["experience"] is True

    def test_goals_detected(self):
        messages = [
            {"role": "user", "content": "I want to save for retirement and grow my wealth"},
        ]
        result = compute_coverage(messages)
        assert result["goals"] is True

    def test_risk_detected(self):
        messages = [
            {"role": "user", "content": "I'm pretty nervous about losing money, I'd prefer safe investments"},
        ]
        result = compute_coverage(messages)
        assert result["risk"] is True

    def test_interests_detected(self):
        messages = [
            {"role": "user", "content": "I'm curious about crypto and real estate"},
        ]
        result = compute_coverage(messages)
        assert result["interests"] is True

    def test_learning_style_detected(self):
        messages = [
            {"role": "user", "content": "I prefer to learn by watching videos and doing hands-on practice"},
        ]
        result = compute_coverage(messages)
        assert result["learning_style"] is True

    def test_assistant_messages_ignored(self):
        messages = [
            {"role": "assistant", "content": "Have you ever invested in stocks before?"},
        ]
        result = compute_coverage(messages)
        assert result["experience"] is False

    def test_multiple_topics_in_one_message(self):
        messages = [
            {"role": "user", "content": "I've never traded stocks, my goal is to learn and I'm nervous about risk"},
        ]
        result = compute_coverage(messages)
        assert result["experience"] is True
        assert result["goals"] is True
        assert result["risk"] is True

    def test_all_topics_covered_across_messages(self):
        messages = [
            {"role": "user", "content": "I'm a beginner with stocks"},
            {"role": "assistant", "content": "Great, what are your goals?"},
            {"role": "user", "content": "I want to grow my wealth long term"},
            {"role": "assistant", "content": "How do you feel about risk?"},
            {"role": "user", "content": "I'm comfortable with moderate risk, not too aggressive"},
            {"role": "assistant", "content": "What interests you?"},
            {"role": "user", "content": "I'm interested in ETFs and crypto"},
            {"role": "assistant", "content": "How do you like to learn?"},
            {"role": "user", "content": "I prefer watching videos and hands-on practice"},
        ]
        result = compute_coverage(messages)
        assert all(v is True for v in result.values())


class TestGetCompletionStatus:
    def test_no_topics_covered_returns_continue(self):
        coverage = {t: False for t in REQUIRED_TOPICS}
        assert get_completion_status(coverage, 1) == "continue"

    def test_some_topics_covered_returns_continue(self):
        coverage = {t: False for t in REQUIRED_TOPICS}
        coverage["experience"] = True
        coverage["goals"] = True
        assert get_completion_status(coverage, 3) == "continue"

    def test_all_topics_covered_returns_wrap_up(self):
        coverage = {t: True for t in REQUIRED_TOPICS}
        assert get_completion_status(coverage, 4) == "wrap_up"

    def test_turn_count_6_returns_wrap_up(self):
        coverage = {t: False for t in REQUIRED_TOPICS}
        coverage["experience"] = True
        assert get_completion_status(coverage, 6) == "wrap_up"

    def test_turn_count_7_returns_wrap_up(self):
        coverage = {t: False for t in REQUIRED_TOPICS}
        assert get_completion_status(coverage, 7) == "wrap_up"

    def test_turn_count_5_not_all_covered_returns_continue(self):
        coverage = {t: True for t in REQUIRED_TOPICS}
        coverage["learning_style"] = False
        assert get_completion_status(coverage, 5) == "continue"


# ============================================
# Unit tests: ExtractedProfile validation
# ============================================

class TestExtractedProfile:
    def test_valid_profile(self):
        profile = ExtractedProfile(
            experience_level="beginner",
            primary_goal="grow_wealth",
            risk_tolerance="moderate",
            interests=["stocks", "crypto"],
            learning_preference="watch",
        )
        assert profile.experience_level == "beginner"
        assert profile.interests == ["stocks", "crypto"]

    def test_invalid_experience_level_defaults(self):
        profile = ExtractedProfile(experience_level="expert")
        assert profile.experience_level == "beginner"

    def test_invalid_risk_tolerance_defaults(self):
        profile = ExtractedProfile(risk_tolerance="yolo")
        assert profile.risk_tolerance == "moderate"

    def test_invalid_primary_goal_defaults(self):
        profile = ExtractedProfile(primary_goal="moon")
        assert profile.primary_goal == "learn_basics"

    def test_invalid_learning_preference_defaults(self):
        profile = ExtractedProfile(learning_preference="telepathy")
        assert profile.learning_preference == "do"

    def test_invalid_interests_filtered(self):
        profile = ExtractedProfile(interests=["stocks", "nfts", "magic_beans"])
        assert profile.interests == ["stocks"]

    def test_empty_interests_defaults(self):
        profile = ExtractedProfile(interests=[])
        assert profile.interests == ["stocks", "etfs"]

    def test_all_invalid_interests_defaults(self):
        profile = ExtractedProfile(interests=["nfts", "magic_beans"])
        assert profile.interests == ["stocks", "etfs"]

    def test_none_experience_maps_correctly(self):
        """The AI extraction uses 'none' for no experience."""
        profile = ExtractedProfile(experience_level="none")
        assert profile.experience_level == "none"

    def test_defaults_applied(self):
        profile = ExtractedProfile()
        assert profile.experience_level == "beginner"
        assert profile.primary_goal == "learn_basics"
        assert profile.risk_tolerance == "moderate"
        assert profile.interests == ["stocks", "etfs"]
        assert profile.learning_preference == "do"
        assert profile.additional_context is None


# ============================================
# Integration tests: API endpoints
# ============================================

def _register_and_get_token(client):
    """Helper to register a user and return auth token."""
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "chattest@example.com", "password": "testpass123"},
    )
    return reg_response.json()["access_token"]


def test_skip_onboarding(client):
    """Test POST /api/onboarding/skip creates profile with defaults."""
    token = _register_and_get_token(client)

    response = client.post(
        "/api/onboarding/skip",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True

    # Verify onboarding is now complete
    progress = client.get(
        "/api/onboarding/progress",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert progress.json()["is_complete"] is True


def test_chat_endpoint_returns_sse(client):
    """Test POST /api/onboarding/chat returns SSE stream."""
    token = _register_and_get_token(client)

    # Mock the AI client to return test chunks
    async def mock_stream(*args, **kwargs):
        yield "Hello "
        yield "there!"

    with patch("app.onboarding.router.get_ai_client") as mock_get_ai:
        mock_client = MagicMock()
        mock_client.chat_stream = mock_stream
        mock_get_ai.return_value = mock_client

        from app.deps import get_ai_client
        from app.main import app as test_app
        test_app.dependency_overrides[get_ai_client] = lambda: mock_client

        response = client.post(
            "/api/onboarding/chat",
            json={"messages": []},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")

        # Parse SSE events
        events = []
        for line in response.text.strip().split("\n"):
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))

        # Should have start, token(s), done
        assert events[0]["type"] == "start"
        assert events[-1]["type"] == "done"
        assert events[-1]["completion_status"] in ("continue", "wrap_up")

        # Clean up
        test_app.dependency_overrides.pop(get_ai_client, None)


def test_chat_complete_with_mock_ai(client):
    """Test POST /api/onboarding/chat/complete extracts profile."""
    token = _register_and_get_token(client)

    mock_extraction = {
        "experience_level": "beginner",
        "primary_goal": "learn_basics",
        "risk_tolerance": "moderate",
        "interests": ["stocks", "etfs"],
        "learning_preference": "do",
        "additional_context": "New user, eager to learn",
    }

    mock_client = AsyncMock()
    mock_client.chat_json = AsyncMock(return_value=mock_extraction)

    from app.deps import get_ai_client
    from app.main import app as test_app
    test_app.dependency_overrides[get_ai_client] = lambda: mock_client

    response = client.post(
        "/api/onboarding/chat/complete",
        json={
            "messages": [
                {"role": "assistant", "content": "Hi! Tell me about yourself."},
                {"role": "user", "content": "I'm new to investing and want to learn the basics."},
                {"role": "assistant", "content": "Great! What topics interest you?"},
                {"role": "user", "content": "Stocks and ETFs mostly."},
            ]
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["profile"]["experience_level"] == "beginner"
    assert data["profile"]["persona"] is not None

    # Verify onboarding marked complete
    progress = client.get(
        "/api/onboarding/progress",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert progress.json()["is_complete"] is True

    test_app.dependency_overrides.pop(get_ai_client, None)


def test_chat_complete_extraction_failure(client):
    """Test POST /api/onboarding/chat/complete handles AI failure gracefully."""
    token = _register_and_get_token(client)

    mock_client = AsyncMock()
    mock_client.chat_json = AsyncMock(side_effect=Exception("AI service unavailable"))

    from app.deps import get_ai_client
    from app.main import app as test_app
    test_app.dependency_overrides[get_ai_client] = lambda: mock_client

    response = client.post(
        "/api/onboarding/chat/complete",
        json={
            "messages": [
                {"role": "user", "content": "I want to learn about stocks."},
            ]
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["error"] == "extraction_failed"

    test_app.dependency_overrides.pop(get_ai_client, None)


def test_skip_then_check_profile(client):
    """Test that skip creates a complete profile with all expected defaults."""
    token = _register_and_get_token(client)

    client.post(
        "/api/onboarding/skip",
        headers={"Authorization": f"Bearer {token}"},
    )

    profile_response = client.get(
        "/api/onboarding/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert profile_response.status_code == 200
    raw = profile_response.json()["raw"]
    assert raw["experience_level"] == "beginner"
    assert raw["primary_goal"] == "learn_basics"
    assert raw["risk_tolerance"] == "moderate"
    assert raw["learning_preference"] == "do"
    assert raw["onboarding_completed"] is True

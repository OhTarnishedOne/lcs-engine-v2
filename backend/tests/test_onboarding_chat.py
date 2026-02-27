"""
Tests for conversational AI onboarding:
- Coverage computation (new deeper topics)
- Completion status logic (with disengagement detection)
- Extraction endpoint (mock AI)
- Skip endpoint
- Chat endpoint (mock AI, SSE stream)
- Complete-conversation endpoint (hybrid tap+chat)
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

    def test_required_topics_are_deeper(self):
        """Verify REQUIRED_TOPICS are the 3 deeper conversation topics."""
        assert set(REQUIRED_TOPICS) == {"motivation", "life_context", "emotional_relationship"}

    def test_motivation_detected(self):
        messages = [
            {"role": "user", "content": "I decided to start investing because I want a better future for my kids"},
        ]
        result = compute_coverage(messages)
        assert result["motivation"] is True

    def test_life_context_detected(self):
        messages = [
            {"role": "user", "content": "I'm mid-career with a family and a mortgage to pay"},
        ]
        result = compute_coverage(messages)
        assert result["life_context"] is True

    def test_emotional_relationship_detected(self):
        messages = [
            {"role": "user", "content": "I feel nervous about investing but also excited to learn"},
        ]
        result = compute_coverage(messages)
        assert result["emotional_relationship"] is True

    def test_assistant_messages_ignored(self):
        messages = [
            {"role": "assistant", "content": "What motivated you to start learning about investing?"},
        ]
        result = compute_coverage(messages)
        assert result["motivation"] is False

    def test_multiple_topics_in_one_message(self):
        messages = [
            {"role": "user", "content": "I decided to learn because of my family. I feel excited but also worried about losing money."},
        ]
        result = compute_coverage(messages)
        assert result["motivation"] is True  # "decided"
        assert result["life_context"] is True  # "family"
        assert result["emotional_relationship"] is True  # "feel", "excited", "worried"

    def test_all_topics_covered_across_messages(self):
        messages = [
            {"role": "user", "content": "I finally decided to learn because I want to build wealth"},
            {"role": "assistant", "content": "Tell me about your life situation."},
            {"role": "user", "content": "I have kids and a busy career, not much time"},
            {"role": "assistant", "content": "How do you feel about money?"},
            {"role": "user", "content": "I feel anxious about it but also hopeful"},
        ]
        result = compute_coverage(messages)
        assert all(v is True for v in result.values())


class TestGetCompletionStatus:
    def test_no_topics_covered_returns_continue(self):
        coverage = {t: False for t in REQUIRED_TOPICS}
        assert get_completion_status(coverage, 1) == "continue"

    def test_some_topics_covered_returns_continue(self):
        coverage = {t: False for t in REQUIRED_TOPICS}
        coverage["motivation"] = True
        assert get_completion_status(coverage, 2) == "continue"

    def test_all_topics_covered_returns_wrap_up(self):
        coverage = {t: True for t in REQUIRED_TOPICS}
        assert get_completion_status(coverage, 3) == "wrap_up"

    def test_turn_count_5_returns_wrap_up(self):
        coverage = {t: False for t in REQUIRED_TOPICS}
        coverage["motivation"] = True
        assert get_completion_status(coverage, 5) == "wrap_up"

    def test_turn_count_4_not_all_covered_returns_continue(self):
        coverage = {t: True for t in REQUIRED_TOPICS}
        coverage["emotional_relationship"] = False
        assert get_completion_status(coverage, 4) == "continue"

    def test_disengagement_detection(self):
        """Two consecutive short responses should trigger wrap_up."""
        coverage = {t: False for t in REQUIRED_TOPICS}
        messages = [
            {"role": "assistant", "content": "What motivated you?"},
            {"role": "user", "content": "idk"},
            {"role": "assistant", "content": "Tell me more?"},
            {"role": "user", "content": "not sure"},
        ]
        assert get_completion_status(coverage, 2, messages) == "wrap_up"

    def test_no_disengagement_with_longer_responses(self):
        """Normal-length responses should not trigger disengagement."""
        coverage = {t: False for t in REQUIRED_TOPICS}
        messages = [
            {"role": "assistant", "content": "What motivated you?"},
            {"role": "user", "content": "I want to learn because my parents never taught me about money and investing"},
            {"role": "assistant", "content": "Tell me more?"},
            {"role": "user", "content": "Yeah so I grew up not really understanding how the stock market works at all"},
        ]
        assert get_completion_status(coverage, 2, messages) == "continue"


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
        assert profile.motivation is None
        assert profile.life_context is None
        assert profile.emotional_relationship is None

    def test_new_valid_interests(self):
        """Options and not_sure are now valid interests."""
        profile = ExtractedProfile(interests=["options", "not_sure", "stocks"])
        assert profile.interests == ["options", "not_sure", "stocks"]

    def test_new_valid_goals(self):
        """side_income, support_family, understand_news are now valid goals."""
        profile = ExtractedProfile(primary_goal="side_income")
        assert profile.primary_goal == "side_income"

    def test_goals_validation(self):
        profile = ExtractedProfile(goals=["grow_wealth", "retirement", "invalid"])
        assert profile.goals == ["grow_wealth", "retirement"]

    def test_goals_all_invalid_defaults(self):
        profile = ExtractedProfile(goals=["invalid1", "invalid2"])
        assert profile.goals == ["learn_basics"]

    def test_conversation_fields(self):
        profile = ExtractedProfile(
            motivation="Want to build wealth for my family",
            life_context="Mid-career professional with limited time",
            emotional_relationship="Nervous but optimistic",
        )
        assert profile.motivation == "Want to build wealth for my family"
        assert profile.life_context == "Mid-career professional with limited time"
        assert profile.emotional_relationship == "Nervous but optimistic"


# ============================================
# Integration tests: API endpoints
# ============================================

def _register_and_get_token(client):
    """Helper to register a user and return auth token."""
    import uuid
    email = f"chattest-{uuid.uuid4().hex[:8]}@example.com"
    reg_response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "testpass123"},
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
    """Test POST /api/onboarding/chat returns SSE stream with tap_responses."""
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
            json={
                "messages": [],
                "tap_responses": {
                    "experience_level": "a_little",
                    "goals": ["learn_basics", "grow_wealth"],
                    "risk_tolerance": "moderate",
                    "interests": ["stocks", "etfs"],
                    "learning_style": "examples",
                },
            },
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
    """Test POST /api/onboarding/chat/complete extracts profile (legacy endpoint)."""
    token = _register_and_get_token(client)

    mock_extraction = {
        "motivation": "Wants to build wealth for family",
        "life_context": "Mid-career professional",
        "emotional_relationship": "Nervous but hopeful",
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
    assert data["profile"]["persona"] is not None

    # Verify onboarding marked complete
    progress = client.get(
        "/api/onboarding/progress",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert progress.json()["is_complete"] is True

    test_app.dependency_overrides.pop(get_ai_client, None)


def test_complete_conversation_hybrid(client):
    """Test POST /api/onboarding/complete-conversation merges tap + chat data."""
    token = _register_and_get_token(client)

    mock_extraction = {
        "motivation": "Inspired by a friend who started investing",
        "life_context": "Works full-time, has two kids",
        "emotional_relationship": "Excited but a bit anxious",
    }

    mock_client = AsyncMock()
    mock_client.chat_json = AsyncMock(return_value=mock_extraction)

    from app.deps import get_ai_client
    from app.main import app as test_app
    test_app.dependency_overrides[get_ai_client] = lambda: mock_client

    response = client.post(
        "/api/onboarding/complete-conversation",
        json={
            "tap_responses": {
                "experience_level": "a_little",
                "goals": ["grow_wealth", "retirement"],
                "risk_tolerance": "moderate",
                "interests": ["stocks", "etfs", "crypto"],
                "learning_style": "detailed",
            },
            "messages": [
                {"role": "assistant", "content": "What motivated you to start?"},
                {"role": "user", "content": "A friend inspired me. I work full-time and have two kids."},
                {"role": "assistant", "content": "How do you feel about investing?"},
                {"role": "user", "content": "Excited but a bit anxious about it all."},
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True

    profile = data["profile"]
    assert profile["experience_level"] == "beginner"  # a_little maps to beginner
    assert profile["primary_goal"] == "grow_wealth"  # first in goals list
    assert profile["risk_tolerance"] == "moderate"
    assert profile["learning_preference"] == "read"  # detailed maps to read
    assert profile["motivation"] == "Inspired by a friend who started investing"
    assert profile["life_context"] == "Works full-time, has two kids"
    assert profile["emotional_relationship"] == "Excited but a bit anxious"

    # Verify onboarding marked complete
    progress = client.get(
        "/api/onboarding/progress",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert progress.json()["is_complete"] is True

    test_app.dependency_overrides.pop(get_ai_client, None)


def test_complete_conversation_tap_only(client):
    """Test complete-conversation with empty messages (skip during chat)."""
    token = _register_and_get_token(client)

    mock_client = AsyncMock()

    from app.deps import get_ai_client
    from app.main import app as test_app
    test_app.dependency_overrides[get_ai_client] = lambda: mock_client

    response = client.post(
        "/api/onboarding/complete-conversation",
        json={
            "tap_responses": {
                "experience_level": "none",
                "goals": ["learn_basics"],
                "risk_tolerance": "conservative",
                "interests": ["bonds"],
                "learning_style": "actionable",
            },
            "messages": [],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True

    profile = data["profile"]
    assert profile["experience_level"] == "never"  # none maps to never
    assert profile["primary_goal"] == "learn_basics"
    assert profile["risk_tolerance"] == "conservative"
    assert profile["learning_preference"] == "watch"  # actionable maps to watch
    assert profile["motivation"] is None  # no conversation
    assert profile["life_context"] is None

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
    assert raw["goals"] == ["learn_basics"]


def test_profile_has_about_you_summary(client):
    """Test that profile with conversation data returns about_you_summary."""
    token = _register_and_get_token(client)

    mock_extraction = {
        "motivation": "Wants to build generational wealth",
        "life_context": "Young professional with no dependents",
        "emotional_relationship": "Excited and confident",
    }

    mock_client = AsyncMock()
    mock_client.chat_json = AsyncMock(return_value=mock_extraction)

    from app.deps import get_ai_client
    from app.main import app as test_app
    test_app.dependency_overrides[get_ai_client] = lambda: mock_client

    # Complete via hybrid flow
    client.post(
        "/api/onboarding/complete-conversation",
        json={
            "tap_responses": {
                "experience_level": "some",
                "goals": ["grow_wealth"],
                "risk_tolerance": "aggressive",
                "interests": ["stocks", "crypto"],
                "learning_style": "deep_dive",
            },
            "messages": [
                {"role": "assistant", "content": "What brought you here?"},
                {"role": "user", "content": "I want to build generational wealth. I'm a young professional."},
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # Fetch profile
    profile_response = client.get(
        "/api/onboarding/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert profile_response.status_code == 200
    derived = profile_response.json()["derived"]
    assert derived["about_you_summary"] is not None
    assert "generational wealth" in derived["about_you_summary"]

    test_app.dependency_overrides.pop(get_ai_client, None)

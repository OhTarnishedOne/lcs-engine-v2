"""
Tests for Strategy endpoints and service.

Uses mocked AI client - no real API calls.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations import ResilientAIClient
from app.strategies.service import StrategyService, VALID_STRATEGY_TYPES


class MockAIClient:
    """Mock ResilientAIClient for testing."""

    def __init__(self):
        self.model = "claude-sonnet-4-20250514"

    def is_configured(self) -> bool:
        return True

    async def chat(self, messages, system_prompt, max_tokens=1024):
        """Return mock comparison/explanation text."""
        return "This is a helpful comparison of your strategies. Strategy 1 is more conservative while Strategy 2 has higher growth potential."

    async def chat_json(self, messages, system_prompt, max_tokens=2048):
        """Return mock strategy JSON."""
        return {
            "name": "Balanced Growth Portfolio",
            "description": "A diversified portfolio balancing growth and stability.",
            "strategy_type": "balanced",
            "risk_level": 3,
            "time_horizon": "medium",
            "assets": [
                {
                    "ticker": "VTI",
                    "name": "Vanguard Total Stock Market ETF",
                    "allocation_pct": 40.0,
                    "rationale": "Broad US market exposure"
                },
                {
                    "ticker": "VXUS",
                    "name": "Vanguard Total International Stock ETF",
                    "allocation_pct": 20.0,
                    "rationale": "International diversification"
                },
                {
                    "ticker": "BND",
                    "name": "Vanguard Total Bond Market ETF",
                    "allocation_pct": 30.0,
                    "rationale": "Stability and income"
                },
                {
                    "ticker": "VNQ",
                    "name": "Vanguard Real Estate ETF",
                    "allocation_pct": 10.0,
                    "rationale": "Real estate exposure"
                }
            ],
            "rationale": "This portfolio is designed for moderate risk tolerance with long-term growth potential.",
            "risks": "Market downturns can affect all asset classes. Past performance does not guarantee future results.",
            "learning_points": ["Diversification", "Asset allocation", "Risk management", "Long-term investing"]
        }


@pytest.fixture
def mock_ai_client():
    """Provide mock AI client."""
    return MockAIClient()


def get_token(client):
    """Helper to register and get auth token."""
    import uuid
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    reg_response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "testpass123"},
    )
    return reg_response.json()["access_token"]


def get_token_with_profile(client):
    """Helper to register, complete onboarding, and get auth token."""
    import uuid
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    reg_response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "testpass123"},
    )
    token = reg_response.json()["access_token"]

    # Complete onboarding
    client.post(
        "/api/onboarding/responses",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_id": "experience_level",
            "answer": "never"
        }
    )
    client.post(
        "/api/onboarding/responses",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_id": "biggest_barrier",
            "answer": "fear_of_losing_money"
        }
    )
    client.post(
        "/api/onboarding/responses",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_id": "primary_goal",
            "answer": "learn_basics"
        }
    )
    client.post(
        "/api/onboarding/responses",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_id": "risk_tolerance",
            "answer": "conservative"
        }
    )
    client.post(
        "/api/onboarding/responses",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_id": "learning_preference",
            "answer": "read"
        }
    )
    client.post(
        "/api/onboarding/complete",
        headers={"Authorization": f"Bearer {token}"}
    )

    return token


def test_generate_strategy_creates_record(client, mock_ai_client):
    """POST /api/strategies/generate creates a new strategy."""
    token = get_token(client)

    from app.deps import get_ai_client
    from app.main import app
    app.dependency_overrides[get_ai_client] = lambda: mock_ai_client

    response = client.post(
        "/api/strategies/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"strategy_type": "balanced"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["name"] == "Balanced Growth Portfolio"
    assert data["strategy_type"] == "balanced"
    assert len(data["assets"]) == 4
    assert data["risk_level"] == 3

    app.dependency_overrides.clear()


def test_generate_auto_selects_type_from_profile(client, mock_ai_client, db):
    """Strategy type auto-selected from onboarding profile."""
    from app.strategies.service import StrategyService
    from app.db.models import UserProfile

    # Create a profile with conservative + learn_basics -> should pick "index"
    profile = UserProfile(
        user_id="test-user-id",
        persona="cautious_beginner",
        experience_level="never",
        biggest_barrier="fear_of_losing_money",
        primary_goal="learn_basics",
        risk_tolerance="conservative",
        learning_preference="read",
        onboarding_completed=True
    )

    service = StrategyService(db, mock_ai_client)
    strategy_type = service.get_default_strategy_type(profile)

    # conservative + learn_basics maps to "index"
    assert strategy_type == "index"


def test_generate_validates_strategy_type(client, mock_ai_client):
    """Invalid strategy type returns 400."""
    token = get_token(client)

    from app.deps import get_ai_client
    from app.main import app
    app.dependency_overrides[get_ai_client] = lambda: mock_ai_client

    response = client.post(
        "/api/strategies/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"strategy_type": "invalid_type"}
    )

    assert response.status_code == 400
    assert "Invalid strategy type" in response.json()["detail"]

    app.dependency_overrides.clear()


def test_list_strategies_empty(client, mock_ai_client):
    """GET /api/strategies returns empty list for new user."""
    token = get_token(client)

    response = client.get(
        "/api/strategies",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["strategies"] == []
    assert data["total"] == 0


def test_list_strategies_returns_all(client, mock_ai_client):
    """GET /api/strategies returns all user's strategies."""
    token = get_token(client)

    from app.deps import get_ai_client
    from app.main import app
    app.dependency_overrides[get_ai_client] = lambda: mock_ai_client

    # Create two strategies
    client.post(
        "/api/strategies/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"strategy_type": "balanced"}
    )
    client.post(
        "/api/strategies/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"strategy_type": "growth"}
    )

    response = client.get(
        "/api/strategies",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["strategies"]) == 2

    app.dependency_overrides.clear()


def test_get_strategy_by_id(client, mock_ai_client):
    """GET /api/strategies/{id} returns specific strategy."""
    token = get_token(client)

    from app.deps import get_ai_client
    from app.main import app
    app.dependency_overrides[get_ai_client] = lambda: mock_ai_client

    # Create strategy
    create_response = client.post(
        "/api/strategies/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"strategy_type": "balanced"}
    )
    strategy_id = create_response.json()["id"]

    # Get by ID
    response = client.get(
        f"/api/strategies/{strategy_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == strategy_id
    assert data["name"] == "Balanced Growth Portfolio"

    app.dependency_overrides.clear()


def test_get_strategy_not_found(client, mock_ai_client):
    """GET /api/strategies/{id} returns 404 for non-existent strategy."""
    token = get_token(client)

    response = client.get(
        "/api/strategies/nonexistent-id",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


def test_delete_strategy(client, mock_ai_client):
    """DELETE /api/strategies/{id} removes strategy."""
    token = get_token(client)

    from app.deps import get_ai_client
    from app.main import app
    app.dependency_overrides[get_ai_client] = lambda: mock_ai_client

    # Create strategy
    create_response = client.post(
        "/api/strategies/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"strategy_type": "balanced"}
    )
    strategy_id = create_response.json()["id"]

    # Delete
    delete_response = client.delete(
        f"/api/strategies/{strategy_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    # Verify deleted
    get_response = client.get(
        f"/api/strategies/{strategy_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 404

    app.dependency_overrides.clear()


def test_delete_strategy_not_found(client, mock_ai_client):
    """DELETE /api/strategies/{id} returns 404 for non-existent strategy."""
    token = get_token(client)

    response = client.delete(
        "/api/strategies/nonexistent-id",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


def test_compare_strategies(client, mock_ai_client):
    """POST /api/strategies/compare returns AI comparison."""
    token = get_token(client)

    from app.deps import get_ai_client
    from app.main import app
    app.dependency_overrides[get_ai_client] = lambda: mock_ai_client

    # Create two strategies
    response1 = client.post(
        "/api/strategies/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"strategy_type": "balanced"}
    )
    response2 = client.post(
        "/api/strategies/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"strategy_type": "growth"}
    )
    strategy_id_1 = response1.json()["id"]
    strategy_id_2 = response2.json()["id"]

    # Compare
    compare_response = client.post(
        "/api/strategies/compare",
        headers={"Authorization": f"Bearer {token}"},
        json={"strategy_ids": [strategy_id_1, strategy_id_2]}
    )

    assert compare_response.status_code == 200
    data = compare_response.json()
    assert "id" in data
    assert len(data["strategies"]) == 2
    assert "comparison_text" in data
    assert len(data["comparison_text"]) > 0

    app.dependency_overrides.clear()


def test_compare_requires_two(client, mock_ai_client):
    """POST /api/strategies/compare requires at least 2 strategies."""
    token = get_token(client)

    from app.deps import get_ai_client
    from app.main import app
    app.dependency_overrides[get_ai_client] = lambda: mock_ai_client

    # Create one strategy
    response1 = client.post(
        "/api/strategies/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"strategy_type": "balanced"}
    )
    strategy_id_1 = response1.json()["id"]

    # Try to compare with just one
    compare_response = client.post(
        "/api/strategies/compare",
        headers={"Authorization": f"Bearer {token}"},
        json={"strategy_ids": [strategy_id_1]}
    )

    assert compare_response.status_code == 422  # Pydantic validation error

    app.dependency_overrides.clear()


def test_compare_max_three(client, mock_ai_client):
    """POST /api/strategies/compare allows max 3 strategies."""
    token = get_token(client)

    from app.deps import get_ai_client
    from app.main import app
    app.dependency_overrides[get_ai_client] = lambda: mock_ai_client

    # Create four strategies
    ids = []
    for _ in range(4):
        response = client.post(
            "/api/strategies/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"strategy_type": "balanced"}
        )
        ids.append(response.json()["id"])

    # Try to compare four
    compare_response = client.post(
        "/api/strategies/compare",
        headers={"Authorization": f"Bearer {token}"},
        json={"strategy_ids": ids}
    )

    assert compare_response.status_code == 422  # Pydantic validation error

    app.dependency_overrides.clear()


def test_explain_strategy(client, mock_ai_client):
    """POST /api/strategies/{id}/explain returns AI explanation."""
    token = get_token(client)

    from app.deps import get_ai_client
    from app.main import app
    app.dependency_overrides[get_ai_client] = lambda: mock_ai_client

    # Create strategy
    create_response = client.post(
        "/api/strategies/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"strategy_type": "balanced"}
    )
    strategy_id = create_response.json()["id"]

    # Ask for explanation
    explain_response = client.post(
        f"/api/strategies/{strategy_id}/explain",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "Why is VTI a good choice for this portfolio?"}
    )

    assert explain_response.status_code == 200
    data = explain_response.json()
    assert data["strategy_id"] == strategy_id
    assert data["question"] == "Why is VTI a good choice for this portfolio?"
    assert "explanation" in data
    assert len(data["explanation"]) > 0

    app.dependency_overrides.clear()


def test_strategy_isolation(client, mock_ai_client):
    """User A can't see User B's strategies."""
    from app.deps import get_ai_client
    from app.main import app
    app.dependency_overrides[get_ai_client] = lambda: mock_ai_client

    # User A creates strategy
    token_a = get_token(client)
    response_a = client.post(
        "/api/strategies/generate",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"strategy_type": "balanced"}
    )
    strategy_id_a = response_a.json()["id"]

    # User B tries to access User A's strategy
    token_b = get_token(client)
    response_b = client.get(
        f"/api/strategies/{strategy_id_a}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert response_b.status_code == 404

    # User B's list should not include User A's strategy
    list_response = client.get(
        "/api/strategies",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert list_response.json()["total"] == 0

    app.dependency_overrides.clear()


def test_max_strategies_limit(client, mock_ai_client):
    """User cannot create more than 10 strategies."""
    token = get_token(client)

    from app.deps import get_ai_client
    from app.main import app
    app.dependency_overrides[get_ai_client] = lambda: mock_ai_client

    # Create 10 strategies
    for i in range(10):
        response = client.post(
            "/api/strategies/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"strategy_type": "balanced"}
        )
        assert response.status_code == 200, f"Failed on strategy {i+1}"

    # 11th should fail
    response = client.post(
        "/api/strategies/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"strategy_type": "balanced"}
    )
    assert response.status_code == 400
    assert "Maximum of 10 strategies" in response.json()["detail"]

    app.dependency_overrides.clear()

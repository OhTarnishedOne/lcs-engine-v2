"""
Tests for Probability Lab endpoints and service.

Uses seed data - no real Kalshi API calls.
"""

import pytest
from datetime import datetime, timedelta

from app.probability.service import ProbabilityService, SEED_MARKETS
from app.db.models import User
from app.auth.utils import hash_password


def _ensure_test_user(db, user_id, email=None):
    """Create a user with a specific ID if it doesn't exist."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, email=email or f"{user_id}@test.com", password_hash=hash_password("test"))
        db.add(user)
        db.commit()
    return user


def get_token(client):
    """Helper to register and get auth token."""
    import uuid
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    reg_response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "testpass123"},
    )
    return reg_response.json()["access_token"]


def test_get_markets(client, db):
    """GET /api/probability/markets returns active markets."""
    token = get_token(client)

    # Seed markets
    service = ProbabilityService(db)
    service.seed_markets_if_empty()
    db.commit()

    response = client.get(
        "/api/probability/markets",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["markets"]) >= 1
    # Market probability should be hidden
    assert data["markets"][0]["market_probability"] is None


def test_submit_prediction(client, db):
    """POST /api/probability/predictions saves a valid prediction."""
    token = get_token(client)

    # Seed markets
    service = ProbabilityService(db)
    service.seed_markets_if_empty()
    db.commit()

    # Get a market
    from app.db.models import PredictionMarket
    market = db.query(PredictionMarket).first()

    response = client.post(
        "/api/probability/predictions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "market_id": market.id,
            "probability": 0.65,
            "reasoning": "I think this is likely based on recent trends."
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["predicted_probability"] == 0.65
    # Market probability is revealed after submission
    assert data["market_probability"] is not None


def test_prediction_range(client, db):
    """Probability must be 0.0-1.0, else 400."""
    token = get_token(client)

    service = ProbabilityService(db)
    service.seed_markets_if_empty()
    db.commit()

    from app.db.models import PredictionMarket
    market = db.query(PredictionMarket).first()

    # Too high
    response = client.post(
        "/api/probability/predictions",
        headers={"Authorization": f"Bearer {token}"},
        json={"market_id": market.id, "probability": 1.5}
    )
    assert response.status_code == 422  # Pydantic validation

    # Too low
    response = client.post(
        "/api/probability/predictions",
        headers={"Authorization": f"Bearer {token}"},
        json={"market_id": market.id, "probability": -0.1}
    )
    assert response.status_code == 422


def test_duplicate_prediction(client, db):
    """Can't predict same market twice, returns 409."""
    token = get_token(client)

    service = ProbabilityService(db)
    service.seed_markets_if_empty()
    db.commit()

    from app.db.models import PredictionMarket
    market = db.query(PredictionMarket).first()

    # First prediction
    response1 = client.post(
        "/api/probability/predictions",
        headers={"Authorization": f"Bearer {token}"},
        json={"market_id": market.id, "probability": 0.65}
    )
    assert response1.status_code == 200

    # Second prediction on same market
    response2 = client.post(
        "/api/probability/predictions",
        headers={"Authorization": f"Bearer {token}"},
        json={"market_id": market.id, "probability": 0.70}
    )
    assert response2.status_code == 409
    assert "already predicted" in response2.json()["detail"].lower()


def test_market_probability_revealed(client, db):
    """Market probability is revealed AFTER submission."""
    token = get_token(client)

    service = ProbabilityService(db)
    service.seed_markets_if_empty()
    db.commit()

    from app.db.models import PredictionMarket
    market = db.query(PredictionMarket).first()

    # Before prediction: probability hidden
    response1 = client.get(
        f"/api/probability/markets/{market.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response1.status_code == 200
    assert response1.json()["market_probability"] is None

    # Submit prediction
    client.post(
        "/api/probability/predictions",
        headers={"Authorization": f"Bearer {token}"},
        json={"market_id": market.id, "probability": 0.65}
    )

    # After prediction: probability revealed
    response2 = client.get(
        f"/api/probability/markets/{market.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response2.status_code == 200
    assert response2.json()["market_probability"] is not None


def test_brier_score_calculation(db):
    """Verify Brier score: (0.7 - 1)^2 = 0.09."""
    service = ProbabilityService(db)

    # Predicted 70%, actual was yes (1)
    score = service.calculate_brier_score(0.7, 1)
    assert abs(score - 0.09) < 0.001

    # Predicted 70%, actual was no (0)
    score = service.calculate_brier_score(0.7, 0)
    assert abs(score - 0.49) < 0.001

    # Perfect prediction
    score = service.calculate_brier_score(1.0, 1)
    assert score == 0.0


def test_calibration_calculation(client, db):
    """Verify calibration bucket grouping."""
    token = get_token(client)

    service = ProbabilityService(db)
    service.seed_markets_if_empty()
    db.commit()

    # Make some predictions
    from app.db.models import PredictionMarket
    markets = db.query(PredictionMarket).limit(3).all()

    for i, market in enumerate(markets):
        client.post(
            "/api/probability/predictions",
            headers={"Authorization": f"Bearer {token}"},
            json={"market_id": market.id, "probability": 0.3 + i * 0.2}
        )

    # Get calibration
    response = client.get(
        "/api/probability/calibration",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_predictions"] == 3


def test_bias_detection_overconfidence(db):
    """Detect overconfidence pattern."""
    service = ProbabilityService(db)
    service.seed_markets_if_empty()
    db.commit()

    from app.db.models import PredictionMarket, UserPrediction

    # Create resolved markets and predictions with overconfidence pattern
    markets = db.query(PredictionMarket).limit(5).all()

    _ensure_test_user(db, "test-user")

    # Simulate resolved predictions with overconfidence
    all_preds = []
    resolved_preds = []
    for i, market in enumerate(markets):
        market.is_resolved = True
        market.resolution = "no"  # All resolved to NO

        pred = UserPrediction(
            user_id="test-user",
            market_id=market.id,
            predicted_probability=0.9,  # Predicted 90% YES (overconfident)
            brier_score=0.81,  # High Brier = wrong
        )
        db.add(pred)
        all_preds.append(pred)
        resolved_preds.append(pred)

    db.commit()

    biases = service._detect_biases(all_preds, resolved_preds)
    assert "overconfidence" in biases


def test_bias_detection_extreme_aversion(db):
    """Detect extreme aversion pattern."""
    service = ProbabilityService(db)
    service.seed_markets_if_empty()
    db.commit()

    from app.db.models import PredictionMarket, UserPrediction

    markets = db.query(PredictionMarket).limit(6).all()

    _ensure_test_user(db, "test-user-2")

    # Create predictions that cluster in the middle (40-60%)
    all_preds = []
    for i, market in enumerate(markets):
        pred = UserPrediction(
            user_id="test-user-2",
            market_id=market.id,
            predicted_probability=0.45 + (i % 3) * 0.05,  # All between 0.45-0.55
        )
        db.add(pred)
        all_preds.append(pred)

    db.commit()

    biases = service._detect_biases(all_preds, [])
    assert "extreme_aversion" in biases


def test_get_calibration(client, db):
    """GET /api/probability/calibration returns calibration data."""
    token = get_token(client)

    response = client.get(
        "/api/probability/calibration",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_predictions" in data
    assert "average_brier_score" in data
    assert "calibration_curve" in data
    assert "detected_biases" in data


def test_get_user_predictions(client, db):
    """GET /api/probability/predictions returns user's predictions."""
    token = get_token(client)

    service = ProbabilityService(db)
    service.seed_markets_if_empty()
    db.commit()

    from app.db.models import PredictionMarket
    market = db.query(PredictionMarket).first()

    # Make a prediction
    client.post(
        "/api/probability/predictions",
        headers={"Authorization": f"Bearer {token}"},
        json={"market_id": market.id, "probability": 0.65}
    )

    response = client.get(
        "/api/probability/predictions",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["predictions"][0]["predicted_probability"] == 0.65


@pytest.mark.asyncio
async def test_resolve_market(db):
    """Resolution triggers Brier scoring."""
    service = ProbabilityService(db)
    service.seed_markets_if_empty()
    db.commit()

    from app.db.models import PredictionMarket, UserPrediction

    market = db.query(PredictionMarket).first()

    _ensure_test_user(db, "test-resolver")

    # Create a prediction
    pred = UserPrediction(
        user_id="test-resolver",
        market_id=market.id,
        predicted_probability=0.7,
    )
    db.add(pred)
    db.commit()

    # Resolve market
    count = await service.resolve_predictions(market.id, "yes")

    assert count == 1

    # Check Brier score was calculated
    db.refresh(pred)
    assert pred.brier_score is not None
    assert abs(pred.brier_score - 0.09) < 0.001  # (0.7 - 1)^2


def test_seed_data_loaded(client, db):
    """Seed markets exist on startup."""
    token = get_token(client)

    service = ProbabilityService(db)
    service.seed_markets_if_empty()
    db.commit()

    from app.db.models import PredictionMarket
    count = db.query(PredictionMarket).count()

    assert count >= len(SEED_MARKETS)


def test_unauthenticated_rejected(client):
    """No token = 401."""
    response = client.get("/api/probability/markets")
    assert response.status_code == 401

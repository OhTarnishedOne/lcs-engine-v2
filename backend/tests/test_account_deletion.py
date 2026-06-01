"""
Tests for account deletion (DELETE /api/auth/me).
"""

import pytest
from app.db.models import (
    User, Profile, UserProfile, Conversation, Message,
    Strategy, TradeLog, UserPrediction, PredictionMarket,
    CalibrationScore,
)
from app.auth.utils import hash_password


def _create_user_with_data(db, email="delete-me@test.com", password="testpass123"):
    """Create a user with child records across all tables."""
    hashed = hash_password(password)
    user = User(email=email, password_hash=hashed, tier="pro")
    db.add(user)
    db.flush()

    # Profile
    profile = Profile(user_id=user.id, onboarding_complete=True)
    db.add(profile)

    # UserProfile
    user_profile = UserProfile(
        user_id=user.id,
        persona="goal_focused",
        experience_level="intermediate",
        onboarding_completed=True,
    )
    db.add(user_profile)

    # Conversation + Message
    conv = Conversation(user_id=user.id, title="Test chat")
    db.add(conv)
    db.flush()
    msg = Message(conversation_id=conv.id, role="user", content="Hello")
    db.add(msg)

    # Strategy
    strategy = Strategy(
        user_id=user.id,
        name="Test Strategy",
        description="Test",
        strategy_type="balanced",
        risk_level=3,
        time_horizon="medium",
        assets=[{"ticker": "SPY", "allocation_pct": 100}],
        rationale="Test",
        risks="Test",
    )
    db.add(strategy)

    # TradeLog
    trade = TradeLog(
        user_id=user.id,
        symbol="AAPL",
        side="buy",
        qty=10,
        order_type="market",
        status="filled",
    )
    db.add(trade)

    # PredictionMarket + UserPrediction
    from datetime import datetime, UTC
    market = PredictionMarket(
        title="Test market",
        category="cpi",
        close_date=datetime.now(UTC),
    )
    db.add(market)
    db.flush()
    prediction = UserPrediction(
        user_id=user.id,
        market_id=market.id,
        predicted_probability=0.7,
    )
    db.add(prediction)

    # CalibrationScore
    cal = CalibrationScore(
        user_id=user.id,
        total_predictions=1,
        resolved_predictions=0,
    )
    db.add(cal)

    db.commit()
    return user


class TestAccountDeletion:
    """Tests for DELETE /api/auth/me."""

    def test_successful_deletion_with_correct_password(self, client, db):
        user = _create_user_with_data(db)
        user_id = user.id

        # Login first
        login_resp = client.post("/api/auth/login", json={
            "email": "delete-me@test.com",
            "password": "testpass123",
        })
        token = login_resp.json()["access_token"]

        # Delete
        resp = client.request("DELETE", "/api/auth/me",
            json={"password": "testpass123"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

        # Verify user is gone
        db.expire_all()
        assert db.query(User).filter(User.id == user_id).first() is None

    def test_all_child_rows_deleted_after_user_deletion(self, client, db):
        user = _create_user_with_data(db)
        user_id = user.id

        login_resp = client.post("/api/auth/login", json={
            "email": "delete-me@test.com",
            "password": "testpass123",
        })
        token = login_resp.json()["access_token"]

        client.request("DELETE", "/api/auth/me",
            json={"password": "testpass123"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Verify all child records are gone
        assert db.query(Profile).filter(Profile.user_id == user_id).first() is None
        assert db.query(UserProfile).filter(UserProfile.user_id == user_id).first() is None
        assert db.query(Conversation).filter(Conversation.user_id == user_id).first() is None
        assert db.query(Strategy).filter(Strategy.user_id == user_id).first() is None
        assert db.query(TradeLog).filter(TradeLog.user_id == user_id).first() is None
        assert db.query(UserPrediction).filter(UserPrediction.user_id == user_id).first() is None
        assert db.query(CalibrationScore).filter(CalibrationScore.user_id == user_id).first() is None

    def test_wrong_password_returns_401(self, client, db):
        _create_user_with_data(db)

        login_resp = client.post("/api/auth/login", json={
            "email": "delete-me@test.com",
            "password": "testpass123",
        })
        token = login_resp.json()["access_token"]

        resp = client.request("DELETE", "/api/auth/me",
            json={"password": "wrongpassword"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401

        # User should still exist
        assert db.query(User).filter(User.email == "delete-me@test.com").first() is not None

    def test_no_auth_returns_401(self, client, db):
        resp = client.request("DELETE", "/api/auth/me",
            json={"password": "anything"},
        )
        assert resp.status_code in (401, 403)

    def test_deleting_already_deleted_account_returns_401(self, client, db):
        user = _create_user_with_data(db)

        login_resp = client.post("/api/auth/login", json={
            "email": "delete-me@test.com",
            "password": "testpass123",
        })
        token = login_resp.json()["access_token"]

        # First delete — succeeds
        resp1 = client.request("DELETE", "/api/auth/me",
            json={"password": "testpass123"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp1.status_code == 204

        # Second delete with same token — should fail (user gone, token invalid)
        resp2 = client.request("DELETE", "/api/auth/me",
            json={"password": "testpass123"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp2.status_code == 401

    def test_missing_password_returns_400(self, client, db):
        _create_user_with_data(db)

        login_resp = client.post("/api/auth/login", json={
            "email": "delete-me@test.com",
            "password": "testpass123",
        })
        token = login_resp.json()["access_token"]

        resp = client.request("DELETE", "/api/auth/me",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

"""
Canonical Decision API — create / read / list / lock / resolve.

Exercises the Sprint 2 decision lifecycle service through its HTTP surface,
plus the resolution -> scoring pipeline and idempotency guarantees.
"""

import uuid
from uuid import UUID

import pytest

from app.db.models import User
from app.db.models.gamification import (
    BadgeSlug,
    Decision,
    DecisionStatus,
    UserBadge,
    UserGamificationProfile,
)
from app.gamification.user_ids import user_id_to_uuid


def _register(client):
    email = f"dec_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": "testpass123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"], email


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _profile(db, email):
    user = db.query(User).filter(User.email == email).one()
    uid = user_id_to_uuid(user.id)
    return (
        db.query(UserGamificationProfile)
        .filter(UserGamificationProfile.user_id == uid)
        .one()
    ), uid


# --------------------------------------------------------------------------- create / read

def test_create_decision_is_locked_by_default(client):
    token, _ = _register(client)
    resp = client.post(
        "/api/decisions",
        json={"question": "Will X happen?", "confidence": 0.7, "reasoning": "because"},
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["confidence"] == 0.7
    assert body["status"] == "pending"
    assert body["domain"] == "investing"
    assert body["locked_at"] is not None


def test_create_decision_draft_is_unlocked(client):
    token, _ = _register(client)
    resp = client.post(
        "/api/decisions",
        json={"question": "Draft?", "confidence": 0.5, "lock": False},
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["locked_at"] is None


def test_get_decision_roundtrip(client):
    token, _ = _register(client)
    created = client.post(
        "/api/decisions",
        json={"question": "Q?", "confidence": 0.6, "domain": "career"},
        headers=_auth(token),
    ).json()

    resp = client.get(f"/api/decisions/{created['id']}", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]
    assert resp.json()["domain"] == "career"


def test_get_missing_decision_404(client):
    token, _ = _register(client)
    resp = client.get(f"/api/decisions/{uuid.uuid4()}", headers=_auth(token))
    assert resp.status_code == 404


def test_cannot_read_another_users_decision(client):
    token_a, _ = _register(client)
    token_b, _ = _register(client)
    created = client.post(
        "/api/decisions",
        json={"question": "Mine", "confidence": 0.6},
        headers=_auth(token_a),
    ).json()

    resp = client.get(f"/api/decisions/{created['id']}", headers=_auth(token_b))
    assert resp.status_code == 404


def test_list_decisions_scoped_and_filtered(client):
    token, _ = _register(client)
    for i in range(3):
        client.post(
            "/api/decisions",
            json={"question": f"Q{i}", "confidence": 0.5},
            headers=_auth(token),
        )

    resp = client.get("/api/decisions", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["decisions"]) == 3

    resolved = client.get(
        "/api/decisions", params={"status": "resolved"}, headers=_auth(token)
    )
    assert resolved.json()["total"] == 0


# --------------------------------------------------------------------------- lock enforcement

def test_patch_locked_decision_rejected(client):
    token, _ = _register(client)
    did = client.post(
        "/api/decisions",
        json={"question": "Q", "confidence": 0.7, "reasoning": "orig"},
        headers=_auth(token),
    ).json()["id"]

    for field, value in [
        ("confidence", 0.2),
        ("reasoning", "rewritten"),
        ("falsification", "moved goalposts"),
    ]:
        resp = client.patch(
            f"/api/decisions/{did}", json={field: value}, headers=_auth(token)
        )
        assert resp.status_code == 400, (field, resp.text)
        assert resp.json()["detail"] == "Decision is locked and cannot be modified"


def test_patch_unlocked_decision_allowed(client):
    token, _ = _register(client)
    did = client.post(
        "/api/decisions",
        json={"question": "Q", "confidence": 0.7, "lock": False},
        headers=_auth(token),
    ).json()["id"]

    resp = client.patch(
        f"/api/decisions/{did}",
        json={"confidence": 0.55, "reasoning": "added"},
        headers=_auth(token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["confidence"] == 0.55
    assert body["reasoning"] == "added"


# --------------------------------------------------------------------------- resolve + scoring

def test_resolve_runs_scoring_pipeline(client, db):
    token, email = _register(client)
    did = client.post(
        "/api/decisions",
        json={"question": "Q", "confidence": 0.9, "reasoning": "r"},
        headers=_auth(token),
    ).json()["id"]

    resp = client.post(
        f"/api/decisions/{did}/resolve",
        json={"outcome_binary": True, "outcome_source": "self_reported"},
        headers=_auth(token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["already_resolved"] is False
    assert body["brier_score"] == pytest.approx(0.01)  # (0.9 - 1)^2
    assert body["is_calibrated"] is True

    decision = db.query(Decision).filter(Decision.id == UUID(did)).one()
    assert decision.status == DecisionStatus.RESOLVED
    assert decision.brier_score is not None
    assert decision.resolved_at is not None

    profile, _ = _profile(db, email)
    assert profile.resolved_calls == 1
    assert profile.process_score > 0
    assert profile.calibration_streak == 1


def test_resolve_is_idempotent(client, db):
    token, email = _register(client)
    did = client.post(
        "/api/decisions",
        json={"question": "Q", "confidence": 0.8},
        headers=_auth(token),
    ).json()["id"]

    first = client.post(
        f"/api/decisions/{did}/resolve",
        json={"outcome_binary": True},
        headers=_auth(token),
    ).json()
    assert first["already_resolved"] is False

    profile, _ = _profile(db, email)
    points_after_first = profile.total_points
    resolved_after_first = profile.resolved_calls

    second = client.post(
        f"/api/decisions/{did}/resolve",
        json={"outcome_binary": True},
        headers=_auth(token),
    ).json()
    assert second["already_resolved"] is True

    db.refresh(profile)
    assert profile.total_points == points_after_first
    assert profile.resolved_calls == resolved_after_first


def test_full_api_lifecycle_awards_calibrated_run(client, db):
    """
    Create and resolve five well-calibrated decisions through the API; the
    calibration streak reaches 5 and CALIBRATED_RUN is earned exactly once,
    with the calibration family unlocked.
    """
    token, email = _register(client)

    for _ in range(5):
        did = client.post(
            "/api/decisions",
            json={"question": "Q", "confidence": 0.95, "reasoning": "r"},
            headers=_auth(token),
        ).json()["id"]
        resp = client.post(
            f"/api/decisions/{did}/resolve",
            json={"outcome_binary": True},
            headers=_auth(token),
        )
        assert resp.status_code == 200

    profile, uid = _profile(db, email)
    assert profile.resolved_calls == 5
    assert profile.calibration_streak == 5
    assert profile.calibration_score == 99.5  # 100 * (1 - 2 * 0.0025)

    cal_run = (
        db.query(UserBadge)
        .filter(
            UserBadge.user_id == uid,
            UserBadge.badge_slug == BadgeSlug.CALIBRATED_RUN,
        )
        .count()
    )
    assert cal_run == 1

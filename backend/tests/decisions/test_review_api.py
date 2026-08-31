"""
Reflection API — submit / fetch a decision review + the journal view.

Covers the Good Loser / Humble Winner badge integration, reflection score
refresh, single-review enforcement, and ownership isolation.
"""

import uuid
from uuid import UUID

from app.db.models import User
from app.db.models.gamification import DecisionReview, UserGamificationProfile
from app.gamification.user_ids import user_id_to_uuid


def _register(client):
    email = f"rev_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": "testpass123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"], email


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _create_resolved(client, token, *, confidence, outcome):
    did = client.post(
        "/api/decisions",
        json={"question": "Q", "confidence": confidence, "reasoning": "r"},
        headers=_auth(token),
    ).json()["id"]
    resp = client.post(
        f"/api/decisions/{did}/resolve",
        json={"outcome_binary": outcome},
        headers=_auth(token),
    )
    assert resp.status_code == 200, resp.text
    return did


def _profile(db, email):
    user = db.query(User).filter(User.email == email).one()
    uid = user_id_to_uuid(user.id)
    return (
        db.query(UserGamificationProfile)
        .filter(UserGamificationProfile.user_id == uid)
        .one()
    )


# --------------------------------------------------------------------------- submit

def test_submit_review_records_and_scores(client, db):
    token, email = _register(client)
    did = _create_resolved(client, token, confidence=0.8, outcome=True)

    resp = client.post(
        f"/api/decisions/{did}/review",
        json={
            "outcome_attribution": "My thesis held up.",
            "was_process_sound": True,
            "luck_vs_process": "process",
        },
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["review"]["decision_id"] == did
    assert body["review"]["reflection_points"] > 0
    assert body["reflection_score"] is not None

    profile = _profile(db, email)
    assert profile.reviewed_calls == 1
    assert profile.reflection_score is not None


def test_good_loser_badge_awarded_on_review(client, db):
    """Wrong outcome + sound process + honest attribution -> Good Loser."""
    token, _ = _register(client)
    did = _create_resolved(client, token, confidence=0.8, outcome=False)

    resp = client.post(
        f"/api/decisions/{did}/review",
        json={
            "outcome_attribution": "Sound macro read; an exogenous shock hit.",
            "was_process_sound": True,
            "luck_vs_process": "luck",
        },
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    assert "good_loser" in resp.json()["badges_awarded"]
    assert resp.json()["review"]["triggers_good_loser"] is True


def test_humble_winner_badge_awarded_on_review(client):
    """Right outcome + weak process + honest admission -> Humble Winner."""
    token, _ = _register(client)
    did = _create_resolved(client, token, confidence=0.8, outcome=True)

    resp = client.post(
        f"/api/decisions/{did}/review",
        json={
            "outcome_attribution": "Got lucky — my reasoning was thin.",
            "was_process_sound": False,
            "luck_vs_process": "luck",
        },
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    assert "humble_winner" in resp.json()["badges_awarded"]
    assert resp.json()["review"]["triggers_humble_winner"] is True


def test_cannot_review_unresolved_decision(client):
    token, _ = _register(client)
    did = client.post(
        "/api/decisions",
        json={"question": "Q", "confidence": 0.6},
        headers=_auth(token),
    ).json()["id"]

    resp = client.post(
        f"/api/decisions/{did}/review",
        json={"outcome_attribution": "x", "was_process_sound": True},
        headers=_auth(token),
    )
    assert resp.status_code == 409


def test_cannot_review_twice(client):
    token, _ = _register(client)
    did = _create_resolved(client, token, confidence=0.7, outcome=True)
    body = {"outcome_attribution": "x", "was_process_sound": True}

    first = client.post(
        f"/api/decisions/{did}/review", json=body, headers=_auth(token)
    )
    assert first.status_code == 201
    second = client.post(
        f"/api/decisions/{did}/review", json=body, headers=_auth(token)
    )
    assert second.status_code == 409


def test_cannot_review_another_users_decision(client):
    token_a, _ = _register(client)
    token_b, _ = _register(client)
    did = _create_resolved(client, token_a, confidence=0.7, outcome=True)

    resp = client.post(
        f"/api/decisions/{did}/review",
        json={"outcome_attribution": "x", "was_process_sound": True},
        headers=_auth(token_b),
    )
    assert resp.status_code == 404


# --------------------------------------------------------------------------- fetch / journal

def test_get_review_roundtrip(client):
    token, _ = _register(client)
    did = _create_resolved(client, token, confidence=0.7, outcome=True)

    missing = client.get(f"/api/decisions/{did}/review", headers=_auth(token))
    assert missing.status_code == 404

    client.post(
        f"/api/decisions/{did}/review",
        json={"outcome_attribution": "note", "was_process_sound": True},
        headers=_auth(token),
    )
    resp = client.get(f"/api/decisions/{did}/review", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["outcome_attribution"] == "note"


def test_journal_lists_resolved_with_reviews(client):
    token, _ = _register(client)
    reviewed = _create_resolved(client, token, confidence=0.7, outcome=True)
    _unreviewed = _create_resolved(client, token, confidence=0.6, outcome=False)
    # An unresolved decision must not appear in the journal.
    client.post(
        "/api/decisions",
        json={"question": "pending", "confidence": 0.5},
        headers=_auth(token),
    )
    client.post(
        f"/api/decisions/{reviewed}/review",
        json={"outcome_attribution": "done", "was_process_sound": True},
        headers=_auth(token),
    )

    resp = client.get("/api/decisions/journal", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2  # two resolved, pending excluded

    by_id = {e["decision"]["id"]: e for e in body["entries"]}
    assert by_id[reviewed]["review"] is not None
    assert by_id[reviewed]["review"]["outcome_attribution"] == "done"
    assert by_id[_unreviewed]["review"] is None

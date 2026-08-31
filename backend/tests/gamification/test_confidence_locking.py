"""
Confidence-locking enforcement on the Decision update route.

Once a decision's `locked_at` is set, its forecast fields (confidence,
reasoning, falsification) are immutable — any PATCH attempting to change them
is rejected with HTTP 400. This protects calibration integrity: you cannot
rewrite a prediction after learning how reality moved.
"""

import uuid
from datetime import datetime

from app.auth.utils import hash_password
from app.db.models import User
from app.db.models.gamification import Decision, DecisionDomain, DecisionStatus
from app.gamification.user_ids import user_id_to_uuid

LOCK_ERROR = "Decision is locked and cannot be modified"


def _register(client):
    email = f"lock_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": "testpass123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"], email


def _make_decision(db, user, *, locked):
    decision = Decision(
        user_id=user_id_to_uuid(user.id),
        question="Will CPI fall below 3% this year?",
        domain=DecisionDomain.INVESTING,
        confidence=0.70,
        reasoning="Original reasoning",
        falsification="Original falsification",
        status=DecisionStatus.PENDING,
        locked_at=datetime.utcnow() if locked else None,
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)

    if not locked:
        # `locked_at` has a func.now() column default; force it NULL explicitly
        # so the "unlocked" control genuinely has no lock.
        decision.locked_at = None
        db.commit()
        db.refresh(decision)

    return decision


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_confidence_cannot_change_after_lock(client, db):
    token, email = _register(client)
    user = db.query(User).filter(User.email == email).one()
    decision = _make_decision(db, user, locked=True)

    resp = client.patch(
        f"/api/gamification/decisions/{decision.id}",
        json={"confidence": 0.20},
        headers=_auth(token),
    )

    assert resp.status_code == 400
    assert resp.json()["detail"] == LOCK_ERROR

    db.refresh(decision)
    assert decision.confidence == 0.70


def test_reasoning_cannot_change_after_lock(client, db):
    token, email = _register(client)
    user = db.query(User).filter(User.email == email).one()
    decision = _make_decision(db, user, locked=True)

    resp = client.patch(
        f"/api/gamification/decisions/{decision.id}",
        json={"reasoning": "Rewritten after seeing the outcome"},
        headers=_auth(token),
    )

    assert resp.status_code == 400
    assert resp.json()["detail"] == LOCK_ERROR

    db.refresh(decision)
    assert decision.reasoning == "Original reasoning"


def test_falsification_cannot_change_after_lock(client, db):
    token, email = _register(client)
    user = db.query(User).filter(User.email == email).one()
    decision = _make_decision(db, user, locked=True)

    resp = client.patch(
        f"/api/gamification/decisions/{decision.id}",
        json={"falsification": "Moved the goalposts"},
        headers=_auth(token),
    )

    assert resp.status_code == 400
    assert resp.json()["detail"] == LOCK_ERROR

    db.refresh(decision)
    assert decision.falsification == "Original falsification"


def test_unlocked_decision_can_be_edited(client, db):
    """Control: the guard is conditional on the lock, not a blanket reject."""
    token, email = _register(client)
    user = db.query(User).filter(User.email == email).one()
    decision = _make_decision(db, user, locked=False)

    resp = client.patch(
        f"/api/gamification/decisions/{decision.id}",
        json={"confidence": 0.42, "reasoning": "Refined before locking"},
        headers=_auth(token),
    )

    assert resp.status_code == 200, resp.text
    db.refresh(decision)
    assert decision.confidence == 0.42
    assert decision.reasoning == "Refined before locking"

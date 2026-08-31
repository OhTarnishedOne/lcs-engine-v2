"""
Diagnosis -> AI tutor wiring.

The chat tutor's system prompt should surface the student's measured decision
weakness (and active training mission) so coaching is grounded in their data.
Tests the context assembly directly — no AI client / API key required.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from app.auth.utils import hash_password
from app.chat.service import ChatService
from app.db.models import User
from app.services.decisions.decision_service import DecisionService
from app.services.interventions.intervention_service import InterventionService


def _make_user(db):
    uid = uuid4()
    db.add(
        User(
            id=str(uid),
            email=f"{uid}@test.com",
            password_hash=hash_password("test"),
        )
    )
    db.flush()
    return uid


def _seed_overconfident(db, uid, n=5):
    service = DecisionService(db)
    for _ in range(n):
        decision = service.create_decision(user_id=uid, question="Q", confidence=0.9)
        service.resolve_decision(decision, outcome_binary=False)  # all miss
    db.flush()


def test_diagnosis_context_surfaces_primary_weakness(db):
    uid = _make_user(db)
    _seed_overconfident(db, uid)

    service = ChatService(db, MagicMock())
    context = service._get_diagnosis_context(str(uid))

    assert context is not None
    assert "Primary weakness" in context
    assert "Overconfidence" in context
    assert "5 resolved decisions" in context


def test_diagnosis_context_includes_active_intervention(db):
    uid = _make_user(db)
    _seed_overconfident(db, uid)
    InterventionService(db).start(uid)  # premortem mission from the diagnosis
    db.flush()

    context = ChatService(db, MagicMock())._get_diagnosis_context(str(uid))
    assert context is not None
    assert "Active training mission" in context
    assert "Pre-mortem" in context


def test_no_diagnosis_context_without_enough_data(db):
    uid = _make_user(db)
    # Only two resolved decisions -> diagnosis is still "building".
    _seed_overconfident(db, uid, n=2)

    context = ChatService(db, MagicMock())._get_diagnosis_context(str(uid))
    assert context is None


def test_diagnosis_context_failure_is_swallowed(db):
    # A malformed user id must not raise — chat must never break on this.
    context = ChatService(db, MagicMock())._get_diagnosis_context("not-a-uuid")
    assert context is None

"""
Canonical Decision lifecycle service.

Single entry point for creating, reading, locking, updating, and resolving a
`Decision` — independent of any one domain (investing, career, business, ...).
Probability Lab keeps its own dual-write bridge for now; this service is the
canonical path for directly-created decisions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.gamification import (
    Decision,
    DecisionDomain,
    DecisionStatus,
    OutcomeSource,
    UserGamificationProfile,
)
from app.services.decisions.resolution_service import (
    ResolutionResult,
    ResolutionService,
)

# Once a decision is locked, these forecast fields are immutable. Editing them
# after the fact would corrupt calibration scoring — you cannot retroactively
# change what you predicted once you know how reality moved.
LOCKED_DECISION_FIELDS = ("confidence", "reasoning", "falsification")


class DecisionNotFoundError(Exception):
    """Decision does not exist or is not owned by the requesting user."""


class DecisionLockedError(Exception):
    """A locked forecast field was edited after `locked_at` was set."""


class DecisionService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------ profile

    def _get_or_create_profile(self, user_id: UUID) -> UserGamificationProfile:
        profile = (
            self.db.query(UserGamificationProfile)
            .filter(UserGamificationProfile.user_id == user_id)
            .first()
        )
        if profile is None:
            profile = UserGamificationProfile(user_id=user_id)
            self.db.add(profile)
            self.db.flush()
        return profile

    # ------------------------------------------------------------------ create

    def create_decision(
        self,
        *,
        user_id: UUID,
        question: str,
        confidence: float,
        domain: DecisionDomain = DecisionDomain.INVESTING,
        reasoning: Optional[str] = None,
        falsification: Optional[str] = None,
        resolution_date: Optional[datetime] = None,
        is_curated: bool = False,
        question_id: Optional[UUID] = None,
        lock: bool = True,
    ) -> Decision:
        """
        Log a new decision. By default it is locked immediately — a committed
        forecast — so confidence/reasoning/falsification become immutable.
        Pass ``lock=False`` to keep it as an editable draft.

        Increments the profile's ``total_calls`` so that the process-score
        rolling average has the correct call number at resolution time.
        """
        profile = self._get_or_create_profile(user_id)

        decision = Decision(
            user_id=user_id,
            question=question,
            domain=domain,
            confidence=confidence,
            reasoning=reasoning,
            falsification=falsification,
            resolution_date=resolution_date,
            is_curated=is_curated,
            question_id=question_id,
            status=DecisionStatus.PENDING,
            locked_at=datetime.utcnow() if lock else None,
        )
        self.db.add(decision)

        profile.total_calls += 1

        self.db.flush()

        # `Decision.locked_at` has a func.now() column default that fires on
        # INSERT even when we pass None, so a draft would come back locked.
        # Clear it with a post-insert UPDATE (defaults don't apply on UPDATE).
        if not lock and decision.locked_at is not None:
            decision.locked_at = None
            self.db.flush()

        return decision

    # -------------------------------------------------------------------- reads

    def get_decision(self, decision_id: UUID, user_id: UUID) -> Decision:
        decision = (
            self.db.query(Decision).filter(Decision.id == decision_id).first()
        )
        if decision is None or str(decision.user_id) != str(user_id):
            # Same error for "missing" and "not yours" — don't leak existence.
            raise DecisionNotFoundError(str(decision_id))
        return decision

    def list_decisions(
        self,
        user_id: UUID,
        *,
        status: Optional[DecisionStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Decision]:
        query = self.db.query(Decision).filter(Decision.user_id == user_id)
        if status is not None:
            query = query.filter(Decision.status == status)
        return (
            query.order_by(Decision.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    # ------------------------------------------------------------------ mutate

    def lock_decision(self, decision: Decision) -> Decision:
        """Idempotently stamp ``locked_at`` (freeze the forecast)."""
        if decision.locked_at is None:
            decision.locked_at = datetime.utcnow()
            self.db.flush()
        return decision

    def update_decision(self, decision: Decision, changes: dict) -> Decision:
        """
        Apply a partial update. Only fields present in ``changes`` are touched.
        If the decision is locked and any locked forecast field is among the
        changes, raise ``DecisionLockedError`` (mapped to HTTP 400 by the route).
        """
        attempted_locked_edits = [
            field for field in LOCKED_DECISION_FIELDS if field in changes
        ]
        if decision.locked_at is not None and attempted_locked_edits:
            raise DecisionLockedError(", ".join(attempted_locked_edits))

        for field, value in changes.items():
            setattr(decision, field, value)
        self.db.flush()
        return decision

    # ----------------------------------------------------------------- resolve

    def resolve_decision(
        self,
        decision: Decision,
        *,
        outcome_binary: bool,
        outcome_source: OutcomeSource = OutcomeSource.SELF_REPORTED,
        outcome_notes: Optional[str] = None,
    ) -> ResolutionResult:
        """
        Resolve the decision and run the full scoring pipeline. The heavy
        lifting (Brier -> score families -> badges) lives in ResolutionService,
        which owns the transaction boundary conceptually; the caller commits.
        """
        return ResolutionService(self.db).resolve(
            decision,
            outcome_binary=outcome_binary,
            outcome_source=outcome_source,
            outcome_notes=outcome_notes,
        )

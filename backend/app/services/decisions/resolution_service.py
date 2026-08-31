"""
Resolution service — the single event that starts the downstream scoring
pipeline for a Decision.

resolve() atomically writes the outcome, computes the Brier score, rolls the
result into the four score families, and evaluates badges. It is idempotent:
resolving an already-resolved decision returns the stored result without
recomputation or double-counting.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.gamification import (
    Decision,
    DecisionStatus,
    OutcomeSource,
    UserGamificationProfile,
)
from app.services.gamification.badge_evaluator import (
    PointsBadgeEvaluator,
    PointsBadgeResult,
)
from app.services.gamification.brier import BrierResult, BrierScoreCalculator
from app.services.gamification.score_family_updater import (
    ScoreFamilyUpdate,
    ScoreFamilyUpdater,
)


@dataclass
class ResolutionResult:
    decision_id: UUID
    brier: Optional[BrierResult]
    score_update: Optional[ScoreFamilyUpdate]
    badge_result: Optional[PointsBadgeResult]
    already_resolved: bool


class ResolutionService:
    def __init__(self, db: Session):
        self.db = db

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

    def resolve(
        self,
        decision: Decision,
        *,
        outcome_binary: bool,
        outcome_source: OutcomeSource = OutcomeSource.SELF_REPORTED,
        outcome_notes: Optional[str] = None,
    ) -> ResolutionResult:
        # Idempotency: an already-scored decision is a no-op.
        if (
            decision.status == DecisionStatus.RESOLVED
            and decision.brier_score is not None
        ):
            return ResolutionResult(
                decision_id=decision.id,
                brier=None,
                score_update=None,
                badge_result=None,
                already_resolved=True,
            )

        outcome_binary = bool(outcome_binary)

        # 1. Write the outcome.
        decision.status = DecisionStatus.RESOLVED
        decision.outcome_binary = outcome_binary
        decision.outcome_source = outcome_source
        decision.outcome_notes = outcome_notes
        decision.resolved_at = decision.resolved_at or datetime.utcnow()

        # 2. Brier calculation for this decision.
        brier = BrierScoreCalculator.calculate(decision.confidence, outcome_binary)
        decision.brier_score = brier.brier_score
        decision.calibration_delta = brier.calibration_gap_pct
        self.db.flush()

        # 3. Roll into the four score families.
        profile = self._get_or_create_profile(decision.user_id)
        score_update = ScoreFamilyUpdater(self.db).update_after_resolution(
            decision, profile
        )

        # 4. Evaluate badges against the new state.
        badge_result = PointsBadgeEvaluator(self.db).on_decision_resolved(
            decision,
            brier.is_calibrated,
            profile,
            score_update,
        )

        self.db.flush()

        return ResolutionResult(
            decision_id=decision.id,
            brier=brier,
            score_update=score_update,
            badge_result=badge_result,
            already_resolved=False,
        )

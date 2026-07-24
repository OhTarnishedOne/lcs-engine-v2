"""
Dual-write bridge: Probability Lab resolution -> gamification Decision pipeline.

Failures are logged and re-raised only to the caller's try/except wrapper so Lab
resolution never depends on gamification succeeding.
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.gamification import (
    Decision,
    DecisionDomain,
    DecisionStatus,
    OutcomeSource,
    UserGamificationProfile,
)
from app.db.models.probability import PredictionMarket, UserPrediction
from app.gamification.user_ids import user_id_to_uuid
from app.services.gamification.badge_evaluator import PointsBadgeEvaluator
from app.services.gamification.brier import BrierScoreCalculator
from app.services.gamification.score_family_updater import ScoreFamilyUpdater

logger = logging.getLogger(__name__)


def _get_or_create_profile(db: Session, user_id: UUID) -> UserGamificationProfile:
    profile = (
        db.query(UserGamificationProfile)
        .filter(UserGamificationProfile.user_id == user_id)
        .first()
    )
    if profile is None:
        profile = UserGamificationProfile(user_id=user_id)
        db.add(profile)
        db.flush()
    return profile


def sync_prediction_resolution_to_gamification(
    db: Session,
    prediction: UserPrediction,
    market: PredictionMarket,
    actual: int,
) -> None:
    """
    Mirror a resolved UserPrediction into the gamification Decision pipeline.

    Idempotent: re-processing the same prediction_id is a no-op.
    """
    decision_id = UUID(str(prediction.id))
    user_uuid = user_id_to_uuid(prediction.user_id)

    existing = db.query(Decision).filter(Decision.id == decision_id).first()
    if (
        existing is not None
        and existing.status == DecisionStatus.RESOLVED
        and existing.brier_score is not None
    ):
        return

    outcome_binary = bool(actual)
    brier_result = BrierScoreCalculator.calculate(
        prediction.predicted_probability,
        outcome_binary,
    )

    if existing is None:
        decision = Decision(
            id=decision_id,
            user_id=user_uuid,
            question=market.title,
            domain=DecisionDomain.INVESTING,
            confidence=prediction.predicted_probability,
            reasoning=prediction.reasoning,
            falsification=None,
            is_curated=False,
            status=DecisionStatus.RESOLVED,
            outcome_binary=outcome_binary,
            outcome_source=OutcomeSource.AUTO_MARKET,
            outcome_notes=f"Resolved via Probability Lab market {market.id}",
            resolved_at=datetime.utcnow(),
            brier_score=prediction.brier_score or brier_result.brier_score,
            calibration_delta=brier_result.calibration_gap_pct,
            extra={
                "source": "probability_lab",
                "prediction_id": prediction.id,
                "market_id": market.id,
                "market_resolution": market.resolution,
            },
        )
        db.add(decision)
        is_new_decision = True
    else:
        decision = existing
        decision.status = DecisionStatus.RESOLVED
        decision.outcome_binary = outcome_binary
        decision.outcome_source = OutcomeSource.AUTO_MARKET
        decision.brier_score = prediction.brier_score or brier_result.brier_score
        decision.calibration_delta = brier_result.calibration_gap_pct
        decision.resolved_at = decision.resolved_at or datetime.utcnow()
        is_new_decision = False

    db.flush()

    profile = _get_or_create_profile(db, user_uuid)
    if is_new_decision:
        profile.total_calls += 1

    score_update = ScoreFamilyUpdater(db).update_after_resolution(decision, profile)
    PointsBadgeEvaluator(db).on_decision_resolved(
        decision,
        brier_result.is_calibrated,
        profile,
        score_update,
    )
    db.flush()

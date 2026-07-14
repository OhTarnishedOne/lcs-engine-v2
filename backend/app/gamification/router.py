"""
Gamification API routes — Calibration Score, history, badges, evaluation.

Exposes the gamification engine (brier.py, score_family_updater.py,
badge_evaluator.py) to the frontend. Follows the existing route
conventions in backend/app/routes/.

Mount in app/main.py:
    from app.routes import gamification
    app.include_router(gamification.router)
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# --- Adjust these imports to match your actual module exports ---
from ..deps import get_db, get_current_user
from ..db.models import User

from app.services.gamification import brier
from app.services.gamification import score_family_updater
from app.services.gamification import badge_evaluator

router = APIRouter(tags=["gamification"])

# Minimum resolved predictions before a calibration score is displayed.
# Below this, the score is too volatile to be trustworthy — and trust is the brand.
MIN_SAMPLE_SIZE = 5


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class TrendDirection(str, Enum):
    improving = "improving"
    stable = "stable"
    declining = "declining"


class CalibrationScoreResponse(BaseModel):
    user_id: UUID
    calibration_score: Optional[float] = Field(
        None, description="User-facing 0–100 score. Null until minimum sample met."
    )
    brier_score: Optional[float] = Field(
        None, description="Raw Brier score (0 = perfect, lower is better)."
    )
    score_family: Optional[str] = Field(
        None, description="Current score family / tier name."
    )
    trend: Optional[TrendDirection] = None
    resolved_predictions: int
    minimum_sample_met: bool
    last_updated: Optional[datetime] = None


class ScoreHistoryPoint(BaseModel):
    date: datetime
    calibration_score: Optional[float]
    brier_score: Optional[float]
    predictions_resolved: int


class FamilyTransition(BaseModel):
    date: datetime
    from_family: str = Field(alias="from")
    to_family: str = Field(alias="to")

    class Config:
        populate_by_name = True


class ScoreHistoryResponse(BaseModel):
    user_id: UUID
    period: str
    points: list[ScoreHistoryPoint]
    score_family_transitions: list[FamilyTransition]


class EarnedBadge(BaseModel):
    badge_id: str
    name: str
    earned_at: datetime
    criteria_summary: str


class InProgressBadge(BaseModel):
    badge_id: str
    name: str
    progress: float = Field(ge=0.0, le=1.0)
    criteria_summary: str


class BadgesResponse(BaseModel):
    earned: list[EarnedBadge]
    in_progress: list[InProgressBadge]


class EvaluateRequest(BaseModel):
    prediction_id: UUID


class EvaluateResponse(BaseModel):
    prediction_id: UUID
    brier_delta: Optional[float] = Field(
        None, description="Change in rolling Brier score from this resolution."
    )
    new_calibration_score: Optional[float]
    family_changed: bool
    new_family: Optional[str] = None
    badges_awarded: list[str] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PERIODS: dict[str, Optional[timedelta]] = {
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
    "all": None,
}


def _resolve_period(period: str) -> Optional[datetime]:
    """Translate a period string into a cutoff datetime (None = all time)."""
    if period not in _PERIODS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid period '{period}'. Valid: {', '.join(_PERIODS)}",
        )
    delta = _PERIODS[period]
    return datetime.now(timezone.utc) - delta if delta else None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/calibration-score", response_model=CalibrationScoreResponse)
async def get_calibration_score(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CalibrationScoreResponse:
    """
    Current calibration state for the authenticated user.

    Returns the user-facing calibration score alongside the raw Brier score,
    current score family, and trend. Scores are null until the user has
    resolved MIN_SAMPLE_SIZE predictions — a volatile early score erodes
    trust in the metric.
    """
    # Materialized read — score_family_updater maintains state on write,
    # so this should be a simple lookup, not a recomputation.
    state = await score_family_updater.get_user_score_state(db, current_user.id)

    if state is None or state.resolved_count == 0:
        return CalibrationScoreResponse(
            user_id=current_user.id,
            resolved_predictions=0,
            minimum_sample_met=False,
        )

    sample_met = state.resolved_count >= MIN_SAMPLE_SIZE

    return CalibrationScoreResponse(
        user_id=current_user.id,
        calibration_score=state.calibration_score if sample_met else None,
        brier_score=state.brier_score if sample_met else None,
        score_family=state.family_name if sample_met else None,
        trend=state.trend if sample_met else None,
        resolved_predictions=state.resolved_count,
        minimum_sample_met=sample_met,
        last_updated=state.updated_at,
    )


@router.get("/score-history", response_model=ScoreHistoryResponse)
async def get_score_history(
    period: str = Query("30d", description="7d | 30d | 90d | all"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScoreHistoryResponse:
    """
    Time series of calibration/Brier scores plus score-family transitions.

    Feeds the trend chart. Family transitions are returned inline so the
    frontend can annotate level-ups without a second call.
    """
    cutoff = _resolve_period(period)

    points = await score_family_updater.get_score_history(
        db, current_user.id, since=cutoff
    )
    transitions = await score_family_updater.get_family_transitions(
        db, current_user.id, since=cutoff
    )

    return ScoreHistoryResponse(
        user_id=current_user.id,
        period=period,
        points=[
            ScoreHistoryPoint(
                date=p.date,
                calibration_score=p.calibration_score,
                brier_score=p.brier_score,
                predictions_resolved=p.predictions_resolved,
            )
            for p in points
        ],
        score_family_transitions=[
            FamilyTransition(date=t.date, **{"from": t.from_family, "to": t.to_family})
            for t in transitions
        ],
    )


@router.get("/badges", response_model=BadgesResponse)
async def get_badges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BadgesResponse:
    """
    Earned and in-progress badges for the authenticated user.

    `in_progress` includes a 0–1 progress fraction — the retention lever.
    Earned badges are trophies; almost-earned badges are tomorrow's login.
    """
    earned = await badge_evaluator.get_earned_badges(db, current_user.id)
    in_progress = await badge_evaluator.get_badge_progress(db, current_user.id)

    return BadgesResponse(
        earned=[
            EarnedBadge(
                badge_id=b.badge_id,
                name=b.name,
                earned_at=b.earned_at,
                criteria_summary=b.criteria_summary,
            )
            for b in earned
        ],
        in_progress=[
            InProgressBadge(
                badge_id=b.badge_id,
                name=b.name,
                progress=b.progress,
                criteria_summary=b.criteria_summary,
            )
            for b in in_progress
        ],
    )


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_prediction(
    payload: EvaluateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EvaluateResponse:
    """
    Run the full evaluation pipeline for a newly resolved prediction:
    Brier calculation → score family update → badge evaluation.

    Score-integrity guarantees:
      * The prediction must belong to the authenticated user.
      * The prediction must be resolved (outcome known).
      * Evaluation is idempotent — re-posting an already-evaluated
        prediction returns the stored result without recomputation.

    NOTE: If prediction resolution is system-driven (e.g. an outcome
    resolver job against market feeds), prefer calling the service layer
    directly from that job and restricting this route to an internal/admin
    scope. Users should never be able to force re-scoring.
    """
    prediction = await brier.get_prediction(db, payload.prediction_id)

    if prediction is None or prediction.user_id != current_user.id:
        # Same response for "not found" and "not yours" — don't leak existence.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found.",
        )

    if not prediction.is_resolved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Prediction has not resolved yet.",
        )

    # Idempotency: if already evaluated, return the stored result.
    existing = await brier.get_evaluation(db, payload.prediction_id)
    if existing is not None:
        return EvaluateResponse(
            prediction_id=payload.prediction_id,
            brier_delta=existing.brier_delta,
            new_calibration_score=existing.calibration_score,
            family_changed=False,
            badges_awarded=[],
        )

    # 1. Brier calculation for this prediction
    brier_result = await brier.evaluate_prediction(db, prediction)

    # 2. Roll into the user's score state + family
    family_result = await score_family_updater.apply_resolution(
        db, current_user.id, brier_result
    )

    # 3. Badge evaluation against the new state
    awarded = await badge_evaluator.evaluate_user(db, current_user.id)

    await db.commit()

    return EvaluateResponse(
        prediction_id=payload.prediction_id,
        brier_delta=brier_result.delta,
        new_calibration_score=family_result.calibration_score,
        family_changed=family_result.family_changed,
        new_family=family_result.new_family if family_result.family_changed else None,
        badges_awarded=[b.badge_id for b in awarded],
    )

"""
Gamification API routes — Calibration Score, history, badges, evaluation.

Exposes the gamification engine (brier.py, score_family_updater.py,
badge_evaluator.py) to the frontend. Prefix is assigned in main.py:

    app.include_router(gamification_router, prefix="/api/gamification")
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..db.models import User
from .user_ids import user_id_to_uuid
from ..db.models.gamification import (
    BadgeSlug,
    Decision,
    DecisionStatus,
    UserBadge,
    UserGamificationProfile,
    UserScoreSnapshot,
)
from ..services.gamification.badge_evaluator import PointsBadgeEvaluator
from ..services.gamification.brier import BrierScoreCalculator
from ..services.gamification.score_family_updater import ScoreFamilyUpdater
from .schemas import (
    BadgesResponse,
    CalibrationScoreResponse,
    EarnedBadge,
    EvaluateRequest,
    EvaluateResponse,
    FamilyTransition,
    InProgressBadge,
    ScoreHistoryPoint,
    ScoreHistoryResponse,
    TrendDirection,
)

router = APIRouter(tags=["gamification"])

# Minimum resolved predictions before a calibration score is displayed.
# Below this, the score is too volatile to be trustworthy — and trust is the brand.
MIN_SAMPLE_SIZE = 5

BADGE_CATALOG: dict[BadgeSlug, tuple[str, str]] = {
    BadgeSlug.FIRST_CALL: (
        "First Call",
        "Log your first decision.",
    ),
    BadgeSlug.WHAT_WOULD_CHANGE: (
        "What Would Change",
        "Add falsification criteria on 5 decisions.",
    ),
    BadgeSlug.PROCESS_BUILDER: (
        "Process Builder",
        "Log 10 decisions with both reasoning and falsification.",
    ),
    BadgeSlug.SEVEN_DAY_STREAK: (
        "Seven Day Streak",
        "Log decisions on 7 consecutive days.",
    ),
    BadgeSlug.THIRTY_DAY_STREAK: (
        "Thirty Day Streak",
        "Log decisions on 30 consecutive days.",
    ),
    BadgeSlug.CALIBRATED_RUN: (
        "Calibrated Run",
        "Land 5 consecutive outcomes within ±15pp.",
    ),
    BadgeSlug.STAYED_CALIBRATED_DRAWDOWN: (
        "Stayed Calibrated",
        "Hold calibration through a drawdown.",
    ),
    BadgeSlug.GOOD_LOSER: (
        "Good Loser",
        "Review a wrong call and credit a sound process.",
    ),
    BadgeSlug.HUMBLE_WINNER: (
        "Humble Winner",
        "Review a correct call and admit a shaky process.",
    ),
    BadgeSlug.AVOIDED_REVENGE: (
        "Avoided Revenge",
        "Skip revenge sizing after a loss.",
    ),
    BadgeSlug.REVISED_THESIS: (
        "Revised Thesis",
        "Revise your thesis after a review.",
    ),
    BadgeSlug.BIAS_CORRECTED: (
        "Bias Corrected",
        "Close an insight loop by reducing a known bias.",
    ),
    BadgeSlug.LOOP_CLOSED: (
        "Loop Closed",
        "Complete an insight loop end-to-end.",
    ),
    BadgeSlug.SKILL_TRANSFERRED: (
        "Skill Transferred",
        "Apply a bias lesson in a new domain.",
    ),
    BadgeSlug.STABLE_UNDER_PRESSURE: (
        "Stable Under Pressure",
        "Stay calibrated across a volatile stretch.",
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PERIODS: dict[str, Optional[timedelta]] = {
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
    "all": None,
}


def _user_uuid(user: User) -> UUID:
    return user_id_to_uuid(user.id)


def _resolve_period(period: str) -> Optional[datetime]:
    """Translate a period string into a cutoff datetime (None = all time)."""
    if period not in _PERIODS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid period '{period}'. Valid: {', '.join(_PERIODS)}",
        )
    delta = _PERIODS[period]
    return datetime.now(timezone.utc) - delta if delta else None


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


def _resolved_decisions(db: Session, user_id: UUID) -> list[Decision]:
    return (
        db.query(Decision)
        .filter(
            Decision.user_id == user_id,
            Decision.status == DecisionStatus.RESOLVED,
            Decision.confidence.isnot(None),
            Decision.outcome_binary.isnot(None),
        )
        .order_by(Decision.resolved_at.asc(), Decision.created_at.asc())
        .all()
    )


def _rolling_from_decisions(decisions: list[Decision]):
    if not decisions:
        return None
    pairs = [(d.confidence, bool(d.outcome_binary)) for d in decisions]
    return BrierScoreCalculator.calculate_rolling(pairs)


def _trend_from_snapshots(
    db: Session, user_id: UUID
) -> Optional[TrendDirection]:
    snapshots = (
        db.query(UserScoreSnapshot)
        .filter(
            UserScoreSnapshot.user_id == user_id,
            UserScoreSnapshot.calibration_score.isnot(None),
        )
        .order_by(UserScoreSnapshot.snapshot_at.desc())
        .limit(10)
        .all()
    )
    if len(snapshots) < 2:
        return TrendDirection.stable

    latest = snapshots[0].calibration_score or 0.0
    earliest = snapshots[-1].calibration_score or 0.0
    delta = latest - earliest
    if delta > 2.0:
        return TrendDirection.improving
    if delta < -2.0:
        return TrendDirection.declining
    return TrendDirection.stable


def _brier_from_calibration(calibration_score: Optional[float]) -> Optional[float]:
    """Inverse of ADR-001: score = 100 * (1 - 2 * brier)."""
    if calibration_score is None:
        return None
    return round((1.0 - (calibration_score / 100.0)) / 2.0, 6)


def _family_transitions(
    snapshots: list[UserScoreSnapshot],
) -> list[FamilyTransition]:
    transitions: list[FamilyTransition] = []
    if not snapshots:
        return transitions

    previous = snapshots[0]
    for snap in snapshots[1:]:
        prev_tier = previous.tier.value if previous.tier else "instinctive"
        next_tier = snap.tier.value if snap.tier else "instinctive"
        if prev_tier != next_tier:
            transitions.append(
                FamilyTransition(
                    date=snap.snapshot_at,
                    **{"from": prev_tier, "to": next_tier},
                )
            )
        previous = snap
    return transitions


def _badge_progress(
    db: Session,
    user_id: UUID,
    profile: UserGamificationProfile,
    earned_slugs: set[BadgeSlug],
) -> list[InProgressBadge]:
    falsification_count = (
        db.query(Decision)
        .filter(
            Decision.user_id == user_id,
            Decision.falsification.isnot(None),
        )
        .count()
    )
    full_process_count = (
        db.query(Decision)
        .filter(
            Decision.user_id == user_id,
            Decision.reasoning.isnot(None),
            Decision.falsification.isnot(None),
        )
        .count()
    )

    progress_map: dict[BadgeSlug, float] = {
        BadgeSlug.FIRST_CALL: min(profile.total_calls / 1.0, 1.0),
        BadgeSlug.WHAT_WOULD_CHANGE: min(falsification_count / 5.0, 1.0),
        BadgeSlug.PROCESS_BUILDER: min(full_process_count / 10.0, 1.0),
        BadgeSlug.SEVEN_DAY_STREAK: min(profile.logging_streak_days / 7.0, 1.0),
        BadgeSlug.THIRTY_DAY_STREAK: min(profile.logging_streak_days / 30.0, 1.0),
        BadgeSlug.CALIBRATED_RUN: min(profile.calibration_streak / 5.0, 1.0),
        BadgeSlug.GOOD_LOSER: 0.0,
        BadgeSlug.HUMBLE_WINNER: 0.0,
        BadgeSlug.AVOIDED_REVENGE: 0.0,
        BadgeSlug.REVISED_THESIS: 0.0,
        BadgeSlug.BIAS_CORRECTED: 0.0,
        BadgeSlug.LOOP_CLOSED: 0.0,
        BadgeSlug.SKILL_TRANSFERRED: 0.0,
        BadgeSlug.STAYED_CALIBRATED_DRAWDOWN: 0.0,
        BadgeSlug.STABLE_UNDER_PRESSURE: (
            1.0 if profile.stable_under_pressure else 0.0
        ),
    }

    in_progress: list[InProgressBadge] = []
    for slug, progress in progress_map.items():
        if slug in earned_slugs:
            continue
        if progress <= 0.0:
            continue
        name, criteria = BADGE_CATALOG[slug]
        in_progress.append(
            InProgressBadge(
                badge_id=slug.value,
                name=name,
                progress=round(min(progress, 0.99), 2),
                criteria_summary=criteria,
            )
        )
    return in_progress


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/calibration-score", response_model=CalibrationScoreResponse)
def get_calibration_score(
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
    user_id = _user_uuid(current_user)
    profile = (
        db.query(UserGamificationProfile)
        .filter(UserGamificationProfile.user_id == user_id)
        .first()
    )
    resolved = _resolved_decisions(db, user_id)
    resolved_count = (
        profile.resolved_calls if profile is not None else len(resolved)
    )

    if resolved_count == 0 and not resolved:
        return CalibrationScoreResponse(
            user_id=user_id,
            resolved_predictions=0,
            minimum_sample_met=False,
        )

    if profile is not None:
        resolved_count = max(profile.resolved_calls, len(resolved))

    sample_met = resolved_count >= MIN_SAMPLE_SIZE
    rolling = _rolling_from_decisions(resolved) if sample_met else None

    calibration_score = None
    brier_score = None
    score_family = None
    trend = None

    if sample_met:
        if profile is not None and profile.calibration_score is not None:
            calibration_score = profile.calibration_score
            brier_score = (
                rolling.average_brier
                if rolling is not None
                else _brier_from_calibration(calibration_score)
            )
            score_family = profile.tier.value if profile.tier else None
        elif rolling is not None:
            calibration_score = rolling.calibration_score
            brier_score = rolling.average_brier
            score_family = profile.tier.value if profile and profile.tier else "instinctive"
        trend = _trend_from_snapshots(db, user_id)

    return CalibrationScoreResponse(
        user_id=user_id,
        calibration_score=calibration_score,
        brier_score=brier_score,
        score_family=score_family,
        trend=trend,
        resolved_predictions=resolved_count,
        minimum_sample_met=sample_met,
        last_updated=profile.updated_at if profile else None,
    )


@router.get("/score-history", response_model=ScoreHistoryResponse)
def get_score_history(
    period: str = Query("30d", description="7d | 30d | 90d | all"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScoreHistoryResponse:
    """
    Time series of calibration/Brier scores plus score-family transitions.

    Feeds the trend chart. Family transitions are returned inline so the
    frontend can annotate level-ups without a second call.
    """
    user_id = _user_uuid(current_user)
    cutoff = _resolve_period(period)

    query = db.query(UserScoreSnapshot).filter(
        UserScoreSnapshot.user_id == user_id
    )
    if cutoff is not None:
        query = query.filter(UserScoreSnapshot.snapshot_at >= cutoff)

    snapshots = query.order_by(UserScoreSnapshot.snapshot_at.asc()).all()

    points = [
        ScoreHistoryPoint(
            date=snap.snapshot_at,
            calibration_score=snap.calibration_score,
            brier_score=(
                snap.rolling_brier
                if snap.rolling_brier is not None
                else _brier_from_calibration(snap.calibration_score)
            ),
            predictions_resolved=snap.resolved_calls,
        )
        for snap in snapshots
    ]

    return ScoreHistoryResponse(
        user_id=user_id,
        period=period,
        points=points,
        score_family_transitions=_family_transitions(snapshots),
    )


@router.get("/badges", response_model=BadgesResponse)
def get_badges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BadgesResponse:
    """
    Earned and in-progress badges for the authenticated user.

    `in_progress` includes a 0–1 progress fraction — the retention lever.
    Earned badges are trophies; almost-earned badges are tomorrow's login.
    """
    user_id = _user_uuid(current_user)
    profile = (
        db.query(UserGamificationProfile)
        .filter(UserGamificationProfile.user_id == user_id)
        .first()
    )

    badges = (
        db.query(UserBadge)
        .filter(UserBadge.user_id == user_id)
        .order_by(UserBadge.earned_at.asc())
        .all()
    )
    earned_slugs = {b.badge_slug for b in badges}

    earned = []
    for badge in badges:
        name, criteria = BADGE_CATALOG.get(
            badge.badge_slug,
            (badge.badge_slug.value, badge.badge_slug.value),
        )
        earned.append(
            EarnedBadge(
                badge_id=badge.badge_slug.value,
                name=name,
                earned_at=badge.earned_at,
                criteria_summary=criteria,
            )
        )

    in_progress: list[InProgressBadge] = []
    if profile is not None:
        in_progress = _badge_progress(db, user_id, profile, earned_slugs)

    return BadgesResponse(
        earned=earned,
        in_progress=in_progress,
    )


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate_prediction(
    payload: EvaluateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EvaluateResponse:
    """
    Run the full evaluation pipeline for a newly resolved decision:
    Brier calculation → score family update → badge evaluation.

    `prediction_id` maps to `Decision.id` in the gamification domain.

    Score-integrity guarantees:
      * The decision must belong to the authenticated user.
      * The decision must be resolved (outcome known).
      * Evaluation is idempotent — re-posting an already-evaluated
        decision returns the stored result without recomputation.

    NOTE: If decision resolution is system-driven, prefer calling the
    service layer directly from that job and restricting this route to
    an internal/admin scope. Users should never be able to force re-scoring.
    """
    user_id = _user_uuid(current_user)
    decision = db.query(Decision).filter(Decision.id == payload.prediction_id).first()

    if decision is None or str(decision.user_id) != str(user_id):
        # Same response for "not found" and "not yours" — don't leak existence.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found.",
        )

    if decision.status != DecisionStatus.RESOLVED or decision.outcome_binary is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Prediction has not resolved yet.",
        )

    profile = _get_or_create_profile(db, user_id)

    # Idempotency: if already evaluated, return the stored result.
    if decision.brier_score is not None:
        return EvaluateResponse(
            prediction_id=payload.prediction_id,
            brier_delta=None,
            new_calibration_score=profile.calibration_score,
            family_changed=False,
            badges_awarded=[],
        )

    prior_resolved = [
        d
        for d in _resolved_decisions(db, user_id)
        if d.id != decision.id and d.brier_score is not None
    ]
    prior_avg = None
    if prior_resolved:
        prior_avg = BrierScoreCalculator.calculate_average_brier(
            [d.brier_score for d in prior_resolved]
        )

    # 1. Brier calculation for this decision
    brier_result = BrierScoreCalculator.calculate(
        decision.confidence, bool(decision.outcome_binary)
    )
    decision.brier_score = brier_result.brier_score
    decision.calibration_delta = brier_result.calibration_gap_pct
    if decision.resolved_at is None:
        decision.resolved_at = datetime.utcnow()

    # 2. Roll into the user's score state + family
    family_result = ScoreFamilyUpdater(db).update_after_resolution(decision, profile)

    # 3. Badge evaluation against the new state
    badge_result = PointsBadgeEvaluator(db).on_decision_resolved(
        decision,
        brier_result.is_calibrated,
        profile,
        family_result,
    )

    db.commit()

    new_avg = BrierScoreCalculator.calculate_average_brier(
        [*(d.brier_score for d in prior_resolved), brier_result.brier_score]
    )
    brier_delta = None if prior_avg is None else round(new_avg - prior_avg, 6)

    return EvaluateResponse(
        prediction_id=payload.prediction_id,
        brier_delta=brier_delta,
        new_calibration_score=family_result.calibration_score,
        family_changed=family_result.tier_advanced,
        new_family=(
            family_result.new_tier.value if family_result.tier_advanced else None
        ),
        badges_awarded=[slug.value for slug in badge_result.badges_earned],
    )

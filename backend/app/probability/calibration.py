"""
Calibration Score Computation

Transforms raw Brier scores into a user-facing 0-100 Calibration Score
with recency weighting, sub-scores by category, and percentile ranking.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..db.models import UserPrediction, PredictionMarket, CalibrationScoreHistory, User


def compute_calibration_score(
    db: Session,
    user_id: str,
) -> dict:
    """
    Compute the full calibration response for a user.

    Returns:
        {
            "overall_score": int | None,
            "prediction_count": int,
            "resolved_count": int,
            "percentile": int | None,
            "sub_scores": [{"category": str, "score": int, "prediction_count": int}],
            "trend_30d": [{"date": str, "score": int}],
        }
    """
    now = datetime.now(UTC)
    window_start = now - timedelta(days=90)

    # Fetch all resolved predictions in the 90-day window
    resolved = (
        db.query(UserPrediction, PredictionMarket)
        .join(PredictionMarket, UserPrediction.market_id == PredictionMarket.id)
        .filter(
            UserPrediction.user_id == user_id,
            UserPrediction.brier_score.isnot(None),
            PredictionMarket.is_resolved == True,
            UserPrediction.created_at >= window_start,
        )
        .all()
    )

    # Total predictions (all time)
    prediction_count = db.query(func.count(UserPrediction.id)).filter(
        UserPrediction.user_id == user_id
    ).scalar() or 0

    resolved_count = len(resolved)

    # Need 5+ resolved predictions to compute a score
    if resolved_count < 5:
        return {
            "overall_score": None,
            "prediction_count": prediction_count,
            "resolved_count": resolved_count,
            "percentile": None,
            "sub_scores": [],
            "trend_30d": _get_trend(db, user_id),
        }

    # Compute weighted mean Brier score
    overall_score = _compute_weighted_score(resolved, now)

    # Sub-scores by category
    sub_scores = _compute_sub_scores(resolved, now)

    # Percentile
    percentile = _compute_percentile(db, user_id, overall_score, now)

    # Save daily snapshot (idempotent — one per day)
    _save_snapshot(db, user_id, overall_score, now)

    return {
        "overall_score": overall_score,
        "prediction_count": prediction_count,
        "resolved_count": resolved_count,
        "percentile": percentile,
        "sub_scores": sub_scores,
        "trend_30d": _get_trend(db, user_id),
    }


def _recency_weight(created_at: datetime, now: datetime) -> float:
    """Weight: 1.0 for last 30d, 0.7 for 30-60d, 0.4 for 60-90d."""
    days_ago = (now - created_at).days
    if days_ago <= 30:
        return 1.0
    elif days_ago <= 60:
        return 0.7
    else:
        return 0.4


def _brier_to_score(weighted_mean_brier: float) -> int:
    """Transform weighted mean Brier to 0-100 scale.
    Perfect calibration (0.0) → 100, maximally bad (0.25) → 0.
    """
    score = 100 * (1 - 4 * weighted_mean_brier)
    return max(0, min(100, round(score)))


def _compute_weighted_score(
    resolved: list[tuple[UserPrediction, PredictionMarket]],
    now: datetime,
) -> int:
    """Compute the overall weighted calibration score."""
    total_weight = 0.0
    weighted_brier_sum = 0.0

    for pred, _ in resolved:
        w = _recency_weight(pred.created_at, now)
        weighted_brier_sum += w * pred.brier_score
        total_weight += w

    if total_weight == 0:
        return 0

    weighted_mean_brier = weighted_brier_sum / total_weight
    return _brier_to_score(weighted_mean_brier)


def _compute_sub_scores(
    resolved: list[tuple[UserPrediction, PredictionMarket]],
    now: datetime,
) -> list[dict]:
    """Compute sub-scores for each category with 3+ predictions."""
    by_category: dict[str, list[tuple[UserPrediction, PredictionMarket]]] = {}

    for pred, market in resolved:
        cat = market.category
        by_category.setdefault(cat, []).append((pred, market))

    sub_scores = []
    for category, preds in sorted(by_category.items()):
        if len(preds) < 3:
            continue

        total_weight = 0.0
        weighted_brier_sum = 0.0
        for pred, _ in preds:
            w = _recency_weight(pred.created_at, now)
            weighted_brier_sum += w * pred.brier_score
            total_weight += w

        if total_weight > 0:
            weighted_mean = weighted_brier_sum / total_weight
            score = _brier_to_score(weighted_mean)
            sub_scores.append({
                "category": category,
                "score": score,
                "prediction_count": len(preds),
            })

    return sub_scores


def _compute_percentile(
    db: Session,
    user_id: str,
    user_score: int,
    now: datetime,
) -> Optional[int]:
    """
    Compute percentile against all users with 5+ resolved predictions
    in the last 30 days. Suppress if fewer than 10 qualifying users.
    """
    window_30d = now - timedelta(days=30)

    # Find all users with 5+ resolved predictions in last 30 days
    qualifying_users = (
        db.query(UserPrediction.user_id)
        .join(PredictionMarket, UserPrediction.market_id == PredictionMarket.id)
        .filter(
            UserPrediction.brier_score.isnot(None),
            PredictionMarket.is_resolved == True,
            UserPrediction.created_at >= window_30d,
        )
        .group_by(UserPrediction.user_id)
        .having(func.count(UserPrediction.id) >= 5)
        .all()
    )

    if len(qualifying_users) < 10:
        return None  # Suppress — insufficient population

    # Compute scores for all qualifying users
    scores = []
    for (uid,) in qualifying_users:
        if uid == user_id:
            scores.append(user_score)
            continue

        preds = (
            db.query(UserPrediction, PredictionMarket)
            .join(PredictionMarket, UserPrediction.market_id == PredictionMarket.id)
            .filter(
                UserPrediction.user_id == uid,
                UserPrediction.brier_score.isnot(None),
                PredictionMarket.is_resolved == True,
                UserPrediction.created_at >= window_30d,
            )
            .all()
        )
        if preds:
            s = _compute_weighted_score(preds, now)
            scores.append(s)

    if not scores:
        return None

    # Percentile: what fraction of users does this user beat?
    below = sum(1 for s in scores if s < user_score)
    return round(below / len(scores) * 100)


def _save_snapshot(db: Session, user_id: str, score: int, now: datetime):
    """Save a daily snapshot. Idempotent — skips if today already saved."""
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    existing = (
        db.query(CalibrationScoreHistory)
        .filter(
            CalibrationScoreHistory.user_id == user_id,
            CalibrationScoreHistory.computed_at >= today_start,
            CalibrationScoreHistory.computed_at < today_end,
        )
        .first()
    )

    if existing:
        existing.score = score
    else:
        db.add(CalibrationScoreHistory(user_id=user_id, score=score))

    db.commit()


def _get_trend(db: Session, user_id: str) -> list[dict]:
    """Get last 30 days of score snapshots for sparkline."""
    cutoff = datetime.now(UTC) - timedelta(days=30)

    snapshots = (
        db.query(CalibrationScoreHistory)
        .filter(
            CalibrationScoreHistory.user_id == user_id,
            CalibrationScoreHistory.computed_at >= cutoff,
        )
        .order_by(CalibrationScoreHistory.computed_at)
        .all()
    )

    return [
        {"date": s.computed_at.strftime("%Y-%m-%d"), "score": s.score}
        for s in snapshots
    ]

"""
Calibration Score Computation

Transforms raw Brier scores into a user-facing 0-100 Calibration Score
with recency weighting, sub-scores by category, and percentile ranking.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..db.models import User, UserPrediction, PredictionMarket, CalibrationScoreHistory


MIN_RESOLVED_PREDICTIONS = 5


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
    pending_count = db.query(func.count(UserPrediction.id)).filter(
        UserPrediction.user_id == user_id,
        UserPrediction.brier_score.is_(None),
    ).scalar() or 0
    trend = _get_trend(db, user_id)
    recent_reviews = _build_recent_reviews(resolved)

    # Need 5+ resolved predictions to compute a score
    if resolved_count < MIN_RESOLVED_PREDICTIONS:
        insights = _build_engine_insights(
            resolved=resolved,
            overall_score=None,
            sub_scores=[],
            trend=trend,
            pending_count=pending_count,
        )
        return {
            "overall_score": None,
            "prediction_count": prediction_count,
            "resolved_count": resolved_count,
            "percentile": None,
            "sub_scores": [],
            "trend_30d": trend,
            "is_first_score_view": False,
            "engine_state": "building",
            "next_action": _build_next_action(
                overall_score=None,
                resolved_count=resolved_count,
                pending_count=pending_count,
                insights=insights,
            ),
            "engine_insights": insights,
            "recent_reviews": recent_reviews,
        }

    # Compute weighted mean Brier score
    overall_score = _compute_weighted_score(resolved, now)

    # Sub-scores by category
    sub_scores = _compute_sub_scores(resolved, now)

    # Percentile
    percentile = _compute_percentile(db, user_id, overall_score, now)

    # Save daily snapshot (idempotent — one per day)
    _save_snapshot(db, user_id, overall_score, now)

    # Check if this is the first time the user sees a computed score
    user = db.query(User).filter(User.id == user_id).first()
    is_first = False
    if user and not user.has_seen_first_score:
        is_first = True

    trend = _get_trend(db, user_id)
    insights = _build_engine_insights(
        resolved=resolved,
        overall_score=overall_score,
        sub_scores=sub_scores,
        trend=trend,
        pending_count=pending_count,
    )

    return {
        "overall_score": overall_score,
        "prediction_count": prediction_count,
        "resolved_count": resolved_count,
        "percentile": percentile,
        "sub_scores": sub_scores,
        "trend_30d": trend,
        "is_first_score_view": is_first,
        "engine_state": "active",
        "next_action": _build_next_action(
            overall_score=overall_score,
            resolved_count=resolved_count,
            pending_count=pending_count,
            insights=insights,
        ),
        "engine_insights": insights,
        "recent_reviews": recent_reviews,
    }


def _recency_weight(created_at: datetime, now: datetime) -> float:
    """Weight: 1.0 for last 30d, 0.7 for 30-60d, 0.4 for 60-90d."""
    # Handle mixed tz-aware/naive datetimes (SQLite stores naive)
    if created_at.tzinfo is None and now.tzinfo is not None:
        created_at = created_at.replace(tzinfo=UTC)
    elif created_at.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    days_ago = (now - created_at).days
    if days_ago <= 30:
        return 1.0
    elif days_ago <= 60:
        return 0.7
    else:
        return 0.4


def _brier_to_score(weighted_mean_brier: float) -> int:
    """Transform weighted mean Brier to 0-100 scale.
    Perfect calibration (0.0) → 100, coin-flip (0.25) → 50, worst (0.5) → 0.
    """
    score = 100 * (1 - 2 * weighted_mean_brier)
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


def _build_recent_reviews(
    resolved: list[tuple[UserPrediction, PredictionMarket]],
    limit: int = 3,
) -> list[dict]:
    """Turn recent resolved predictions into decision-review cards."""
    recent = sorted(resolved, key=lambda item: item[0].created_at, reverse=True)[:limit]
    return [_build_decision_review(pred, market) for pred, market in recent]


def _build_decision_review(
    pred: UserPrediction,
    market: PredictionMarket,
) -> dict:
    """Explain how one resolved decision affected the calibration loop."""
    brier = pred.brier_score or 0.0
    decision_score = _brier_to_score(brier)
    probability = pred.predicted_probability
    outcome = market.resolution or "unknown"
    actual = 1 if outcome == "yes" else 0
    was_directionally_right = (
        (probability >= 0.5 and actual == 1) or
        (probability < 0.5 and actual == 0)
    )

    if decision_score >= 85:
        verdict = "Sharp read"
    elif decision_score >= 65:
        verdict = "Mostly calibrated"
    elif decision_score >= 40:
        verdict = "Mixed signal"
    else:
        verdict = "Judgment breakdown"

    if decision_score >= 85:
        diagnosis = "Your confidence matched the outcome closely. Capture what evidence mattered."
    elif 0.4 <= probability <= 0.6:
        diagnosis = "Your estimate stayed near 50/50. Review what evidence would have moved you."
    elif probability >= 0.75 and actual == 0:
        diagnosis = "Overconfidence: you assigned high odds to an event that did not happen."
    elif probability <= 0.25 and actual == 1:
        diagnosis = "Underreaction: you assigned low odds to an event that happened."
    elif not was_directionally_right:
        diagnosis = "Direction miss: your lean pointed the wrong way, so revisit the base rate."
    else:
        diagnosis = "Directionally right, but the confidence level can be tightened next time."

    return {
        "market_title": market.title,
        "category": market.category,
        "predicted_probability": probability,
        "outcome": outcome,
        "brier_score": brier,
        "decision_score": decision_score,
        "verdict": verdict,
        "diagnosis": diagnosis,
        "created_at": pred.created_at.isoformat(),
    }


def _build_engine_insights(
    resolved: list[tuple[UserPrediction, PredictionMarket]],
    overall_score: Optional[int],
    sub_scores: list[dict],
    trend: list[dict],
    pending_count: int,
) -> list[dict]:
    """Create concise coaching insights from the user's calibration evidence."""
    insights: list[dict] = []
    resolved_count = len(resolved)

    if resolved_count < MIN_RESOLVED_PREDICTIONS:
        remaining = MIN_RESOLVED_PREDICTIONS - resolved_count
        insights.append({
            "type": "progress",
            "title": "Feedback loop is warming up",
            "description": (
                f"{remaining} more resolved prediction"
                f"{'s' if remaining != 1 else ''} unlock the full Calibration Score."
            ),
            "severity": "info",
        })
        if pending_count > 0:
            insights.append({
                "type": "resolution",
                "title": "Outcomes are still pending",
                "description": (
                    f"{pending_count} prediction"
                    f"{'s are' if pending_count != 1 else ' is'} waiting for market resolution."
                ),
                "severity": "info",
            })
        return insights

    reviews = [_build_decision_review(pred, market) for pred, market in resolved]
    breakdowns = [review for review in reviews if review["decision_score"] < 40]
    if breakdowns:
        worst = min(breakdowns, key=lambda review: review["decision_score"])
        insights.append({
            "type": "breakdown",
            "title": "Biggest judgment breakdown",
            "description": worst["diagnosis"],
            "severity": "warning",
        })

    if sub_scores:
        weakest = min(sub_scores, key=lambda score: score["score"])
        insights.append({
            "type": "category",
            "title": f"Lowest sub-score: {weakest['category']}",
            "description": (
                f"{weakest['prediction_count']} resolved predictions in this category "
                f"score {weakest['score']}. Review the assumptions you repeat there."
            ),
            "severity": "warning" if weakest["score"] < 50 else "info",
        })

    confident = [
        (pred, market) for pred, market in resolved
        if pred.predicted_probability >= 0.75 or pred.predicted_probability <= 0.25
    ]
    if len(confident) >= 3:
        misses = 0
        for pred, market in confident:
            actual = 1 if market.resolution == "yes" else 0
            directionally_right = (
                (pred.predicted_probability >= 0.5 and actual == 1) or
                (pred.predicted_probability < 0.5 and actual == 0)
            )
            if not directionally_right:
                misses += 1
        miss_rate = misses / len(confident)
        if miss_rate >= 0.4:
            insights.append({
                "type": "confidence",
                "title": "Check high-conviction calls",
                "description": (
                    f"{round(miss_rate * 100)}% of your high-conviction resolved calls "
                    "missed directionally. Pressure-test the evidence before going extreme."
                ),
                "severity": "warning",
            })

    middle = [
        pred for pred, _ in resolved
        if 0.4 <= pred.predicted_probability <= 0.6
    ]
    if len(middle) / resolved_count >= 0.6:
        insights.append({
            "type": "confidence",
            "title": "Too many 50/50 estimates",
            "description": "Your recent calls cluster near neutral. Name the evidence that would move you to 60% or 40%.",
            "severity": "info",
        })

    if len(trend) >= 2:
        delta = trend[-1]["score"] - trend[0]["score"]
        if abs(delta) >= 5:
            direction = "improved" if delta > 0 else "slipped"
            insights.append({
                "type": "trend",
                "title": f"30-day score {direction}",
                "description": f"Your Calibration Score moved {delta:+d} points across the latest snapshots.",
                "severity": "positive" if delta > 0 else "warning",
            })

    if not insights:
        label = "strong" if (overall_score or 0) >= 70 else "steady"
        insights.append({
            "type": "practice",
            "title": f"{label.title()} calibration base",
            "description": "Keep writing a short reason before each prediction so the next score change has a clear cause.",
            "severity": "positive" if label == "strong" else "info",
        })

    return insights[:3]


def _build_next_action(
    overall_score: Optional[int],
    resolved_count: int,
    pending_count: int,
    insights: list[dict],
) -> dict:
    """Recommend the next step in the decide-score-diagnose-improve loop."""
    if resolved_count < MIN_RESOLVED_PREDICTIONS:
        remaining = MIN_RESOLVED_PREDICTIONS - resolved_count
        return {
            "title": "Make the loop measurable",
            "description": (
                f"Get {remaining} more prediction"
                f"{'s' if remaining != 1 else ''} resolved to unlock diagnosis and score history."
            ),
            "cta": "Predict a market",
            "href": "/probability-lab",
        }

    warning = next((insight for insight in insights if insight["severity"] == "warning"), None)
    if warning:
        return {
            "title": "Review the weakest pattern",
            "description": warning["description"],
            "cta": "Inspect decisions",
            "href": "/probability-lab",
        }

    if pending_count == 0:
        return {
            "title": "Feed the engine",
            "description": "Make another prediction so your next resolved outcome can update the score.",
            "cta": "Predict a market",
            "href": "/probability-lab",
        }

    return {
        "title": "Write the reason before the number",
        "description": (
            "Your score is active. For the next call, capture the base rate and the evidence "
            "that would change your mind."
        ),
        "cta": "Make next prediction",
        "href": "/probability-lab",
    }


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

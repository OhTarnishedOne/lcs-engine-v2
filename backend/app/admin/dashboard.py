"""
Admin Dashboard API

Authenticated admin endpoints for user management, analytics, and moderation.
All endpoints require is_admin=True.
"""

import logging
from datetime import datetime, timedelta, UTC

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, case, extract
from sqlalchemy.orm import Session

from ..deps import get_db, get_admin_user
from ..db.models import (
    User, UserProfile, Conversation, Message, Strategy,
    TradeLog, UserPrediction, PredictionMarket, CalibrationScore,
)
from ..db.models.analytics import AnalyticsEvent
from ..auth.utils import hash_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])


# ---------------------------------------------------------------------------
# Overview stats
# ---------------------------------------------------------------------------

@router.get("/overview")
def get_overview(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> dict:
    """High-level platform metrics."""
    now = datetime.now(UTC)
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    total_users = db.query(func.count(User.id)).filter(User.is_guest == False).scalar() or 0
    total_guests = db.query(func.count(User.id)).filter(User.is_guest == True).scalar() or 0
    pro_users = db.query(func.count(User.id)).filter(User.tier == "pro", User.is_guest == False).scalar() or 0

    # Onboarding
    total_onboarded = db.query(func.count(UserProfile.id)).filter(UserProfile.onboarding_completed == True).scalar() or 0
    total_started = db.query(func.count(UserProfile.id)).scalar() or 0
    onboarding_rate = round((total_onboarded / total_started * 100), 1) if total_started > 0 else 0

    # Activity (last 30 days)
    predictions_30d = db.query(func.count(UserPrediction.id)).filter(UserPrediction.created_at >= thirty_days_ago).scalar() or 0
    messages_30d = db.query(func.count(Message.id)).filter(Message.created_at >= thirty_days_ago).scalar() or 0
    trades_30d = db.query(func.count(TradeLog.id)).filter(TradeLog.created_at >= thirty_days_ago).scalar() or 0
    strategies_30d = db.query(func.count(Strategy.id)).filter(Strategy.created_at >= thirty_days_ago).scalar() or 0

    # Signups this week
    signups_7d = db.query(func.count(User.id)).filter(
        User.created_at >= seven_days_ago, User.is_guest == False
    ).scalar() or 0

    return {
        "total_users": total_users,
        "total_guests": total_guests,
        "pro_users": pro_users,
        "signups_7d": signups_7d,
        "onboarding_completion_rate": onboarding_rate,
        "activity_30d": {
            "predictions": predictions_30d,
            "chat_messages": messages_30d,
            "trades": trades_30d,
            "strategies": strategies_30d,
        },
    }


# ---------------------------------------------------------------------------
# Charts data
# ---------------------------------------------------------------------------

@router.get("/charts/user-growth")
def get_user_growth(
    days: int = Query(default=90, le=365),
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Daily signups over time (non-guest users)."""
    cutoff = datetime.now(UTC) - timedelta(days=days)
    users = db.query(User).filter(
        User.created_at >= cutoff, User.is_guest == False
    ).order_by(User.created_at).all()

    # Group by date
    by_date: dict[str, int] = {}
    cumulative = db.query(func.count(User.id)).filter(
        User.created_at < cutoff, User.is_guest == False
    ).scalar() or 0

    for user in users:
        day = user.created_at.strftime("%Y-%m-%d")
        by_date[day] = by_date.get(day, 0) + 1

    # Build cumulative series
    result = []
    current = cutoff
    now = datetime.now(UTC)
    while current <= now:
        day_str = current.strftime("%Y-%m-%d")
        new = by_date.get(day_str, 0)
        cumulative += new
        result.append({"date": day_str, "new": new, "total": cumulative})
        current += timedelta(days=1)

    return result


@router.get("/charts/prediction-activity")
def get_prediction_activity(
    days: int = Query(default=30, le=365),
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Daily prediction counts."""
    cutoff = datetime.now(UTC) - timedelta(days=days)
    preds = db.query(UserPrediction).filter(
        UserPrediction.created_at >= cutoff
    ).all()

    by_date: dict[str, int] = {}
    for p in preds:
        day = p.created_at.strftime("%Y-%m-%d")
        by_date[day] = by_date.get(day, 0) + 1

    result = []
    current = cutoff
    now = datetime.now(UTC)
    while current <= now:
        day_str = current.strftime("%Y-%m-%d")
        result.append({"date": day_str, "count": by_date.get(day_str, 0)})
        current += timedelta(days=1)

    return result


@router.get("/charts/feature-usage")
def get_feature_usage(
    days: int = Query(default=30, le=365),
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Event counts by feature."""
    cutoff = datetime.now(UTC) - timedelta(days=days)
    events = (
        db.query(AnalyticsEvent.event_name, func.count(AnalyticsEvent.id))
        .filter(AnalyticsEvent.created_at >= cutoff)
        .group_by(AnalyticsEvent.event_name)
        .order_by(func.count(AnalyticsEvent.id).desc())
        .all()
    )

    FEATURE_LABELS = {
        "chat_message_sent": "AI Chat",
        "prediction_submitted": "Probability Lab",
        "strategy_generated": "Strategies",
        "paper_trade_placed": "Paper Trading",
        "onboarding_completed": "Onboarding",
        "signup_completed": "Signups",
        "login_completed": "Logins",
        "session_started": "Sessions",
    }

    return [
        {"event": FEATURE_LABELS.get(name, name), "count": count}
        for name, count in events
        if name in FEATURE_LABELS
    ]


@router.get("/charts/calibration-distribution")
def get_calibration_distribution(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Distribution of Calibration Scores (non-guest, non-null)."""
    scores = (
        db.query(CalibrationScore)
        .join(User, CalibrationScore.user_id == User.id)
        .filter(
            User.is_guest == False,
            CalibrationScore.average_brier_score.isnot(None),
            CalibrationScore.resolved_predictions >= 5,
        )
        .all()
    )

    # Convert to 0-100 scores and bucket
    buckets = {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0}
    for cal in scores:
        score = max(0, min(100, round(100 * (1 - 2 * cal.average_brier_score))))
        if score < 20:
            buckets["0-20"] += 1
        elif score < 40:
            buckets["20-40"] += 1
        elif score < 60:
            buckets["40-60"] += 1
        elif score < 80:
            buckets["60-80"] += 1
        else:
            buckets["80-100"] += 1

    return [{"range": k, "count": v} for k, v in buckets.items()]


@router.get("/charts/conversion-funnel")
def get_conversion_funnel(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Signup → Onboarding → First prediction → Pro conversion funnel."""
    total_signups = db.query(func.count(User.id)).filter(User.is_guest == False).scalar() or 0
    completed_onboarding = db.query(func.count(UserProfile.id)).filter(
        UserProfile.onboarding_completed == True
    ).scalar() or 0

    users_with_predictions = (
        db.query(func.count(func.distinct(UserPrediction.user_id)))
        .join(User, UserPrediction.user_id == User.id)
        .filter(User.is_guest == False)
        .scalar() or 0
    )

    pro_users = db.query(func.count(User.id)).filter(
        User.tier == "pro", User.is_guest == False
    ).scalar() or 0

    return [
        {"stage": "Signed up", "count": total_signups},
        {"stage": "Completed onboarding", "count": completed_onboarding},
        {"stage": "Made a prediction", "count": users_with_predictions},
        {"stage": "Upgraded to Pro", "count": pro_users},
    ]


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

@router.get("/users")
def list_users(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """List all non-guest users with key metadata."""
    users = (
        db.query(User)
        .filter(User.is_guest == False)
        .order_by(User.created_at.desc())
        .all()
    )

    result = []
    for u in users:
        profile = db.query(UserProfile).filter(UserProfile.user_id == u.id).first()
        cal = db.query(CalibrationScore).filter(CalibrationScore.user_id == u.id).first()
        pred_count = db.query(func.count(UserPrediction.id)).filter(UserPrediction.user_id == u.id).scalar() or 0
        conv_count = db.query(func.count(Conversation.id)).filter(Conversation.user_id == u.id).scalar() or 0

        cal_score = None
        if cal and cal.average_brier_score is not None and cal.resolved_predictions >= 5:
            cal_score = max(0, min(100, round(100 * (1 - 2 * cal.average_brier_score))))

        result.append({
            "id": u.id,
            "email": u.email,
            "tier": u.tier,
            "is_admin": u.is_admin,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "persona": profile.persona if profile else None,
            "onboarding_complete": profile.onboarding_completed if profile else False,
            "prediction_count": pred_count,
            "conversation_count": conv_count,
            "calibration_score": cal_score,
        })

    return result


@router.patch("/users/{user_id}")
def update_user(
    user_id: str,
    data: dict,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> dict:
    """Update user fields (tier, is_admin)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if "tier" in data and data["tier"] in ("free", "pro"):
        user.tier = data["tier"]
    if "is_admin" in data and isinstance(data["is_admin"], bool):
        user.is_admin = data["is_admin"]

    db.commit()
    return {"id": user.id, "email": user.email, "tier": user.tier, "is_admin": user.is_admin}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> dict:
    """Delete a user and all their data."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_admin:
        raise HTTPException(status_code=403, detail="Cannot delete admin users")

    from ..db.models import Strategy, StrategyComparison
    db.query(Strategy).filter(Strategy.user_id == user_id).delete()
    db.query(StrategyComparison).filter(StrategyComparison.user_id == user_id).delete()
    db.delete(user)
    db.commit()

    logger.info(f"Admin deleted user {user_id}")
    return {"deleted": True, "user_id": user_id}


# ---------------------------------------------------------------------------
# Chat moderation
# ---------------------------------------------------------------------------

@router.get("/users/{user_id}/conversations")
def get_user_conversations(
    user_id: str,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """View a user's conversation list."""
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "title": c.title,
            "message_count": len(c.messages),
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in convs
    ]


@router.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(
    conversation_id: str,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """View messages in a conversation."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in conv.messages
    ]

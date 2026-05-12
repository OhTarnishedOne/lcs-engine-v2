"""
Demo / Guest Session Management

Per-visitor guest accounts with 5-day time-limited Pro access.
Each visitor gets their own isolated account with pre-seeded data.
"""

import logging
import uuid
from datetime import datetime, timedelta, UTC
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..deps import get_db
from ..db.models import User, Profile, UserProfile, Conversation, Message
from ..db.models.probability import PredictionMarket, UserPrediction, CalibrationScore
from .utils import hash_password, create_access_token, create_refresh_token
from .schemas import TokenResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

GUEST_TRIAL_DAYS = 5
GUEST_PASSWORD_PLACEHOLDER = "guest-no-login"
MAX_GUEST_SESSIONS_PER_IP = 3


@router.post("/demo")
def demo_login(
    request: Request,
    guest_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> dict:
    """
    Create or resume a guest session for the demo subdomain.

    - If guest_id is provided and valid (not expired), resume that session.
    - Otherwise, create a new guest user with 5-day Pro access.
    - Returns tokens + guest metadata for the frontend.
    """
    now = datetime.now(UTC)

    # Try to resume existing guest session
    if guest_id:
        user = db.query(User).filter(
            User.id == guest_id,
            User.is_guest == True,
        ).first()
        if user and user.guest_expires_at and user.guest_expires_at > now:
            return _build_response(user, now)
        # Expired or not found — fall through to create new

    # Rate limit: max 3 new guests per IP per 24 hours
    client_ip = request.client.host if request.client else "unknown"
    one_day_ago = now - timedelta(hours=24)
    recent_guests = (
        db.query(User)
        .filter(
            User.is_guest == True,
            User.guest_created_at > one_day_ago,
        )
        .count()
    )
    # Simple global rate limit for v1 (per-IP requires storing IP, deferred)
    if recent_guests > 50:
        raise HTTPException(status_code=429, detail="Too many demo sessions. Try again later.")

    # Create new guest user
    guest_uuid = str(uuid.uuid4())[:8]
    guest_email = f"guest-{guest_uuid}@demo.lcsengine.com"

    user = User(
        email=guest_email,
        password_hash=hash_password(GUEST_PASSWORD_PLACEHOLDER),
        tier="pro",
        is_guest=True,
        guest_created_at=now,
        guest_expires_at=now + timedelta(days=GUEST_TRIAL_DAYS),
    )
    db.add(user)
    db.flush()

    # Create profile + user profile
    profile = Profile(user_id=user.id, onboarding_complete=True)
    db.add(profile)

    user_profile = UserProfile(
        user_id=user.id,
        persona="goal_focused",
        experience_level="intermediate",
        biggest_barrier="dont_know_where_to_start",
        primary_goal="build_wealth",
        risk_tolerance="moderate",
        learning_preference="visual",
        time_horizon="3_to_5_years",
        interests=["stocks", "etfs", "retirement"],
        motivation="I want to feel confident making my own investment decisions.",
        life_context="Mid-career professional with stable income.",
        emotional_relationship="Cautiously optimistic about investing.",
        onboarding_completed=True,
        onboarding_completed_at=now,
        current_section=5,
    )
    db.add(user_profile)
    db.commit()

    # Seed data in separate transactions
    try:
        _seed_conversations(db, user.id)
        db.commit()
    except Exception as e:
        logger.warning(f"Guest conversation seeding failed: {e}")
        db.rollback()

    try:
        _seed_predictions(db, user.id)
        db.commit()
    except Exception as e:
        logger.warning(f"Guest prediction seeding failed: {e}")
        db.rollback()

    logger.info(f"Guest session created: {guest_email} (expires {user.guest_expires_at})")
    return _build_response(user, now)


def _build_response(user: User, now: datetime) -> dict:
    """Build the demo login response with tokens + guest metadata."""
    token_data = {"sub": user.id, "email": user.email}
    days_remaining = 0
    if user.guest_expires_at:
        delta = user.guest_expires_at - now
        days_remaining = max(0, delta.days + 1)  # Day 1 = first day

    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
        "guest_id": user.id,
        "guest_expires_at": user.guest_expires_at.isoformat() if user.guest_expires_at else None,
        "days_remaining": days_remaining,
    }


@router.post("/claim-guest")
def claim_guest_account(
    data: dict,
    db: Session = Depends(get_db),
) -> dict:
    """
    Convert a guest account to a real account.
    Migrates all guest data (predictions, trades, chats, calibration).

    Body: { guest_id: str, email: str, password: str }
    """
    guest_id = data.get("guest_id")
    email = data.get("email")
    password = data.get("password")

    if not guest_id or not email or not password:
        raise HTTPException(status_code=400, detail="guest_id, email, and password are required")

    if len(password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")

    # Find the guest user
    guest = db.query(User).filter(
        User.id == guest_id,
        User.is_guest == True,
    ).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest session not found")

    # Check email not already taken
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Convert the guest to a real user (in-place, preserving all data relationships)
    guest.email = email
    guest.password_hash = hash_password(password)
    guest.tier = "free"
    guest.is_guest = False
    # Keep guest_created_at and guest_expires_at for audit trail

    db.commit()

    token_data = {"sub": guest.id, "email": guest.email}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
        "message": "Account claimed successfully. Your trial activity has been saved.",
    }


async def cleanup_expired_guests(db: Session):
    """
    Delete guest accounts expired 30+ days ago that were never converted.
    Called by the background job.
    """
    cutoff = datetime.now(UTC) - timedelta(days=30)

    expired_guests = (
        db.query(User)
        .filter(
            User.is_guest == True,
            User.guest_expires_at < cutoff,
        )
        .all()
    )

    deleted = 0
    for guest in expired_guests:
        db.delete(guest)  # CASCADE handles related records
        deleted += 1

    if deleted:
        db.commit()
        logger.info(f"Cleaned up {deleted} expired guest accounts")

    return deleted


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

def _seed_conversations(db: Session, user_id: str):
    """Seed AI tutor conversation history."""
    conversations = [
        {
            "title": "What is dollar-cost averaging?",
            "messages": [
                ("user", "What is dollar-cost averaging and should I use it?"),
                ("assistant", "Dollar-cost averaging (DCA) means investing a fixed amount at regular intervals \u2014 say $500 every month \u2014 regardless of what the market is doing. When prices are low, your $500 buys more shares. When prices are high, it buys fewer.\n\nThe beauty is you don't need to time the market. Over time, your average purchase price smooths out, reducing the impact of volatility.\n\nFor someone with your moderate risk tolerance and 3-5 year horizon, DCA is a great fit. It removes the emotional decision of \"is now a good time to invest?\" \u2014 the answer is always \"yes, systematically.\""),
            ],
        },
        {
            "title": "ETFs vs individual stocks",
            "messages": [
                ("user", "Should I buy ETFs or individual stocks?"),
                ("assistant", "Great question \u2014 and it's not either/or.\n\n**ETFs** give you instant diversification. One share of SPY gives you exposure to 500 companies. Lower risk, lower maintenance.\n\n**Individual stocks** let you concentrate on companies you believe in. Higher potential returns, but also higher risk.\n\nFor your archetype, I'd suggest a core-satellite approach: 70-80% in broad ETFs (your core), 20-30% in individual stocks you've researched (your satellites)."),
            ],
        },
        {
            "title": "Understanding P/E ratios",
            "messages": [
                ("user", "How do I know if a stock is overvalued?"),
                ("assistant", "The most common starting point is the P/E ratio \u2014 Price divided by Earnings per share.\n\nIf a stock costs $100 and earns $5 per share annually, the P/E is 20. You're paying $20 for every $1 of earnings.\n\n**Rules of thumb:**\n- S&P 500 historical average: ~16-18\n- Growth stocks (tech): 25-40+\n- Value stocks (banks, utilities): 10-15\n\nAlways compare P/E within the same sector, not across different ones."),
            ],
        },
    ]

    for conv_data in conversations:
        conv = Conversation(user_id=user_id, title=conv_data["title"])
        db.add(conv)
        db.flush()
        for role, content in conv_data["messages"]:
            msg = Message(conversation_id=conv.id, role=role, content=content)
            db.add(msg)


def _seed_predictions(db: Session, user_id: str):
    """Seed probability lab predictions on existing markets."""
    markets = db.query(PredictionMarket).limit(7).all()
    if not markets:
        return

    prediction_data = [
        (0.70, 0.09),
        (0.55, 0.2025),
        (0.80, 0.04),
        (0.45, 0.3025),
        (0.60, 0.16),
    ]

    for i, market in enumerate(markets[:5]):
        if i < len(prediction_data):
            prob, brier = prediction_data[i]
            pred = UserPrediction(
                user_id=user_id,
                market_id=market.id,
                predicted_probability=prob,
                brier_score=brier if market.is_resolved else None,
            )
            db.add(pred)

    for market in markets[5:7]:
        pred = UserPrediction(
            user_id=user_id,
            market_id=market.id,
            predicted_probability=0.55,
            brier_score=None,
        )
        db.add(pred)

    resolved_preds = [d for i, d in enumerate(prediction_data) if i < len(markets) and markets[i].is_resolved]
    if resolved_preds:
        avg_brier = sum(b for _, b in resolved_preds) / len(resolved_preds)
        cal = CalibrationScore(
            user_id=user_id,
            total_predictions=min(7, len(markets)),
            resolved_predictions=len(resolved_preds),
            average_brier_score=avg_brier,
        )
        db.add(cal)

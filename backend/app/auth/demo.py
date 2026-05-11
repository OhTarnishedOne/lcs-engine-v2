"""
Demo Authentication

Provides a no-auth endpoint that returns a valid session for the demo user.
The demo user is auto-created on first call if it doesn't exist.
"""

import logging
from datetime import datetime, UTC

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db
from ..db.models import User, Profile, UserProfile, Conversation, Message
from ..db.models.probability import PredictionMarket, UserPrediction, CalibrationScore
from .utils import hash_password, create_access_token, create_refresh_token
from .schemas import TokenResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

DEMO_EMAIL = "demo@lcsengine.com"
DEMO_PASSWORD = "demo-secure-internal-only-2026"


def _get_or_create_demo_user(db: Session) -> User:
    """Get or create the demo user with full seeded data."""
    user = db.query(User).filter(User.email == DEMO_EMAIL).first()
    if user:
        return user

    # Create demo user
    user = User(
        email=DEMO_EMAIL,
        password_hash=hash_password(DEMO_PASSWORD),
        tier="pro",
    )
    db.add(user)
    db.flush()

    # Create profile
    profile = Profile(user_id=user.id, onboarding_complete=True)
    db.add(profile)

    # Create user profile (onboarding data)
    user_profile = UserProfile(
        user_id=user.id,
        persona="goal_focused",
        experience_level="intermediate",
        biggest_barrier="dont_know_where_to_start",
        primary_goal="Build long-term wealth through informed investing decisions",
        risk_tolerance="moderate",
        learning_preference="visual",
        time_horizon="3_to_5_years",
        interests=["stocks", "etfs", "retirement"],
        motivation="I want to feel confident making my own investment decisions instead of relying on others.",
        life_context="Mid-career professional with stable income and growing savings.",
        emotional_relationship="Cautiously optimistic — I know money can grow but I've seen people lose it too.",
        onboarding_completed=True,
        onboarding_completed_at=datetime.now(UTC),
        current_section=5,
    )
    db.add(user_profile)

    db.commit()

    # Seed data in separate transactions so failures don't block user creation
    try:
        _seed_conversations(db, user.id)
        db.commit()
    except Exception as e:
        logger.warning(f"Demo conversation seeding failed: {e}")
        db.rollback()

    try:
        _seed_predictions(db, user.id)
        db.commit()
    except Exception as e:
        logger.warning(f"Demo prediction seeding failed: {e}")
        db.rollback()

    logger.info(f"Demo user created: {DEMO_EMAIL}")
    return user


def _seed_conversations(db: Session, user_id: str):
    """Seed AI tutor conversation history."""
    conversations = [
        {
            "title": "What is dollar-cost averaging?",
            "messages": [
                ("user", "What is dollar-cost averaging and should I use it?"),
                ("assistant", "Dollar-cost averaging (DCA) means investing a fixed amount at regular intervals — say $500 every month — regardless of what the market is doing. When prices are low, your $500 buys more shares. When prices are high, it buys fewer.\n\nThe beauty is you don't need to time the market. Over time, your average purchase price smooths out, reducing the impact of volatility.\n\nFor someone with your moderate risk tolerance and 3-5 year horizon, DCA is a great fit. It removes the emotional decision of \"is now a good time to invest?\" — the answer is always \"yes, systematically.\""),
            ],
        },
        {
            "title": "ETFs vs individual stocks",
            "messages": [
                ("user", "Should I buy ETFs or individual stocks?"),
                ("assistant", "Great question — and it's not either/or. Here's how to think about it:\n\n**ETFs** give you instant diversification. One share of SPY gives you exposure to 500 companies. Lower risk, lower maintenance, historically solid returns (8-10% annually).\n\n**Individual stocks** let you concentrate on companies you believe in. Higher potential returns, but also higher risk — one bad earnings report can drop a stock 20% overnight.\n\nFor your archetype, I'd suggest a core-satellite approach: 70-80% in broad ETFs (your core), 20-30% in individual stocks you've researched (your satellites). This way you get stability plus the ability to express conviction."),
            ],
        },
        {
            "title": "Understanding P/E ratios",
            "messages": [
                ("user", "How do I know if a stock is overvalued?"),
                ("assistant", "The most common starting point is the P/E ratio — Price divided by Earnings per share.\n\nThink of it like this: if a stock costs $100 and earns $5 per share annually, the P/E is 20. You're paying $20 for every $1 of earnings.\n\n**Rules of thumb:**\n- S&P 500 historical average: ~16-18\n- Growth stocks (tech): 25-40+ is common\n- Value stocks (banks, utilities): 10-15\n\nA P/E of 50 isn't necessarily \"overvalued\" — it might mean the market expects explosive future growth. A P/E of 8 isn't necessarily cheap — it might mean the market expects earnings to decline.\n\nAlways compare P/E within the same sector, not across different ones."),
            ],
        },
        {
            "title": "Risk tolerance explained",
            "messages": [
                ("user", "What does my moderate risk tolerance actually mean for my portfolio?"),
                ("assistant", "Your moderate risk tolerance means you're comfortable with short-term drops of 10-15% in exchange for better long-term returns. You wouldn't panic-sell in a correction, but a 40% crash would make you lose sleep.\n\nIn practice, this often translates to:\n- **60-70% stocks** (growth engine)\n- **20-30% bonds** (stability cushion)\n- **5-10% alternatives or cash** (dry powder)\n\nWith your 3-5 year time horizon, you have enough runway to recover from a downturn but not so much that you can ignore risk entirely. The key is building a portfolio you can hold through a bad year without making emotional decisions."),
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
    # Get existing markets
    markets = db.query(PredictionMarket).limit(7).all()
    if not markets:
        return

    # Create predictions with varying accuracy
    prediction_data = [
        (0.70, 0.09),   # Good prediction
        (0.55, 0.2025), # Mediocre
        (0.80, 0.04),   # Very good
        (0.45, 0.3025), # Poor
        (0.60, 0.16),   # Decent
    ]

    for i, market in enumerate(markets[:5]):
        if i < len(prediction_data):
            prob, brier = prediction_data[i]
            # Only set brier if market is resolved
            pred = UserPrediction(
                user_id=user_id,
                market_id=market.id,
                predicted_probability=prob,
                brier_score=brier if market.is_resolved else None,
            )
            db.add(pred)

    # Add pending predictions for unresolved markets
    for market in markets[5:7]:
        pred = UserPrediction(
            user_id=user_id,
            market_id=market.id,
            predicted_probability=0.55,
            brier_score=None,
        )
        db.add(pred)

    # Update calibration score
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


@router.post("/demo", response_model=TokenResponse)
def demo_login(db: Session = Depends(get_db)) -> TokenResponse:
    """
    No-auth endpoint that returns a valid session for the demo user.
    Auto-creates the demo user with seeded data on first call.
    """
    try:
        user = _get_or_create_demo_user(db)
    except Exception as e:
        logger.error(f"Demo user creation failed: {type(e).__name__}: {e}")
        db.rollback()
        # Try to just fetch the user if creation failed (partial create)
        user = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if not user:
            raise

    token_data = {"sub": user.id, "email": user.email}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )

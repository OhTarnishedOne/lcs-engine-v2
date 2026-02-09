import uuid
from datetime import datetime, UTC
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Integer, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...database import Base


def utc_now():
    return datetime.now(UTC)


class UserProfile(Base):
    """Extended user profile from onboarding - deep personalization data."""
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # === SECTION 1: Where They Are ===
    experience_level: Mapped[Optional[str]] = mapped_column(String(20))
    # "never", "curious", "beginner", "intermediate", "advanced"
    current_situation: Mapped[Optional[str]] = mapped_column(String(20))
    # "student", "early_career", "mid_career", "career_change", "pre_retirement"
    has_investment_account: Mapped[Optional[bool]] = mapped_column(Boolean)
    has_retirement_account: Mapped[Optional[bool]] = mapped_column(Boolean)

    # === SECTION 2: What's Holding Them Back ===
    barriers: Mapped[Optional[list]] = mapped_column(JSON)
    # ["dont_know_where_to_start", "fear_of_losing_money", "not_enough_money", ...]
    biggest_barrier: Mapped[Optional[str]] = mapped_column(String(50))

    # === SECTION 3: What They Want ===
    primary_goal: Mapped[Optional[str]] = mapped_column(String(30))
    # "learn_basics", "start_investing", "grow_wealth", "retirement", "specific_goal"
    specific_goal_description: Mapped[Optional[str]] = mapped_column(Text)
    time_horizon: Mapped[Optional[str]] = mapped_column(String(20))
    # "less_than_1_year", "1_to_3_years", "3_to_5_years", "5_to_10_years", "10_plus_years"

    # === SECTION 4: Risk & Comfort ===
    risk_tolerance: Mapped[Optional[str]] = mapped_column(String(20))
    # "very_conservative", "conservative", "moderate", "aggressive", "very_aggressive"
    loss_reaction: Mapped[Optional[str]] = mapped_column(String(20))
    # "sell_immediately", "wait_and_see", "buy_more", "not_sure"
    monthly_investable: Mapped[Optional[str]] = mapped_column(String(20))
    # "nothing_yet", "under_100", "100_to_500", "500_to_1000", "over_1000", "not_sure"

    # === SECTION 5: Learning Style ===
    learning_preference: Mapped[Optional[str]] = mapped_column(String(20))
    # "read", "watch", "do", "discuss"
    time_commitment: Mapped[Optional[str]] = mapped_column(String(20))
    # "5_min_daily", "15_min_daily", "30_min_weekly", "1_hour_weekly", "flexible"
    interests: Mapped[Optional[list]] = mapped_column(JSON)
    # ["stocks", "etfs", "bonds", "crypto", "real_estate", "retirement", "all"]

    # === Derived / Computed ===
    persona: Mapped[Optional[str]] = mapped_column(String(50))
    # AI-assigned: "cautious_beginner", "eager_learner", "goal_focused", etc.
    persona_description: Mapped[Optional[str]] = mapped_column(Text)

    # === Status ===
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="user_profile")

    def __repr__(self) -> str:
        return f"<UserProfile user_id={self.user_id} persona={self.persona}>"


class OnboardingResponse(Base):
    """Individual question responses - for analytics and progressive onboarding."""
    __tablename__ = "onboarding_responses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    question_key: Mapped[str] = mapped_column(String(50), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_value: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string for arrays
    answer_display: Mapped[str] = mapped_column(Text, nullable=False)

    section: Mapped[int] = mapped_column(Integer, nullable=False)
    question_order: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    def __repr__(self) -> str:
        return f"<OnboardingResponse user_id={self.user_id} key={self.question_key}>"

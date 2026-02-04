import uuid
from datetime import datetime, UTC
from typing import Any
from sqlalchemy import String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...database import Base


def utc_now():
    return datetime.now(UTC)


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    risk_tolerance: Mapped[str | None] = mapped_column(String(20))  # conservative, moderate, aggressive
    investment_horizon: Mapped[str | None] = mapped_column(String(20))  # short, medium, long
    experience_level: Mapped[str | None] = mapped_column(String(20))  # beginner, intermediate, advanced
    goals: Mapped[dict[str, Any] | None] = mapped_column(JSON)  # array of goal strings
    interests: Mapped[dict[str, Any] | None] = mapped_column(JSON)  # for probability lab topics
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=utc_now)

    # Relationship to user
    user: Mapped["User"] = relationship("User", back_populates="profile")

    def __repr__(self) -> str:
        return f"<Profile user_id={self.user_id}>"

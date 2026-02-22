import uuid
from datetime import datetime, UTC

from sqlalchemy import String, DateTime, Integer, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from ...database import Base


def utc_now():
    return datetime.now(UTC)


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    session_id: Mapped[str] = mapped_column(String(36), nullable=False)
    event_name: Mapped[str] = mapped_column(String(50), nullable=False)
    event_properties: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    __table_args__ = (
        Index("ix_analytics_events_event_name", "event_name"),
        Index("ix_analytics_events_user_id", "user_id"),
        Index("ix_analytics_events_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AnalyticsEvent {self.event_name} user={self.user_id}>"

"""
Trading Database Models

Local trade log for analytics and learning.
"""

from datetime import datetime, UTC
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ...database import Base


def utcnow():
    return datetime.now(UTC)


class TradeLog(Base):
    """Local log of trades for analytics and learning."""

    __tablename__ = "trade_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    alpaca_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # buy, sell
    qty: Mapped[float] = mapped_column(Float, nullable=False)
    order_type: Mapped[str] = mapped_column(String(20), nullable=False)  # market, limit
    limit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    filled_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # pending, filled, cancelled, failed

    strategy_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True
    )
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

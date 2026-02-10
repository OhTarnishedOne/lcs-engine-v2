"""
Probability Lab Database Models

Prediction markets, user predictions, and calibration tracking.
"""

from datetime import datetime, UTC
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from ...database import Base


def utcnow():
    return datetime.now(UTC)


class PredictionMarket(Base):
    """Cached Kalshi markets or manually curated questions."""

    __tablename__ = "prediction_markets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    external_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True
    )  # Kalshi market ID

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)

    market_probability: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # 0-1

    close_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )  # "yes" or "no"

    explainer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    investing_connection: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class UserPrediction(Base):
    """User's probability predictions."""

    __tablename__ = "user_predictions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    market_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("prediction_markets.id", ondelete="CASCADE"), nullable=False
    )

    predicted_probability: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0-1.0
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    brier_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    saw_market_price: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class CalibrationScore(Base):
    """Aggregated calibration data for a user."""

    __tablename__ = "calibration_scores"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    total_predictions: Mapped[int] = mapped_column(Integer, default=0)
    resolved_predictions: Mapped[int] = mapped_column(Integer, default=0)
    average_brier_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    calibration_data: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Bucketed calibration curve data
    detected_biases: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # List of detected bias names

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

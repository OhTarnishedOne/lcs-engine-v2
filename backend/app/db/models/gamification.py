# app/db/models/gamification.py
# v2 — fixes applied:
#   + PROCESS_BUILDER added to BadgeSlug
#   + last_trend_bonus_at added to UserGamificationProfile

from datetime import datetime
from uuid import uuid4
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime,
    ForeignKey, Text, Enum, CheckConstraint, Index, JSON,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.gamification.user_ids import GamificationUserIdType

JSONType = JSON().with_variant(JSONB(), "postgresql")


def _pg_enum(enum_cls: type[PyEnum]) -> Enum:
    """Persist Python enum .value (lowercase) to match PostgreSQL native enums."""
    return Enum(enum_cls, values_callable=lambda x: [e.value for e in x])


class DecisionDomain(str, PyEnum):
    INVESTING        = "investing"
    CAREER           = "career"
    PERSONAL_FINANCE = "personal_finance"
    BUSINESS         = "business"
    LIFE             = "life"


class DecisionStatus(str, PyEnum):
    PENDING   = "pending"
    RESOLVED  = "resolved"
    EXPIRED   = "expired"
    CANCELLED = "cancelled"


class OutcomeSource(str, PyEnum):
    AUTO_MARKET   = "auto_market"
    SELF_REPORTED = "self_reported"


class TierLevel(str, PyEnum):
    INSTINCTIVE = "instinctive"
    REFLECTIVE  = "reflective"
    CALIBRATED  = "calibrated"
    STRATEGIC   = "strategic"
    ARCHITECT   = "architect"


class BadgeSlug(str, PyEnum):
    # Process
    FIRST_CALL        = "first_call"
    WHAT_WOULD_CHANGE = "what_would_change"
    PROCESS_BUILDER   = "process_builder"       # FIX #1: new slug
    SEVEN_DAY_STREAK  = "seven_day_streak"
    THIRTY_DAY_STREAK = "thirty_day_streak"
    # Calibration
    CALIBRATED_RUN              = "calibrated_run"
    STAYED_CALIBRATED_DRAWDOWN  = "stayed_calibrated_drawdown"
    # Reflection
    GOOD_LOSER    = "good_loser"
    HUMBLE_WINNER = "humble_winner"
    AVOIDED_REVENGE  = "avoided_revenge"
    REVISED_THESIS   = "revised_thesis"
    # Improvement
    BIAS_CORRECTED        = "bias_corrected"
    LOOP_CLOSED           = "loop_closed"
    SKILL_TRANSFERRED     = "skill_transferred"
    STABLE_UNDER_PRESSURE = "stable_under_pressure"


class Decision(Base):
    __tablename__ = "decisions"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id         = Column(GamificationUserIdType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question        = Column(Text, nullable=False)
    domain          = Column(_pg_enum(DecisionDomain), nullable=False, default=DecisionDomain.INVESTING)
    confidence      = Column(Float, nullable=False)
    reasoning       = Column(Text, nullable=True)
    falsification   = Column(Text, nullable=True)
    resolution_date = Column(DateTime, nullable=True)
    is_curated      = Column(Boolean, default=False)
    question_id     = Column(UUID(as_uuid=True), ForeignKey("curated_questions.id"), nullable=True)
    status          = Column(_pg_enum(DecisionStatus), default=DecisionStatus.PENDING, nullable=False)
    locked_at       = Column(DateTime, default=func.now())
    outcome_binary  = Column(Boolean, nullable=True)
    outcome_source  = Column(_pg_enum(OutcomeSource), nullable=True)
    outcome_notes   = Column(Text, nullable=True)
    resolved_at     = Column(DateTime, nullable=True)
    brier_score     = Column(Float, nullable=True)
    calibration_delta = Column(Float, nullable=True)
    created_at      = Column(DateTime, default=func.now())
    updated_at      = Column(DateTime, default=func.now(), onupdate=func.now())
    extra           = Column(JSONType, nullable=True)

    user            = relationship("User", viewonly=True)
    question_ref    = relationship(
        "CuratedQuestion", back_populates="logged_decisions"
    )
    review          = relationship(
        "DecisionReview", back_populates="decision", uselist=False
    )
    ai_tutor_session = relationship(
        "AITutorSession", back_populates="decision", uselist=False
    )

    __table_args__ = (
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="confidence_range"),
        Index("ix_decisions_user_id", "user_id"),
        Index("ix_decisions_status", "status"),
        Index("ix_decisions_domain", "domain"),
        Index("ix_decisions_locked_at", "locked_at"),
    )


class DecisionReview(Base):
    __tablename__ = "decision_reviews"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    decision_id     = Column(UUID(as_uuid=True), ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id         = Column(GamificationUserIdType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    outcome_attribution         = Column(Text, nullable=True)
    was_process_sound           = Column(Boolean, nullable=True)
    identified_bias             = Column(Text, nullable=True)
    luck_vs_process             = Column(String(20), nullable=True)
    thesis_revised              = Column(Boolean, default=False)
    self_flagged_bias_before_ai = Column(Boolean, default=False)
    reflection_points           = Column(Integer, default=0)
    triggers_good_loser         = Column(Boolean, default=False)
    triggers_humble_winner      = Column(Boolean, default=False)
    triggers_avoided_revenge    = Column(Boolean, default=False)
    created_at      = Column(DateTime, default=func.now())
    updated_at      = Column(DateTime, default=func.now(), onupdate=func.now())

    decision = relationship("Decision", back_populates="review")
    user     = relationship("User", viewonly=True)

    __table_args__ = (
        Index("ix_reviews_user_id", "user_id"),
        Index("ix_reviews_decision_id", "decision_id"),
    )


class UserGamificationProfile(Base):
    __tablename__ = "user_gamification_profiles"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id         = Column(GamificationUserIdType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    process_score      = Column(Float, default=0.0)
    calibration_score  = Column(Float, nullable=True)
    reflection_score   = Column(Float, nullable=True)
    improvement_score  = Column(Float, nullable=True)
    lcs_score          = Column(Float, default=0.0)
    tier               = Column(_pg_enum(TierLevel), default=TierLevel.INSTINCTIVE)
    tier_updated_at    = Column(DateTime, nullable=True)
    total_points       = Column(Integer, default=0)
    logging_streak_days      = Column(Integer, default=0)
    logging_streak_last_date = Column(DateTime, nullable=True)
    grace_days_used          = Column(Integer, default=0)
    grace_days_reset_at      = Column(DateTime, nullable=True)
    calibration_streak       = Column(Integer, default=0)
    review_streak            = Column(Integer, default=0)
    total_calls        = Column(Integer, default=0)
    resolved_calls     = Column(Integer, default=0)
    calibrated_calls   = Column(Integer, default=0)
    reviewed_calls     = Column(Integer, default=0)
    known_biases       = Column(JSONType, nullable=True)
    stable_under_pressure            = Column(Boolean, default=False)
    stable_under_pressure_earned_at  = Column(DateTime, nullable=True)
    domains_unlocked   = Column(JSONType, default=lambda: ["investing"])
    last_trend_bonus_at = Column(DateTime, nullable=True)  # FIX #4: idempotency guard
    created_at         = Column(DateTime, default=func.now())
    updated_at         = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", viewonly=True)

    __table_args__ = (
        Index("ix_gamification_profiles_user_id", "user_id"),
        Index("ix_gamification_profiles_tier", "tier"),
        Index("ix_gamification_profiles_lcs_score", "lcs_score"),
    )


class UserScoreSnapshot(Base):
    __tablename__ = "user_score_snapshots"

    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id            = Column(GamificationUserIdType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    process_score      = Column(Float, default=0.0)
    calibration_score  = Column(Float, default=0.0)
    reflection_score   = Column(Float, default=0.0)
    improvement_score  = Column(Float, default=0.0)
    lcs_score          = Column(Float, default=0.0)
    tier               = Column(_pg_enum(TierLevel), default=TierLevel.INSTINCTIVE)
    total_calls        = Column(Integer, default=0)
    resolved_calls     = Column(Integer, default=0)
    reviewed_calls     = Column(Integer, default=0)
    domain_scores      = Column(JSONType, nullable=True)
    rolling_brier      = Column(Float, nullable=True)
    triggered_by       = Column(UUID(as_uuid=True), ForeignKey("decisions.id"), nullable=True)
    snapshot_at        = Column(DateTime, default=func.now())

    user = relationship("User", viewonly=True)

    __table_args__ = (
        Index("ix_snapshots_user_id", "user_id"),
        Index("ix_snapshots_snapshot_at", "snapshot_at"),
    )


class UserBadge(Base):
    __tablename__ = "user_badges"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id     = Column(GamificationUserIdType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    badge_slug  = Column(_pg_enum(BadgeSlug), nullable=False)
    triggered_by_decision_id = Column(UUID(as_uuid=True), ForeignKey("decisions.id"), nullable=True)
    triggered_by_review_id   = Column(UUID(as_uuid=True), ForeignKey("decision_reviews.id"), nullable=True)
    points_awarded = Column(Integer, default=0)
    earned_at   = Column(DateTime, default=func.now())

    user = relationship("User", viewonly=True)

    __table_args__ = (
        Index("ix_user_badges_user_badge", "user_id", "badge_slug", unique=True),
    )


class PointsLedger(Base):
    __tablename__ = "points_ledger"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id       = Column(GamificationUserIdType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    points        = Column(Integer, nullable=False)
    reason        = Column(String(100), nullable=False)
    category      = Column(String(50), nullable=False)
    decision_id   = Column(UUID(as_uuid=True), ForeignKey("decisions.id"), nullable=True)
    review_id     = Column(UUID(as_uuid=True), ForeignKey("decision_reviews.id"), nullable=True)
    badge_slug    = Column(_pg_enum(BadgeSlug), nullable=True)
    running_total = Column(Integer, nullable=False)
    created_at    = Column(DateTime, default=func.now())

    user = relationship("User", viewonly=True)

    __table_args__ = (
        Index("ix_points_ledger_user_id", "user_id"),
        Index("ix_points_ledger_created_at", "created_at"),
        Index("ix_points_ledger_category", "category"),
    )


class CuratedQuestion(Base):
    __tablename__ = "curated_questions"

    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    question             = Column(Text, nullable=False)
    domain               = Column(_pg_enum(DecisionDomain), nullable=False)
    resolution_type      = Column(String(50), nullable=True)
    resolution_ticker    = Column(String(20), nullable=True)
    resolution_condition = Column(JSONType, nullable=True)
    is_active            = Column(Boolean, default=True)
    active_from          = Column(DateTime, nullable=True)
    expires_at           = Column(DateTime, nullable=True)
    resolved_at          = Column(DateTime, nullable=True)
    resolved_outcome     = Column(Boolean, nullable=True)
    created_at           = Column(DateTime, default=func.now())

    logged_decisions = relationship("Decision", back_populates="question_ref")

    __table_args__ = (
        Index("ix_curated_questions_domain", "domain"),
        Index("ix_curated_questions_is_active", "is_active"),
    )


class AITutorSession(Base):
    __tablename__ = "ai_tutor_sessions"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id             = Column(GamificationUserIdType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    decision_id         = Column(UUID(as_uuid=True), ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False, unique=True)
    bias_flagged        = Column(String(100), nullable=True)
    bias_severity       = Column(Float, nullable=True)
    clarifying_question = Column(Text, nullable=True)
    user_responded      = Column(Boolean, default=False)
    response_text       = Column(Text, nullable=True)
    points_awarded      = Column(Integer, default=0)
    created_at          = Column(DateTime, default=func.now())

    user     = relationship("User", viewonly=True)
    decision = relationship("Decision", back_populates="ai_tutor_session")


class InsightLoop(Base):
    __tablename__ = "insight_loops"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id           = Column(GamificationUserIdType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bias_name         = Column(String(100), nullable=False)
    domain            = Column(_pg_enum(DecisionDomain), nullable=False)
    detected_at       = Column(DateTime, nullable=False)
    acknowledged_at   = Column(DateTime, nullable=True)
    improved_at       = Column(DateTime, nullable=True)
    pre_bias_score    = Column(Float, nullable=True)
    post_bias_score   = Column(Float, nullable=True)
    improvement_delta = Column(Float, nullable=True)
    status            = Column(String(20), default="detected")
    points_awarded    = Column(Integer, default=0)
    completed_at      = Column(DateTime, nullable=True)
    created_at        = Column(DateTime, default=func.now())
    updated_at        = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", viewonly=True)

    __table_args__ = (
        Index("ix_insight_loops_user_id", "user_id"),
        Index("ix_insight_loops_status", "status"),
    )

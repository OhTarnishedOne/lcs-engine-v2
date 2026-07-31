"""Regression tests: gamification enums must persist lowercase .value to PostgreSQL."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import class_mapper

from app.auth.utils import hash_password
from app.database import Base
from app.db.models import User
from app.db.models.gamification import (
    BadgeSlug,
    Decision,
    DecisionDomain,
    DecisionStatus,
    OutcomeSource,
    TierLevel,
    UserBadge,
    UserGamificationProfile,
)
from app.db.models.probability import PredictionMarket, UserPrediction
from app.services.gamification.probability_bridge import (
    sync_prediction_resolution_to_gamification,
)


def _bind_value(model_cls, column: str, enum_member, dialect):
    mapper = class_mapper(model_cls)
    proc = mapper.columns[column].type.bind_processor(dialect)
    return proc(enum_member)


@pytest.mark.parametrize(
    "model_cls, column, enum_member, expected",
    [
        (Decision, "domain", DecisionDomain.INVESTING, "investing"),
        (Decision, "status", DecisionStatus.RESOLVED, "resolved"),
        (Decision, "outcome_source", OutcomeSource.AUTO_MARKET, "auto_market"),
        (UserGamificationProfile, "tier", TierLevel.INSTINCTIVE, "instinctive"),
        (UserBadge, "badge_slug", BadgeSlug.FIRST_CALL, "first_call"),
    ],
)
def test_gamification_enum_bind_uses_lowercase_value(
    model_cls, column, enum_member, expected
):
    """SQLAlchemy must bind enum .value, not .name (PostgreSQL native enums)."""
    engine = create_engine("sqlite://")
    dialect = engine.dialect
    assert _bind_value(model_cls, column, enum_member, dialect) == expected


def test_probability_bridge_persists_lowercase_enums(db):
    """Dual-write path inserts Decision rows with PostgreSQL-compatible enum values."""
    user_id = str(uuid4())
    db.add(
        User(
            id=user_id,
            email=f"{user_id}@test.com",
            password_hash=hash_password("test"),
        )
    )
    db.flush()
    market = PredictionMarket(
        id=str(uuid4()),
        title="Will CPI fall below 3%?",
        category="macro",
        close_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
    )
    db.add(market)
    db.flush()
    prediction = UserPrediction(
        id=str(uuid4()),
        user_id=user_id,
        market_id=market.id,
        predicted_probability=0.65,
        reasoning="Trend looks favorable.",
    )
    db.add(prediction)
    db.commit()

    sync_prediction_resolution_to_gamification(db, prediction, market, actual=1)
    db.commit()

    decision = db.query(Decision).filter(Decision.id == UUID(prediction.id)).one()
    assert decision.domain == DecisionDomain.INVESTING
    assert decision.status == DecisionStatus.RESOLVED
    assert decision.outcome_source == OutcomeSource.AUTO_MARKET

    engine = create_engine("sqlite://")
    dialect = engine.dialect
    assert _bind_value(Decision, "domain", decision.domain, dialect) == "investing"
    assert _bind_value(Decision, "status", decision.status, dialect) == "resolved"
    assert (
        _bind_value(Decision, "outcome_source", decision.outcome_source, dialect)
        == "auto_market"
    )

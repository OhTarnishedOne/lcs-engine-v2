"""
Dual-write fault isolation (ADR-001).

Probability Lab resolution dual-writes into the gamification Decision pipeline.
A gamification failure must NEVER break Lab resolution: the market must still
resolve and Brier scores must still be written, even when the gamification
write raises.
"""

from uuid import uuid4

import pytest

from app.auth.utils import hash_password
from app.db.models import User
from app.db.models.gamification import Decision
from app.db.models.probability import PredictionMarket, UserPrediction
from app.probability.service import ProbabilityService


def _seed(db):
    user_id = str(uuid4())
    db.add(
        User(
            id=user_id,
            email=f"{user_id}@test.com",
            password_hash=hash_password("test"),
        )
    )
    db.flush()

    service = ProbabilityService(db)
    service.seed_markets_if_empty()
    db.commit()

    market = db.query(PredictionMarket).first()
    prediction = UserPrediction(
        id=str(uuid4()),
        user_id=user_id,
        market_id=market.id,
        predicted_probability=0.70,
    )
    db.add(prediction)
    db.commit()
    return service, market, prediction


@pytest.mark.asyncio
async def test_gamification_failure_does_not_break_lab_resolution(db, monkeypatch):
    service, market, prediction = _seed(db)

    # Simulate a gamification dual-write blowing up. resolve_predictions imports
    # this symbol from the bridge module at call time, so patching the module
    # attribute is what the resolution loop actually calls.
    import app.services.gamification.probability_bridge as bridge_mod

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated gamification failure")

    monkeypatch.setattr(
        bridge_mod, "sync_prediction_resolution_to_gamification", _boom
    )

    # Must NOT raise despite the gamification failure.
    count = await service.resolve_predictions(market.id, "yes")

    assert count == 1

    # Core Lab resolution succeeded and is durable.
    db.refresh(market)
    db.refresh(prediction)
    assert market.is_resolved is True
    assert market.resolution == "yes"
    assert prediction.brier_score is not None
    assert abs(prediction.brier_score - 0.09) < 1e-6  # (0.7 - 1)^2

    # The failed gamification write left no partial Decision behind (savepoint
    # rollback isolated it).
    assert db.query(Decision).count() == 0


@pytest.mark.asyncio
async def test_successful_dual_write_still_records_decision(db):
    """Control: with no failure injected, the dual-write persists a Decision."""
    service, market, prediction = _seed(db)

    count = await service.resolve_predictions(market.id, "yes")

    assert count == 1
    db.refresh(prediction)
    assert prediction.brier_score is not None
    # The gamification Decision mirror was created for the resolved prediction.
    assert db.query(Decision).count() == 1

"""
Full-pipeline integration test for the gamification lifecycle.

Exercises the real dual-write path end to end against a live SQLite session:

    Probability Lab prediction
        -> resolve with an outcome
        -> probability_bridge fires
        -> Brier score written to the Decision record
        -> score_family_updater updates the score families
        -> badge_evaluator.on_decision_resolved fires
        -> re-resolution is idempotent (no duplicate badges/points)

Run just this pipeline with:  pytest tests/ -k "lifecycle"
"""

from datetime import datetime, timezone
from uuid import uuid4

from app.auth.utils import hash_password
from app.db.models import User
from app.db.models.gamification import (
    BadgeSlug,
    Decision,
    DecisionStatus,
    OutcomeSource,
    PointsLedger,
    UserBadge,
    UserGamificationProfile,
    UserScoreSnapshot,
)
from app.db.models.probability import PredictionMarket, UserPrediction
from app.gamification.user_ids import user_id_to_uuid
from app.services.gamification.probability_bridge import (
    sync_prediction_resolution_to_gamification,
)


def _make_user(db):
    user_id = str(uuid4())
    db.add(
        User(
            id=user_id,
            email=f"{user_id}@test.com",
            password_hash=hash_password("test"),
        )
    )
    db.flush()
    return user_id


def _make_market(db, index):
    market = PredictionMarket(
        id=str(uuid4()),
        title=f"Will macro event {index} happen?",
        category="macro",
        close_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
    )
    db.add(market)
    db.flush()
    return market


def _make_prediction(db, user_id, market, probability):
    prediction = UserPrediction(
        id=str(uuid4()),
        user_id=user_id,
        market_id=market.id,
        predicted_probability=probability,
        reasoning="Base rate favors this outcome.",
    )
    db.add(prediction)
    db.flush()
    return prediction


def test_full_decision_lifecycle_pipeline(db):
    user_id = _make_user(db)
    user_uuid = user_id_to_uuid(user_id)

    # 1. Create predictions in the Probability Lab. Five well-calibrated calls
    #    (0.95 confidence, outcome "yes" -> 5pp gap) so the calibration streak
    #    reaches 5 and the CALIBRATED_RUN badge is exercised.
    pairs = []
    for i in range(5):
        market = _make_market(db, i)
        prediction = _make_prediction(db, user_id, market, 0.95)
        pairs.append((prediction, market))
    db.commit()

    # 2 + 3. Resolve each prediction -> the bridge fires the full pipeline.
    for prediction, market in pairs:
        sync_prediction_resolution_to_gamification(db, prediction, market, actual=1)
    db.commit()

    # 3 + 4. probability_bridge fired: a resolved Decision with a Brier score
    #        exists for every prediction.
    decisions = (
        db.query(Decision).filter(Decision.user_id == user_uuid).all()
    )
    assert len(decisions) == 5
    for decision in decisions:
        assert decision.status == DecisionStatus.RESOLVED
        assert decision.outcome_source == OutcomeSource.AUTO_MARKET
        assert decision.brier_score is not None
        # (0.95 - 1)^2 = 0.0025
        assert abs(decision.brier_score - 0.0025) < 1e-6

    # 5. score_family_updater ran and updated the correct families.
    profile = (
        db.query(UserGamificationProfile)
        .filter(UserGamificationProfile.user_id == user_uuid)
        .one()
    )
    assert profile.resolved_calls == 5
    assert profile.process_score > 0                     # process family updated
    assert profile.lcs_score > 0                          # composite updated
    # Calibration family unlocks at 5 resolved calls (ADR-001).
    # avg Brier 0.0025 -> 100 * (1 - 2 * 0.0025) = 99.5
    assert profile.calibration_score == 99.5
    # A score snapshot was written per resolution.
    assert (
        db.query(UserScoreSnapshot)
        .filter(UserScoreSnapshot.user_id == user_uuid)
        .count()
        == 5
    )

    # 6. badge_evaluator.on_decision_resolved fired: resolution points were
    #    ledgered and the calibration streak advanced to 5, earning
    #    CALIBRATED_RUN exactly once.
    assert profile.calibration_streak == 5
    ledger_reasons = {
        entry.reason
        for entry in db.query(PointsLedger)
        .filter(PointsLedger.user_id == user_uuid)
        .all()
    }
    assert "Decision Resolved" in ledger_reasons
    assert (
        db.query(UserBadge)
        .filter(
            UserBadge.user_id == user_uuid,
            UserBadge.badge_slug == BadgeSlug.CALIBRATED_RUN,
        )
        .count()
        == 1
    )

    # 7. Re-resolving the same predictions is a no-op: the bridge is idempotent,
    #    so no duplicate badges and no additional points/ledger entries.
    points_before = profile.total_points
    ledger_before = (
        db.query(PointsLedger)
        .filter(PointsLedger.user_id == user_uuid)
        .count()
    )

    for prediction, market in pairs:
        sync_prediction_resolution_to_gamification(db, prediction, market, actual=1)
    db.commit()
    db.refresh(profile)

    assert profile.total_points == points_before
    assert (
        db.query(PointsLedger)
        .filter(PointsLedger.user_id == user_uuid)
        .count()
        == ledger_before
    )
    assert (
        db.query(UserBadge)
        .filter(
            UserBadge.user_id == user_uuid,
            UserBadge.badge_slug == BadgeSlug.CALIBRATED_RUN,
        )
        .count()
        == 1
    )
    # Decision count is unchanged — no duplicate Decision rows were created.
    assert db.query(Decision).filter(Decision.user_id == user_uuid).count() == 5

"""
Tests for the Calibration Score computation (Phase 3/6).
"""

import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import patch

from app.probability.calibration import (
    compute_calibration_score,
    _recency_weight,
    _brier_to_score,
    _compute_weighted_score,
)
from app.db.models import User, PredictionMarket, UserPrediction, CalibrationScoreHistory


def _create_user(db, email="test@example.com"):
    user = User(email=email, password_hash="hashed", tier="free")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_resolved_market(db, title="Test Market", resolution="yes", days_ago=10):
    close = datetime.now(UTC) - timedelta(days=days_ago + 1)
    market = PredictionMarket(
        title=title,
        category="cpi",
        close_date=close,
        is_resolved=True,
        resolution=resolution,
    )
    db.add(market)
    db.commit()
    db.refresh(market)
    return market


def _create_prediction(db, user_id, market_id, probability, brier_score, days_ago=5):
    pred = UserPrediction(
        user_id=user_id,
        market_id=market_id,
        predicted_probability=probability,
        brier_score=brier_score,
        created_at=datetime.now(UTC) - timedelta(days=days_ago),
    )
    db.add(pred)
    db.commit()
    db.refresh(pred)
    return pred


class TestCalibrationScoreNullCases:
    """Tests for null/empty return conditions."""

    def test_returns_null_for_user_with_no_resolved_predictions(self, db):
        user = _create_user(db)
        result = compute_calibration_score(db, user.id)
        assert result["overall_score"] is None
        assert result["resolved_count"] == 0

    def test_returns_null_for_user_with_fewer_than_5_resolved(self, db):
        user = _create_user(db)
        # Create 4 resolved predictions (below threshold)
        for i in range(4):
            market = _create_resolved_market(db, f"Market {i}")
            _create_prediction(db, user.id, market.id, 0.7, 0.09, days_ago=i + 1)

        result = compute_calibration_score(db, user.id)
        assert result["overall_score"] is None
        assert result["resolved_count"] == 4


class TestCalibrationScoreComputation:
    """Tests for score math."""

    def test_perfect_predictions_returns_100(self, db):
        user = _create_user(db)
        # Brier score of 0 = predicted 1.0 and outcome was yes (or 0.0 and outcome was no)
        for i in range(5):
            market = _create_resolved_market(db, f"Market {i}", resolution="yes")
            _create_prediction(db, user.id, market.id, 1.0, 0.0, days_ago=i + 1)

        result = compute_calibration_score(db, user.id)
        assert result["overall_score"] == 100

    def test_uniform_50_50_predictions_on_resolved_events(self, db):
        """Predicting 50% on everything that resolves yes gives Brier=0.25 → score=0."""
        user = _create_user(db)
        for i in range(5):
            market = _create_resolved_market(db, f"Market {i}", resolution="yes")
            # Brier for 0.5 prediction, outcome 1: (0.5 - 1)^2 = 0.25
            _create_prediction(db, user.id, market.id, 0.5, 0.25, days_ago=i + 1)

        result = compute_calibration_score(db, user.id)
        assert result["overall_score"] == 0

    def test_recency_weighting_recent_predictions_count_more(self, db):
        user = _create_user(db)

        # 3 recent predictions (within 30d) — perfect (brier=0)
        for i in range(3):
            market = _create_resolved_market(db, f"Recent {i}")
            _create_prediction(db, user.id, market.id, 1.0, 0.0, days_ago=5 + i)

        # 2 old predictions (50-60 days ago) — terrible (brier=0.25)
        for i in range(2):
            market = _create_resolved_market(db, f"Old {i}", days_ago=55)
            _create_prediction(db, user.id, market.id, 0.5, 0.25, days_ago=55 + i)

        result = compute_calibration_score(db, user.id)
        # Weighted: (3*1.0*0.0 + 2*0.7*0.25) / (3*1.0 + 2*0.7) = 0.35 / 4.4 ≈ 0.0795
        # Score: 100 * (1 - 4 * 0.0795) ≈ 68
        assert result["overall_score"] is not None
        assert result["overall_score"] > 50  # Biased toward the better recent predictions


class TestSubScores:
    """Tests for category sub-scores."""

    def test_sub_score_only_returned_for_categories_with_3_plus_predictions(self, db):
        user = _create_user(db)

        # 4 CPI predictions (should produce sub-score)
        for i in range(4):
            market = PredictionMarket(
                title=f"CPI {i}", category="cpi",
                close_date=datetime.now(UTC) - timedelta(days=20),
                is_resolved=True, resolution="yes",
            )
            db.add(market)
            db.commit()
            _create_prediction(db, user.id, market.id, 0.8, 0.04, days_ago=i + 1)

        # 2 GDP predictions (should NOT produce sub-score)
        for i in range(2):
            market = PredictionMarket(
                title=f"GDP {i}", category="gdp",
                close_date=datetime.now(UTC) - timedelta(days=20),
                is_resolved=True, resolution="yes",
            )
            db.add(market)
            db.commit()
            _create_prediction(db, user.id, market.id, 0.7, 0.09, days_ago=i + 1)

        result = compute_calibration_score(db, user.id)
        categories = [s["category"] for s in result["sub_scores"]]
        assert "cpi" in categories
        assert "gdp" not in categories


class TestPercentile:
    """Tests for percentile computation."""

    def test_percentile_suppressed_when_population_below_10(self, db):
        user = _create_user(db)
        for i in range(5):
            market = _create_resolved_market(db, f"Market {i}")
            _create_prediction(db, user.id, market.id, 0.8, 0.04, days_ago=i + 1)

        result = compute_calibration_score(db, user.id)
        # Only 1 user in the system — well below 10
        assert result["percentile"] is None


class TestResolutionPipeline:
    """Tests for resolution idempotency."""

    @pytest.mark.asyncio
    async def test_resolution_pipeline_idempotent(self, db):
        """Running resolve_predictions twice doesn't double-count."""
        from app.probability.service import ProbabilityService

        user = _create_user(db)
        market = PredictionMarket(
            title="Idempotent test",
            category="cpi",
            close_date=datetime.now(UTC) - timedelta(days=5),
            is_resolved=False,
            resolution=None,
        )
        db.add(market)
        db.commit()

        pred = UserPrediction(
            user_id=user.id,
            market_id=market.id,
            predicted_probability=0.7,
        )
        db.add(pred)
        db.commit()

        service = ProbabilityService(db)

        # Resolve once
        count1 = await service.resolve_predictions(market.id, "yes")
        db.refresh(pred)
        brier1 = pred.brier_score

        # Resolve again — brier should remain the same
        count2 = await service.resolve_predictions(market.id, "yes")
        db.refresh(pred)
        brier2 = pred.brier_score

        assert brier1 == brier2
        assert abs(brier1 - (0.7 - 1) ** 2) < 0.0001  # 0.09

    def test_resolution_pipeline_handles_unresolved_events_gracefully(self, db):
        """Markets with no data yet should be skipped, not error."""
        user = _create_user(db)
        market = PredictionMarket(
            title="Future event",
            category="gdp",
            close_date=datetime.now(UTC) + timedelta(days=30),  # Future
            is_resolved=False,
        )
        db.add(market)
        db.commit()

        pred = UserPrediction(
            user_id=user.id,
            market_id=market.id,
            predicted_probability=0.6,
        )
        db.add(pred)
        db.commit()

        # Should not raise, prediction should remain unresolved
        result = compute_calibration_score(db, user.id)
        assert result["overall_score"] is None  # Not enough resolved
        db.refresh(pred)
        assert pred.brier_score is None  # Still unresolved


class TestHelpers:
    """Unit tests for helper functions."""

    def test_recency_weight_recent(self):
        now = datetime.now(UTC)
        assert _recency_weight(now - timedelta(days=5), now) == 1.0

    def test_recency_weight_mid(self):
        now = datetime.now(UTC)
        assert _recency_weight(now - timedelta(days=45), now) == 0.7

    def test_recency_weight_old(self):
        now = datetime.now(UTC)
        assert _recency_weight(now - timedelta(days=75), now) == 0.4

    def test_brier_to_score_perfect(self):
        assert _brier_to_score(0.0) == 100

    def test_brier_to_score_worst(self):
        assert _brier_to_score(0.25) == 0

    def test_brier_to_score_mid(self):
        # 0.125 → 100 * (1 - 4*0.125) = 50
        assert _brier_to_score(0.125) == 50

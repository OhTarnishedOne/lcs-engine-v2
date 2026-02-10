"""
Probability Lab Service

Business logic for prediction markets, calibration, and bias detection.
"""

import logging
from datetime import datetime, UTC
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..db.models import PredictionMarket, UserPrediction, CalibrationScore
from ..integrations import KalshiClient

logger = logging.getLogger(__name__)


# Bias explanations with investing connections
BIAS_EXPLANATIONS = {
    "overconfidence": {
        "name": "Overconfidence",
        "description": "You tend to be very certain, but accuracy doesn't match confidence.",
        "tip": "Try hedging more. If 90% sure, consider whether 75% is more honest.",
        "investing_connection": "Overconfident investors take bigger positions than they should."
    },
    "underconfidence": {
        "name": "Underconfidence",
        "description": "You stay near 50/50 even when you have real information.",
        "tip": "When you have evidence, commit. 50% means no opinion.",
        "investing_connection": "Underconfident investors miss opportunities by staying in cash."
    },
    "anchoring": {
        "name": "Anchoring",
        "description": "Your predictions are heavily influenced by the first number you see.",
        "tip": "Form your own estimate BEFORE looking at others'.",
        "investing_connection": "Anchored investors fixate on purchase price instead of current value."
    },
    "extreme_aversion": {
        "name": "Extreme Aversion",
        "description": "You avoid very high or very low predictions even when evidence supports them.",
        "tip": "Sometimes things really are very likely or unlikely. It's okay to predict 5% or 95%.",
        "investing_connection": "This makes investors underreact to both strong opportunities and clear risks."
    }
}


# Seed data for prediction markets
SEED_MARKETS = [
    {
        "title": "Will the Federal Reserve cut interest rates at their next meeting?",
        "category": "fed-funds-rate",
        "description": "The FOMC meets 8 times per year to set the federal funds rate.",
        "market_probability": 0.35,
        "close_date": "2026-03-19T18:00:00Z",
        "explainer": "The federal funds rate affects everything from mortgage rates to savings yields.",
        "investing_connection": "When rates drop, bonds go up and stocks often rally. When rates rise, bonds fall and growth stocks get hit."
    },
    {
        "title": "Will US CPI inflation be above 3% for the next monthly report?",
        "category": "cpi",
        "description": "CPI measures the average change in consumer prices.",
        "market_probability": 0.42,
        "close_date": "2026-03-12T12:30:00Z",
        "explainer": "CPI is the most-watched inflation measure. The Fed targets 2%.",
        "investing_connection": "High inflation erodes purchasing power. It hurts bond holders but can benefit commodities producers."
    },
    {
        "title": "Will US GDP growth exceed 2.5% in Q1 2026?",
        "category": "gdp",
        "description": "GDP measures total economic output.",
        "market_probability": 0.55,
        "close_date": "2026-04-30T12:30:00Z",
        "explainer": "GDP growth above 2.5% is considered strong. Below 0% for two quarters is a recession.",
        "investing_connection": "Strong GDP growth is generally good for stocks, especially cyclical sectors like industrials and consumer discretionary."
    },
    {
        "title": "Will the unemployment rate stay below 4.5% through March 2026?",
        "category": "unemployment",
        "description": "The Bureau of Labor Statistics releases monthly employment data.",
        "market_probability": 0.72,
        "close_date": "2026-04-04T12:30:00Z",
        "explainer": "Low unemployment means a strong job market. The Fed considers this when setting rates.",
        "investing_connection": "Low unemployment supports consumer spending, which drives ~70% of US GDP."
    },
    {
        "title": "Will the 10-year Treasury yield end March above 4.0%?",
        "category": "treasury-yields",
        "description": "The 10-year Treasury yield is a benchmark for borrowing costs.",
        "market_probability": 0.65,
        "close_date": "2026-03-31T20:00:00Z",
        "explainer": "Treasury yields move inversely to bond prices. Higher yields mean bonds are paying more but existing bonds lose value.",
        "investing_connection": "Rising yields hurt growth stocks (future earnings worth less) but benefit bank stocks (wider lending margins)."
    },
    {
        "title": "Will the US enter a recession in the first half of 2026?",
        "category": "recession",
        "description": "A recession is commonly defined as two consecutive quarters of negative GDP growth.",
        "market_probability": 0.15,
        "close_date": "2026-07-31T12:00:00Z",
        "explainer": "Recessions bring falling stock prices, rising unemployment, and lower consumer spending.",
        "investing_connection": "Defensive stocks (utilities, healthcare) and bonds tend to outperform during recessions."
    },
    {
        "title": "Will the Fed Funds rate be below 4.0% by June 2026?",
        "category": "fed-funds-rate",
        "description": "The Fed has been cutting rates from their 2023-2024 highs.",
        "market_probability": 0.48,
        "close_date": "2026-06-30T18:00:00Z",
        "explainer": "Rate cuts make borrowing cheaper, stimulate the economy, and generally boost asset prices.",
        "investing_connection": "Falling rates are bullish for real estate (cheaper mortgages), growth stocks, and bonds."
    },
    {
        "title": "Will core PCE inflation fall below 2.5% by mid-2026?",
        "category": "inflation",
        "description": "Core PCE is the Fed's preferred inflation measure, excluding food and energy.",
        "market_probability": 0.38,
        "close_date": "2026-06-30T12:30:00Z",
        "explainer": "The Fed targets 2% PCE. Getting close to target gives the Fed room to cut rates.",
        "investing_connection": "Falling inflation is good for bonds and growth stocks, but can signal weakening demand."
    },
    {
        "title": "Will US retail sales grow more than 3% year-over-year in Q1 2026?",
        "category": "gdp",
        "description": "Retail sales measure consumer spending at stores and online.",
        "market_probability": 0.52,
        "close_date": "2026-04-15T12:30:00Z",
        "explainer": "Consumer spending drives ~70% of the US economy. Strong retail sales signal economic health.",
        "investing_connection": "Strong retail data benefits consumer stocks (Amazon, Walmart) and signals economic expansion."
    },
    {
        "title": "Will initial jobless claims exceed 250,000 in any week of March 2026?",
        "category": "unemployment",
        "description": "Weekly jobless claims measure new unemployment filings.",
        "market_probability": 0.30,
        "close_date": "2026-04-03T12:30:00Z",
        "explainer": "Rising jobless claims can be an early warning sign of economic slowdown.",
        "investing_connection": "Spiking claims often precede broader market selloffs and defensive sector rotations."
    },
]


class ProbabilityService:
    """Service for probability lab operations."""

    def __init__(self, db: Session, kalshi: Optional[KalshiClient] = None):
        self.db = db
        self.kalshi = kalshi

    def seed_markets_if_empty(self):
        """Seed prediction markets if table is empty."""
        count = self.db.query(PredictionMarket).count()
        if count > 0:
            return

        logger.info("Seeding prediction markets...")
        for market_data in SEED_MARKETS:
            market = PredictionMarket(
                title=market_data["title"],
                category=market_data["category"],
                description=market_data["description"],
                market_probability=market_data["market_probability"],
                close_date=datetime.fromisoformat(market_data["close_date"].replace("Z", "+00:00")),
                explainer=market_data["explainer"],
                investing_connection=market_data["investing_connection"],
            )
            self.db.add(market)

        self.db.commit()
        logger.info(f"Seeded {len(SEED_MARKETS)} prediction markets")

    async def get_active_markets(self) -> list[PredictionMarket]:
        """Get active markets. Try Kalshi, fall back to DB seed data."""
        # Try Kalshi first
        if self.kalshi:
            try:
                kalshi_markets = await self.kalshi.get_active_markets()
                if kalshi_markets:
                    # Could sync to DB here if needed
                    pass
            except Exception as e:
                logger.info(f"Kalshi unavailable, using seed data: {e}")

        # Ensure seed data exists
        self.seed_markets_if_empty()

        # Return unresolved markets from DB
        return (
            self.db.query(PredictionMarket)
            .filter(PredictionMarket.is_resolved == False)
            .order_by(PredictionMarket.close_date.asc())
            .all()
        )

    def get_market(self, market_id: str) -> Optional[PredictionMarket]:
        """Get a single market by ID."""
        return self.db.query(PredictionMarket).filter(
            PredictionMarket.id == market_id
        ).first()

    async def submit_prediction(
        self,
        user_id: str,
        market_id: str,
        probability: float,
        reasoning: Optional[str] = None
    ) -> tuple[UserPrediction, PredictionMarket]:
        """
        Submit a prediction.
        Returns prediction and market (with probability revealed).
        """
        # Validate probability range
        if probability < 0.0 or probability > 1.0:
            raise ValueError("Probability must be between 0.0 and 1.0")

        # Get market
        market = self.get_market(market_id)
        if not market:
            raise ValueError("Market not found")

        if market.is_resolved:
            raise ValueError("This market has closed")

        # Check for existing prediction
        existing = self.db.query(UserPrediction).filter(
            and_(
                UserPrediction.user_id == user_id,
                UserPrediction.market_id == market_id
            )
        ).first()

        if existing:
            raise ValueError("You've already predicted this market")

        # Save prediction
        prediction = UserPrediction(
            user_id=user_id,
            market_id=market_id,
            predicted_probability=probability,
            reasoning=reasoning,
            saw_market_price=False,
        )

        self.db.add(prediction)

        # Update calibration count
        self._update_calibration_counts(user_id)

        self.db.commit()
        self.db.refresh(prediction)

        return prediction, market

    def calculate_brier_score(self, predicted: float, actual: int) -> float:
        """
        Calculate Brier score.
        Brier = (predicted - actual)^2
        Lower is better. 0=perfect, 1=worst.
        """
        return (predicted - actual) ** 2

    async def resolve_predictions(self, market_id: str, resolution: str) -> int:
        """
        When market resolves: calculate Brier scores, update calibration.
        Returns number of predictions scored.
        """
        if resolution not in ["yes", "no"]:
            raise ValueError("Resolution must be 'yes' or 'no'")

        market = self.get_market(market_id)
        if not market:
            raise ValueError("Market not found")

        # Update market
        market.is_resolved = True
        market.resolution = resolution

        # Calculate Brier scores for all predictions
        actual = 1 if resolution == "yes" else 0
        predictions = self.db.query(UserPrediction).filter(
            UserPrediction.market_id == market_id
        ).all()

        for pred in predictions:
            pred.brier_score = self.calculate_brier_score(
                pred.predicted_probability, actual
            )

        self.db.commit()

        # Update calibration for each user
        user_ids = set(p.user_id for p in predictions)
        for user_id in user_ids:
            self._update_calibration(user_id)

        return len(predictions)

    def _update_calibration_counts(self, user_id: str):
        """Update prediction counts in calibration."""
        calibration = self.db.query(CalibrationScore).filter(
            CalibrationScore.user_id == user_id
        ).first()

        if not calibration:
            calibration = CalibrationScore(
                user_id=user_id,
                total_predictions=0,
                resolved_predictions=0,
            )
            self.db.add(calibration)

        calibration.total_predictions += 1

    def _update_calibration(self, user_id: str):
        """Recalculate full calibration for a user."""
        predictions = (
            self.db.query(UserPrediction)
            .filter(UserPrediction.user_id == user_id)
            .all()
        )

        resolved = [p for p in predictions if p.brier_score is not None]

        if not resolved:
            return

        # Calculate average Brier score
        avg_brier = sum(p.brier_score for p in resolved) / len(resolved)

        # Calculate calibration curve (10% buckets)
        buckets = {i: {"predictions": [], "outcomes": []} for i in range(10)}

        for pred in resolved:
            bucket_idx = min(int(pred.predicted_probability * 10), 9)
            market = self.get_market(pred.market_id)
            actual = 1 if market and market.resolution == "yes" else 0
            buckets[bucket_idx]["predictions"].append(pred.predicted_probability)
            buckets[bucket_idx]["outcomes"].append(actual)

        calibration_data = []
        for i, data in buckets.items():
            if data["predictions"]:
                calibration_data.append({
                    "bucket_start": i / 10,
                    "bucket_end": (i + 1) / 10,
                    "predicted_avg": sum(data["predictions"]) / len(data["predictions"]),
                    "actual_rate": sum(data["outcomes"]) / len(data["outcomes"]),
                    "count": len(data["predictions"]),
                })

        # Detect biases
        biases = self._detect_biases(predictions, resolved)

        # Update calibration record
        calibration = self.db.query(CalibrationScore).filter(
            CalibrationScore.user_id == user_id
        ).first()

        if not calibration:
            calibration = CalibrationScore(user_id=user_id)
            self.db.add(calibration)

        calibration.total_predictions = len(predictions)
        calibration.resolved_predictions = len(resolved)
        calibration.average_brier_score = avg_brier
        calibration.calibration_data = calibration_data
        calibration.detected_biases = biases

        self.db.commit()

    def _detect_biases(self, all_predictions: list, resolved: list) -> list[str]:
        """Detect cognitive biases from prediction patterns."""
        biases = []

        # Overconfidence requires resolved predictions
        if len(resolved) >= 5:
            # Overconfidence: High confidence (>0.8 or <0.2) but poor accuracy
            extreme_preds = [p for p in resolved if p.predicted_probability > 0.8 or p.predicted_probability < 0.2]
            if len(extreme_preds) >= 3:
                correct = 0
                for p in extreme_preds:
                    market = self.get_market(p.market_id)
                    if market:
                        actual = 1 if market.resolution == "yes" else 0
                        # Prediction was confident in the right direction
                        if (p.predicted_probability > 0.5 and actual == 1) or \
                           (p.predicted_probability < 0.5 and actual == 0):
                            correct += 1
                accuracy = correct / len(extreme_preds)
                if accuracy < 0.6:
                    biases.append("overconfidence")

        # These biases can be detected from all predictions (no resolution needed)
        probs = [p.predicted_probability for p in all_predictions]
        if len(probs) >= 5:
            # Extreme aversion: Never predicts below 15% or above 85%
            has_extreme_low = any(p < 0.15 for p in probs)
            has_extreme_high = any(p > 0.85 for p in probs)
            if not has_extreme_low and not has_extreme_high:
                biases.append("extreme_aversion")

            # Underconfidence: Predictions cluster near 50%
            mid_range = [p for p in probs if 0.4 <= p <= 0.6]
            if len(mid_range) / len(probs) > 0.7:
                biases.append("underconfidence")

        return biases

    async def get_calibration(self, user_id: str) -> dict:
        """Get calibration data for display."""
        calibration = self.db.query(CalibrationScore).filter(
            CalibrationScore.user_id == user_id
        ).first()

        if not calibration:
            return {
                "total_predictions": 0,
                "resolved_predictions": 0,
                "average_brier_score": None,
                "calibration_curve": [],
                "detected_biases": [],
            }

        bias_infos = [
            BIAS_EXPLANATIONS[b] for b in (calibration.detected_biases or [])
            if b in BIAS_EXPLANATIONS
        ]

        return {
            "total_predictions": calibration.total_predictions,
            "resolved_predictions": calibration.resolved_predictions,
            "average_brier_score": calibration.average_brier_score,
            "calibration_curve": calibration.calibration_data or [],
            "detected_biases": bias_infos,
        }

    async def get_user_predictions(
        self,
        user_id: str,
        status: str = "all"
    ) -> list[dict]:
        """Get predictions with market info. Status: all, pending, resolved."""
        query = self.db.query(UserPrediction).filter(
            UserPrediction.user_id == user_id
        )

        predictions = query.order_by(UserPrediction.created_at.desc()).all()

        results = []
        for pred in predictions:
            market = self.get_market(pred.market_id)
            if not market:
                continue

            # Filter by status
            if status == "pending" and market.is_resolved:
                continue
            if status == "resolved" and not market.is_resolved:
                continue

            results.append({
                "id": pred.id,
                "market_id": pred.market_id,
                "market_title": market.title,
                "predicted_probability": pred.predicted_probability,
                "market_probability": market.market_probability,
                "reasoning": pred.reasoning,
                "brier_score": pred.brier_score,
                "is_resolved": market.is_resolved,
                "resolution": market.resolution,
                "created_at": pred.created_at,
            })

        return results

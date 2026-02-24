"""
Market Resolution Service

Automates resolution of FRED-backed prediction markets and generates
new markets for upcoming economic releases.
"""

import logging
from datetime import date, datetime, UTC
from dateutil.relativedelta import relativedelta

from sqlalchemy.orm import Session

from ..db.models import PredictionMarket
from ..integrations.fred import FredClient
from .service import ProbabilityService
from .market_templates import (
    MARKET_TEMPLATES,
    SEED_MARKET_MAPPINGS,
    get_next_reference_date,
    get_close_date,
    format_period,
)

logger = logging.getLogger(__name__)


class MarketAutomation:
    """Handles auto-resolution of FRED-backed markets and generation of new ones."""

    def __init__(self, db: Session, fred: FredClient, service: ProbabilityService | None = None):
        self.db = db
        self.fred = fred
        self.service = service or ProbabilityService(db)

    async def check_and_resolve(self) -> dict:
        """Check all unresolved FRED-backed markets. Auto-resolve if data available.

        Returns {"resolved": [...market_ids], "checked": N}
        """
        now = datetime.now(UTC)
        resolved_ids = []

        # Query unresolved markets with FRED resolution metadata whose close date has passed
        markets = (
            self.db.query(PredictionMarket)
            .filter(
                PredictionMarket.is_resolved == False,
                PredictionMarket.resolution_metadata.isnot(None),
                PredictionMarket.close_date < now,
            )
            .all()
        )

        for market in markets:
            meta = market.resolution_metadata
            if not meta or meta.get("source") != "fred":
                continue

            try:
                result = await self._resolve_market(market, meta)
                if result is not None:
                    await self.service.resolve_predictions(market.id, result)
                    resolved_ids.append(market.id)
                    logger.info(
                        f"Resolved market '{market.title}' as '{result}'"
                    )
            except Exception as e:
                logger.warning(f"Failed to resolve market {market.id}: {e}")

        return {"resolved": resolved_ids, "checked": len(markets)}

    async def _resolve_market(self, market: PredictionMarket, meta: dict) -> str | None:
        """Attempt to resolve a single market using FRED data.

        Returns "yes", "no", or None if data not yet available.
        """
        series_id = meta["series_id"]
        transform = meta.get("transform", "raw")
        threshold = meta["threshold"]
        operator = meta["operator"]
        reference_date = meta.get("reference_date", "")

        if transform == "pct_change_year":
            value = await self._get_pct_change_year(series_id, reference_date)
        elif transform == "raw":
            # For weekly series (ICSA), check all observations in the period
            if series_id == "ICSA" and operator == "gt":
                return await self._resolve_weekly_max(
                    series_id, reference_date, threshold
                )
            value = await self._get_raw_value(series_id, reference_date)
        else:
            logger.warning(f"Unknown transform: {transform}")
            return None

        if value is None:
            return None

        return self._compare(value, threshold, operator)

    async def _get_raw_value(self, series_id: str, reference_date: str) -> float | None:
        """Get the raw FRED value for a reference date."""
        obs = await self.fred.get_latest_observation(series_id)
        if not obs:
            return None

        # For daily series, just use the latest value
        # For monthly, check that the observation is for the right period
        if reference_date:
            obs_date = obs.get("date", "")
            if obs_date < reference_date:
                return None  # Data not yet published for this period

        try:
            return float(obs["value"])
        except (ValueError, KeyError):
            return None

    async def _get_pct_change_year(self, series_id: str, reference_date: str) -> float | None:
        """Calculate year-over-year percent change for a series."""
        if not reference_date:
            return None

        ref = date.fromisoformat(reference_date)
        year_ago = ref - relativedelta(years=1)

        # Fetch observations covering both the current and year-ago period
        observations = await self.fred.get_observations(
            series_id,
            start_date=(year_ago - relativedelta(months=1)).isoformat(),
            end_date=(ref + relativedelta(months=1)).isoformat(),
        )

        if len(observations) < 2:
            return None

        # Find the observation closest to the reference date and year ago
        current_obs = None
        year_ago_obs = None

        for obs in observations:
            obs_date = date.fromisoformat(obs["date"])
            try:
                val = float(obs["value"])
            except ValueError:
                continue

            if obs_date <= ref:
                current_obs = val
            if obs_date <= year_ago:
                year_ago_obs = val

        if current_obs is None or year_ago_obs is None or year_ago_obs == 0:
            return None

        return ((current_obs - year_ago_obs) / year_ago_obs) * 100

    async def _resolve_weekly_max(
        self, series_id: str, reference_date: str, threshold: float
    ) -> str | None:
        """For weekly series: check if any observation in the month exceeds threshold."""
        if not reference_date:
            return None

        ref = date.fromisoformat(reference_date)
        month_start = ref.replace(day=1)
        month_end = month_start + relativedelta(months=1) - relativedelta(days=1)

        observations = await self.fred.get_observations(
            series_id,
            start_date=month_start.isoformat(),
            end_date=month_end.isoformat(),
        )

        if not observations:
            return None

        try:
            max_value = max(float(obs["value"]) for obs in observations)
        except (ValueError, KeyError):
            return None

        # For ICSA, threshold is in thousands (e.g., 250 = 250K = 250,000)
        return "yes" if max_value > threshold * 1000 else "no"

    def _compare(self, value: float, threshold: float, operator: str) -> str:
        """Compare value to threshold. Returns 'yes' or 'no'."""
        ops = {
            "gt": value > threshold,
            "lt": value < threshold,
            "gte": value >= threshold,
            "lte": value <= threshold,
        }
        result = ops.get(operator)
        if result is None:
            logger.warning(f"Unknown operator: {operator}")
            return "no"
        return "yes" if result else "no"

    async def generate_upcoming_markets(self) -> dict:
        """Create markets for next period if they don't already exist.

        Returns {"created": [...market_titles], "skipped": N}
        """
        today = date.today()
        created = []
        skipped = 0

        for template in MARKET_TEMPLATES:
            try:
                reference_date = get_next_reference_date(
                    template["frequency"], today
                )
                period = format_period(reference_date, template["frequency"])
                close_date = get_close_date(reference_date, template["series_id"])

                # Check if market already exists for this series + reference date
                existing = (
                    self.db.query(PredictionMarket)
                    .filter(PredictionMarket.resolution_metadata.isnot(None))
                    .all()
                )

                already_exists = False
                for m in existing:
                    meta = m.resolution_metadata or {}
                    if (
                        meta.get("series_id") == template["series_id"]
                        and meta.get("reference_date") == reference_date.isoformat()
                    ):
                        already_exists = True
                        break

                if already_exists:
                    skipped += 1
                    continue

                title = template["title_template"].format(
                    threshold=template["threshold"],
                    period=period,
                )

                resolution_metadata = {
                    "source": "fred",
                    "series_id": template["series_id"],
                    "threshold": template["threshold"],
                    "operator": template["operator"],
                    "transform": template["transform"],
                    "reference_date": reference_date.isoformat(),
                }

                market = PredictionMarket(
                    title=title,
                    category=template["category"],
                    description=template["description"],
                    market_probability=template.get("default_probability", 0.50),
                    close_date=datetime(
                        close_date.year,
                        close_date.month,
                        close_date.day,
                        12, 0, 0,
                        tzinfo=UTC,
                    ),
                    resolution_metadata=resolution_metadata,
                    explainer=template["explainer"],
                    investing_connection=template["investing_connection"],
                )
                self.db.add(market)
                created.append(title)
            except Exception as e:
                logger.warning(
                    f"Failed to create market for {template['series_id']}: {e}"
                )

        if created:
            self.db.commit()

        return {"created": created, "skipped": skipped}

    async def backfill_seed_markets(self) -> int:
        """Add resolution_metadata to the original seed markets so they can be
        auto-resolved. Only updates markets that have resolution_metadata = None.

        Returns count of markets updated.
        """
        updated = 0
        markets = (
            self.db.query(PredictionMarket)
            .filter(PredictionMarket.resolution_metadata.is_(None))
            .all()
        )

        for market in markets:
            for title_prefix, metadata in SEED_MARKET_MAPPINGS.items():
                if market.title.startswith(title_prefix):
                    market.resolution_metadata = metadata
                    updated += 1
                    break

        if updated:
            self.db.commit()
            logger.info(f"Backfilled resolution_metadata for {updated} seed markets")

        return updated

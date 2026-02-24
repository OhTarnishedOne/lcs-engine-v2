"""
FRED (Federal Reserve Economic Data) Client

Read-only integration for economic data series (CPI, unemployment, GDP, etc.).
Used for auto-resolving prediction markets when new data is published.
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class FredClient:
    """Read-only integration with the FRED API for economic data."""

    BASE_URL = "https://api.stlouisfed.org/fred"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    def _base_params(self) -> dict:
        """Base query params included in every request."""
        return {"api_key": self.api_key, "file_type": "json"}

    async def _get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make GET request to FRED API."""
        url = f"{self.BASE_URL}{endpoint}"
        request_params = self._base_params()
        if params:
            request_params.update(params)
        try:
            response = await self.client.get(url, params=request_params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.warning(f"FRED API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.warning(f"FRED API unavailable: {e}")
            raise

    async def get_latest_observation(self, series_id: str) -> Optional[dict]:
        """Get most recent observation for a FRED series.

        Returns: {"date": "2026-01-01", "value": "3.1"} or None
        """
        try:
            data = await self._get("/series/observations", {
                "series_id": series_id,
                "sort_order": "desc",
                "limit": 1,
            })
            observations = data.get("observations", [])
            if observations and observations[0].get("value") != ".":
                return observations[0]
            return None
        except Exception as e:
            logger.warning(f"Failed to get latest observation for {series_id}: {e}")
            return None

    async def get_observations(
        self,
        series_id: str,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        """Get observations in a date range. For historical data and transforms.

        Args:
            series_id: FRED series ID (e.g., "CPIAUCSL")
            start_date: Start date "YYYY-MM-DD"
            end_date: End date "YYYY-MM-DD"

        Returns: List of {"date": "...", "value": "..."} dicts
        """
        try:
            data = await self._get("/series/observations", {
                "series_id": series_id,
                "observation_start": start_date,
                "observation_end": end_date,
                "sort_order": "asc",
            })
            # Filter out missing values (FRED uses "." for missing)
            return [
                obs for obs in data.get("observations", [])
                if obs.get("value") != "."
            ]
        except Exception as e:
            logger.warning(f"Failed to get observations for {series_id}: {e}")
            return []

    async def get_series_info(self, series_id: str) -> Optional[dict]:
        """Get series metadata (title, frequency, units)."""
        try:
            data = await self._get("/series", {"series_id": series_id})
            serieses = data.get("seriess", [])
            if serieses:
                return serieses[0]
            return None
        except Exception as e:
            logger.warning(f"Failed to get series info for {series_id}: {e}")
            return None

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

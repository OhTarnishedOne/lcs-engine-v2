"""
Kalshi Prediction Markets Client

Read-only integration for economics/finance prediction markets.
Falls back to seed data if API is unavailable.
"""

import logging
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class KalshiClient:
    """Read-only integration with Kalshi for economics/finance predictions."""

    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

    ECONOMICS_CATEGORIES = [
        "fed-funds-rate",
        "inflation",
        "cpi",
        "gdp",
        "unemployment",
        "recession",
        "treasury-yields",
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    def _get_headers(self) -> dict:
        """Get request headers with optional auth."""
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make GET request to Kalshi API."""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = await self.client.get(
                url,
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.warning(f"Kalshi API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.warning(f"Kalshi API unavailable: {e}")
            raise

    async def get_active_markets(self, limit: int = 20) -> list[dict]:
        """
        Get active economics/finance markets.
        Filter to ECONOMICS_CATEGORIES only.
        """
        try:
            # Try to get markets from Kalshi
            data = await self._get("/markets", {
                "limit": limit * 2,  # Get extra to filter
                "status": "open",
            })

            markets = []
            for market in data.get("markets", []):
                # Filter to economics categories
                category = market.get("category", "").lower()
                if any(cat in category for cat in self.ECONOMICS_CATEGORIES):
                    yes_price = market.get("yes_bid", 0) or market.get("last_price", 0.5)
                    markets.append({
                        "id": market.get("ticker"),
                        "title": market.get("title"),
                        "category": category,
                        "yes_price": yes_price / 100 if yes_price > 1 else yes_price,
                        "no_price": 1 - (yes_price / 100 if yes_price > 1 else yes_price),
                        "volume": market.get("volume", 0),
                        "close_date": market.get("close_time"),
                        "description": market.get("subtitle", ""),
                    })

                if len(markets) >= limit:
                    break

            return markets
        except Exception as e:
            logger.info(f"Kalshi API unavailable, will use seed data: {e}")
            return []

    async def get_market(self, market_id: str) -> Optional[dict]:
        """Get single market details."""
        try:
            data = await self._get(f"/markets/{market_id}")
            market = data.get("market", {})

            if not market:
                return None

            yes_price = market.get("yes_bid", 0) or market.get("last_price", 0.5)

            return {
                "id": market.get("ticker"),
                "title": market.get("title"),
                "category": market.get("category", "").lower(),
                "yes_price": yes_price / 100 if yes_price > 1 else yes_price,
                "no_price": 1 - (yes_price / 100 if yes_price > 1 else yes_price),
                "volume": market.get("volume", 0),
                "close_date": market.get("close_time"),
                "description": market.get("subtitle", ""),
                "rules": market.get("rules_primary", ""),
            }
        except Exception as e:
            logger.warning(f"Failed to get market {market_id}: {e}")
            return None

    async def get_market_history(self, market_id: str) -> list[dict]:
        """Get price history for a market."""
        try:
            data = await self._get(f"/markets/{market_id}/history")

            history = []
            for point in data.get("history", []):
                history.append({
                    "timestamp": point.get("ts"),
                    "yes_price": point.get("yes_price", 0) / 100,
                    "volume": point.get("volume", 0),
                })

            return history
        except Exception as e:
            logger.warning(f"Failed to get market history for {market_id}: {e}")
            return []

    async def check_resolution(self, market_id: str) -> Optional[dict]:
        """Check if a market has resolved."""
        try:
            data = await self._get(f"/markets/{market_id}")
            market = data.get("market", {})

            status = market.get("status", "").lower()
            if status in ["settled", "finalized"]:
                result = market.get("result", "")
                settled_price = 1.0 if result == "yes" else 0.0

                return {
                    "resolved": True,
                    "result": result,
                    "settled_price": settled_price,
                }

            return {"resolved": False, "result": None, "settled_price": None}
        except Exception as e:
            logger.warning(f"Failed to check resolution for {market_id}: {e}")
            return None

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

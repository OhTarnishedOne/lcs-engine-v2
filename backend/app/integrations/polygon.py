"""
Polygon.io Market Data Client

REST API integration for real-time and historical market data.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class PolygonClient:
    """Market data via Polygon.io REST API."""

    BASE_URL = "https://api.polygon.io"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def _get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make authenticated GET request to Polygon API."""
        params = params or {}
        params["apiKey"] = self.api_key

        url = f"{self.BASE_URL}{endpoint}"
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def get_quote(self, symbol: str) -> dict:
        """Latest price for a symbol."""
        try:
            # Get previous day's close for reference
            data = await self._get(f"/v2/aggs/ticker/{symbol.upper()}/prev")

            if data.get("results") and len(data["results"]) > 0:
                result = data["results"][0]
                prev_close = result.get("c", 0)

                # Try real-time snapshot (requires paid Polygon tier)
                try:
                    snapshot = await self._get(f"/v2/snapshot/locale/us/markets/stocks/tickers/{symbol.upper()}")

                    if snapshot.get("ticker"):
                        ticker_data = snapshot["ticker"]
                        current = ticker_data.get("day", {}).get("c") or ticker_data.get("prevDay", {}).get("c", prev_close)
                        prev = ticker_data.get("prevDay", {}).get("c", prev_close)

                        change = current - prev if prev else 0
                        change_pct = (change / prev * 100) if prev else 0

                        return {
                            "symbol": symbol.upper(),
                            "price": current,
                            "change": round(change, 2),
                            "change_pct": round(change_pct, 2),
                            "volume": ticker_data.get("day", {}).get("v", 0),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                except httpx.HTTPStatusError:
                    logger.debug(f"Snapshot unavailable for {symbol}, using previous close")

            # Fallback to previous close
            prev_close = 0
            volume = 0
            if data.get("results") and len(data["results"]) > 0:
                result = data["results"][0]
                prev_close = result.get("c", 0)
                volume = result.get("v", 0)

            return {
                "symbol": symbol.upper(),
                "price": prev_close,
                "change": 0,
                "change_pct": 0,
                "volume": volume,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Symbol {symbol} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            raise

    async def get_quotes_batch(self, symbols: list[str]) -> list[dict]:
        """Latest prices for multiple symbols."""
        results = []
        for symbol in symbols:
            try:
                quote = await self.get_quote(symbol)
                results.append(quote)
            except Exception as e:
                logger.warning(f"Failed to get quote for {symbol}: {e}")
                results.append({
                    "symbol": symbol.upper(),
                    "price": None,
                    "error": str(e)
                })
        return results

    async def search_symbols(self, query: str) -> list[dict]:
        """Search for stock/ETF symbols by name or ticker."""
        try:
            data = await self._get("/v3/reference/tickers", {
                "search": query,
                "active": "true",
                "market": "stocks",
                "limit": 20,
            })

            results = []
            for ticker in data.get("results", []):
                # Filter to stocks and ETFs on US exchanges
                ticker_type = ticker.get("type", "")
                if ticker_type in ["CS", "ETF", "ADRC"]:  # Common Stock, ETF, ADR
                    results.append({
                        "ticker": ticker.get("ticker"),
                        "name": ticker.get("name"),
                        "type": "ETF" if ticker_type == "ETF" else "Stock",
                        "market": ticker.get("primary_exchange", ""),
                    })

            return results[:15]  # Limit results
        except Exception as e:
            logger.error(f"Failed to search symbols for '{query}': {e}")
            raise

    async def get_chart_data(
        self,
        symbol: str,
        timespan: str = "day",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> dict:
        """OHLCV data for charting."""
        try:
            # Default date range
            if not to_date:
                to_date = datetime.utcnow().strftime("%Y-%m-%d")
            if not from_date:
                # Default to 30 days ago
                from_dt = datetime.utcnow() - timedelta(days=30)
                from_date = from_dt.strftime("%Y-%m-%d")

            data = await self._get(
                f"/v2/aggs/ticker/{symbol.upper()}/range/1/{timespan}/{from_date}/{to_date}",
                {"adjusted": "true", "sort": "asc", "limit": 500}
            )

            bars = []
            for bar in data.get("results", []):
                bars.append({
                    "open": bar.get("o"),
                    "high": bar.get("h"),
                    "low": bar.get("l"),
                    "close": bar.get("c"),
                    "volume": bar.get("v"),
                    "timestamp": datetime.fromtimestamp(bar.get("t", 0) / 1000).isoformat(),
                })

            return {
                "symbol": symbol.upper(),
                "bars": bars,
            }
        except Exception as e:
            logger.error(f"Failed to get chart data for {symbol}: {e}")
            raise

    async def get_company_info(self, symbol: str) -> dict:
        """Basic company details."""
        try:
            data = await self._get(f"/v3/reference/tickers/{symbol.upper()}")

            result = data.get("results", {})
            return {
                "ticker": result.get("ticker"),
                "name": result.get("name"),
                "description": result.get("description", ""),
                "sector": result.get("sic_description", ""),
                "industry": result.get("sic_description", ""),
                "market_cap": result.get("market_cap"),
                "homepage_url": result.get("homepage_url", ""),
                "logo_url": result.get("branding", {}).get("logo_url", ""),
            }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Company info for {symbol} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to get company info for {symbol}: {e}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

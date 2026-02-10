"""
Trading Service

Business logic for paper trading.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from ..db.models import TradeLog
from ..integrations import AlpacaClient, PolygonClient

logger = logging.getLogger(__name__)


class TradingService:
    """Service for paper trading operations."""

    def __init__(
        self,
        db: Session,
        alpaca: Optional[AlpacaClient] = None,
        polygon: Optional[PolygonClient] = None
    ):
        self.db = db
        self.alpaca = alpaca
        self.polygon = polygon

    async def get_portfolio(self, user_id: str) -> dict:
        """Get full portfolio with account and positions."""
        if not self.alpaca:
            raise RuntimeError("Paper trading is not configured")

        account = await self.alpaca.get_account()
        positions = await self.alpaca.get_positions()

        # Calculate total P&L
        total_pl = sum(p.get("unrealized_pl", 0) for p in positions)
        total_pl_pct = (total_pl / float(account["equity"]) * 100) if account["equity"] else 0

        return {
            "equity": account["equity"],
            "cash": account["cash"],
            "buying_power": account["buying_power"],
            "total_pl": total_pl,
            "total_pl_pct": round(total_pl_pct, 2),
            "positions": positions,
        }

    async def get_positions(self) -> list[dict]:
        """Get all current positions."""
        if not self.alpaca:
            raise RuntimeError("Paper trading is not configured")
        return await self.alpaca.get_positions()

    async def get_position(self, symbol: str) -> Optional[dict]:
        """Get a single position."""
        if not self.alpaca:
            raise RuntimeError("Paper trading is not configured")
        return await self.alpaca.get_position(symbol)

    async def place_order(
        self,
        user_id: str,
        symbol: str,
        qty: float,
        side: str,
        order_type: str,
        limit_price: Optional[float] = None,
        strategy_id: Optional[str] = None,
        reasoning: Optional[str] = None,
    ) -> TradeLog:
        """Place a paper trade and log it."""
        if not self.alpaca:
            raise RuntimeError("Paper trading is not configured")

        # Place order via Alpaca
        order = await self.alpaca.place_order(
            symbol=symbol,
            qty=qty,
            side=side,
            order_type=order_type,
            limit_price=limit_price,
        )

        # Log the trade locally
        trade_log = TradeLog(
            user_id=user_id,
            alpaca_order_id=order.get("id"),
            symbol=symbol.upper(),
            side=side,
            qty=qty,
            order_type=order_type,
            limit_price=limit_price,
            filled_price=order.get("filled_avg_price"),
            status=order.get("status", "pending"),
            strategy_id=strategy_id,
            reasoning=reasoning,
        )

        self.db.add(trade_log)
        self.db.commit()
        self.db.refresh(trade_log)

        return trade_log

    async def get_orders(self, status: str = "all") -> list[dict]:
        """Get orders from Alpaca."""
        if not self.alpaca:
            raise RuntimeError("Paper trading is not configured")
        return await self.alpaca.get_orders(status)

    async def cancel_order(self, order_id: str) -> dict:
        """Cancel an open order."""
        if not self.alpaca:
            raise RuntimeError("Paper trading is not configured")
        return await self.alpaca.cancel_order(order_id)

    def get_trade_history(self, user_id: str, limit: int = 50) -> list[TradeLog]:
        """Get user's trade history from local log."""
        return (
            self.db.query(TradeLog)
            .filter(TradeLog.user_id == user_id)
            .order_by(TradeLog.created_at.desc())
            .limit(limit)
            .all()
        )

    async def get_portfolio_history(self, period: str = "1M") -> dict:
        """Get portfolio value history for charting."""
        if not self.alpaca:
            raise RuntimeError("Paper trading is not configured")
        return await self.alpaca.get_portfolio_history(period=period)

    async def search_symbols(self, query: str) -> list[dict]:
        """Search for stock/ETF symbols."""
        if not self.polygon:
            raise RuntimeError("Market data is not configured")
        return await self.polygon.search_symbols(query)

    async def get_quote(self, symbol: str) -> dict:
        """Get latest quote for a symbol."""
        if not self.polygon:
            raise RuntimeError("Market data is not configured")
        return await self.polygon.get_quote(symbol)

    async def get_company_info(self, symbol: str) -> dict:
        """Get company information."""
        if not self.polygon:
            raise RuntimeError("Market data is not configured")
        return await self.polygon.get_company_info(symbol)

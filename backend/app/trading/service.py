"""
Trading Service

Business logic for paper trading.
Supports both real Alpaca integration and simulated guest trading.
"""

import logging
from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session

from ..db.models import TradeLog
from ..integrations import AlpacaClient, PolygonClient

logger = logging.getLogger(__name__)

GUEST_STARTING_CASH = 100_000.0

# Simulated prices for guest trading (no Alpaca/Polygon calls)
SIMULATED_PRICES = {
    "AAPL": 189.25, "TSLA": 234.95, "SPY": 502.18, "NVDA": 892.50,
    "MSFT": 415.80, "AMZN": 186.40, "GOOGL": 157.25, "META": 498.10,
    "BRK.B": 425.00, "JPM": 198.50, "V": 278.30, "JNJ": 155.20,
    "WMT": 168.90, "PG": 162.40, "HD": 342.00, "BAC": 38.50,
    "XOM": 112.30, "DIS": 108.75, "NFLX": 625.00, "AMD": 165.40,
}


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

    # ------------------------------------------------------------------
    # Guest / simulated trading (no Alpaca)
    # ------------------------------------------------------------------

    def _get_simulated_price(self, symbol: str) -> float:
        return SIMULATED_PRICES.get(symbol.upper(), 150.0)

    async def get_guest_portfolio(self, user_id: str) -> dict:
        """Build portfolio from trade_logs for guest users."""
        trades = self.get_trade_history(user_id, limit=500)

        # Compute positions from trade history
        holdings: dict[str, float] = defaultdict(float)  # symbol → shares
        cash_spent = 0.0

        for trade in reversed(trades):  # oldest first
            if trade.status != "filled":
                continue
            price = trade.filled_price or self._get_simulated_price(trade.symbol)
            if trade.side == "buy":
                holdings[trade.symbol] += trade.qty
                cash_spent += trade.qty * price
            elif trade.side == "sell":
                holdings[trade.symbol] -= trade.qty
                cash_spent -= trade.qty * price

        cash = GUEST_STARTING_CASH - cash_spent
        positions = []
        total_value = 0.0

        for symbol, shares in holdings.items():
            if shares <= 0:
                continue
            current_price = self._get_simulated_price(symbol)
            market_value = shares * current_price
            # Estimate avg cost from trades
            buy_qty = sum(t.qty for t in trades if t.symbol == symbol and t.side == "buy" and t.status == "filled")
            buy_cost = sum(t.qty * (t.filled_price or self._get_simulated_price(t.symbol)) for t in trades if t.symbol == symbol and t.side == "buy" and t.status == "filled")
            avg_cost = buy_cost / buy_qty if buy_qty > 0 else current_price
            unrealized_pl = (current_price - avg_cost) * shares

            positions.append({
                "symbol": symbol,
                "qty": shares,
                "avg_entry_price": round(avg_cost, 2),
                "current_price": current_price,
                "market_value": round(market_value, 2),
                "unrealized_pl": round(unrealized_pl, 2),
                "unrealized_plpc": round((unrealized_pl / (avg_cost * shares)) * 100, 2) if avg_cost * shares > 0 else 0,
            })
            total_value += market_value

        equity = cash + total_value
        total_pl = equity - GUEST_STARTING_CASH

        return {
            "equity": round(equity, 2),
            "cash": round(cash, 2),
            "buying_power": round(cash, 2),
            "total_pl": round(total_pl, 2),
            "total_pl_pct": round((total_pl / GUEST_STARTING_CASH) * 100, 2),
            "positions": positions,
        }

    async def get_guest_positions(self, user_id: str) -> list[dict]:
        """Get positions computed from trade logs."""
        portfolio = await self.get_guest_portfolio(user_id)
        return portfolio["positions"]

    async def place_guest_order(
        self,
        user_id: str,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = "market",
        limit_price: Optional[float] = None,
    ) -> TradeLog:
        """Simulate an order for guest users — no Alpaca call."""
        price = self._get_simulated_price(symbol)

        if side == "sell":
            # Check the user actually holds enough
            portfolio = await self.get_guest_portfolio(user_id)
            held = 0.0
            for pos in portfolio["positions"]:
                if pos["symbol"].upper() == symbol.upper():
                    held = pos["qty"]
                    break
            if held < qty:
                raise ValueError(f"Insufficient shares: you hold {held} {symbol} but tried to sell {qty}")

        if side == "buy":
            portfolio = await self.get_guest_portfolio(user_id)
            cost = qty * price
            if cost > portfolio["cash"]:
                raise ValueError(f"Insufficient cash: need ${cost:.2f} but have ${portfolio['cash']:.2f}")

        trade_log = TradeLog(
            user_id=user_id,
            alpaca_order_id=None,
            symbol=symbol.upper(),
            side=side,
            qty=qty,
            order_type=order_type,
            limit_price=limit_price,
            filled_price=price,
            status="filled",
        )
        self.db.add(trade_log)
        self.db.commit()
        self.db.refresh(trade_log)
        return trade_log

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

"""
Alpaca Paper Trading Client

Integration with Alpaca Markets for paper trading.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType, QueryOrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

logger = logging.getLogger(__name__)


class AlpacaClient:
    """Paper trading integration via Alpaca Markets."""

    def __init__(self, api_key: str, secret_key: str, base_url: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url
        self.paper = "paper" in base_url.lower()

        self.trading_client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=self.paper
        )
        self.data_client = StockHistoricalDataClient(
            api_key=api_key,
            secret_key=secret_key
        )

    async def get_account(self) -> dict:
        """Account balance, equity, buying power, cash."""
        try:
            account = self.trading_client.get_account()
            return {
                "equity": float(account.equity),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
                "portfolio_value": float(account.portfolio_value),
                "currency": account.currency,
                "status": account.status.value if hasattr(account.status, 'value') else str(account.status),
            }
        except Exception as e:
            logger.error(f"Failed to get account: {e}")
            raise

    async def get_positions(self) -> list[dict]:
        """Current open positions with P&L."""
        try:
            positions = self.trading_client.get_all_positions()
            return [
                {
                    "symbol": p.symbol,
                    "qty": float(p.qty),
                    "avg_entry_price": float(p.avg_entry_price),
                    "current_price": float(p.current_price),
                    "market_value": float(p.market_value),
                    "unrealized_pl": float(p.unrealized_pl),
                    "unrealized_pl_pct": float(p.unrealized_plpc) * 100,  # Convert to percentage
                    "side": p.side.value if hasattr(p.side, 'value') else str(p.side),
                }
                for p in positions
            ]
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise

    async def get_position(self, symbol: str) -> Optional[dict]:
        """Single position details."""
        try:
            p = self.trading_client.get_open_position(symbol.upper())
            return {
                "symbol": p.symbol,
                "qty": float(p.qty),
                "avg_entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_pl_pct": float(p.unrealized_plpc) * 100,
                "side": p.side.value if hasattr(p.side, 'value') else str(p.side),
            }
        except Exception as e:
            if "position does not exist" in str(e).lower():
                return None
            logger.error(f"Failed to get position {symbol}: {e}")
            raise

    async def place_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        order_type: str,
        limit_price: Optional[float] = None,
        time_in_force: str = "day"
    ) -> dict:
        """Place a paper trade order."""
        # Validate inputs
        if qty <= 0:
            raise ValueError("Quantity must be greater than 0")
        if side not in ["buy", "sell"]:
            raise ValueError("Side must be 'buy' or 'sell'")
        if order_type not in ["market", "limit"]:
            raise ValueError("Order type must be 'market' or 'limit'")
        if order_type == "limit" and limit_price is None:
            raise ValueError("Limit orders require a limit_price")

        try:
            order_side = OrderSide.BUY if side == "buy" else OrderSide.SELL
            tif = TimeInForce.DAY if time_in_force == "day" else TimeInForce.GTC

            if order_type == "market":
                order_request = MarketOrderRequest(
                    symbol=symbol.upper(),
                    qty=qty,
                    side=order_side,
                    time_in_force=tif
                )
            else:
                order_request = LimitOrderRequest(
                    symbol=symbol.upper(),
                    qty=qty,
                    side=order_side,
                    time_in_force=tif,
                    limit_price=limit_price
                )

            order = self.trading_client.submit_order(order_request)

            return {
                "id": str(order.id),
                "client_order_id": order.client_order_id,
                "symbol": order.symbol,
                "qty": float(order.qty) if order.qty else qty,
                "side": order.side.value if hasattr(order.side, 'value') else str(order.side),
                "order_type": order.order_type.value if hasattr(order.order_type, 'value') else str(order.order_type),
                "status": order.status.value if hasattr(order.status, 'value') else str(order.status),
                "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
                "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
                "created_at": order.created_at.isoformat() if order.created_at else None,
            }
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise

    async def get_orders(self, status: str = "all") -> list[dict]:
        """List orders. Status: open, closed, all."""
        try:
            if status == "open":
                query_status = QueryOrderStatus.OPEN
            elif status == "closed":
                query_status = QueryOrderStatus.CLOSED
            else:
                query_status = QueryOrderStatus.ALL

            request = GetOrdersRequest(status=query_status, limit=100)
            orders = self.trading_client.get_orders(request)

            return [
                {
                    "id": str(o.id),
                    "symbol": o.symbol,
                    "qty": float(o.qty) if o.qty else 0,
                    "side": o.side.value if hasattr(o.side, 'value') else str(o.side),
                    "order_type": o.order_type.value if hasattr(o.order_type, 'value') else str(o.order_type),
                    "status": o.status.value if hasattr(o.status, 'value') else str(o.status),
                    "filled_avg_price": float(o.filled_avg_price) if o.filled_avg_price else None,
                    "limit_price": float(o.limit_price) if o.limit_price else None,
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                }
                for o in orders
            ]
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise

    async def cancel_order(self, order_id: str) -> dict:
        """Cancel an open order."""
        try:
            self.trading_client.cancel_order_by_id(order_id)
            return {"cancelled": True, "order_id": order_id}
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise

    async def get_portfolio_history(self, period: str = "1M", timeframe: str = "1D") -> dict:
        """Historical portfolio value for charting."""
        try:
            # Map period to days
            period_map = {
                "1D": 1,
                "1W": 7,
                "1M": 30,
                "3M": 90,
                "1Y": 365,
            }
            days = period_map.get(period, 30)

            history = self.trading_client.get_portfolio_history(
                period=f"{days}D",
                timeframe="1D"
            )

            return {
                "timestamps": [ts.isoformat() if hasattr(ts, 'isoformat') else str(ts) for ts in (history.timestamp or [])],
                "equity": list(history.equity or []),
                "profit_loss": list(history.profit_loss or []),
                "profit_loss_pct": list(history.profit_loss_pct or []),
            }
        except Exception as e:
            logger.error(f"Failed to get portfolio history: {e}")
            raise

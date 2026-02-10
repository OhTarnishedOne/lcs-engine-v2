"""
Trading Schemas

Pydantic models for trading request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlaceOrderRequest(BaseModel):
    """Request to place a trade order."""
    symbol: str = Field(..., min_length=1, max_length=10)
    qty: float = Field(..., gt=0)
    side: str = Field(..., pattern="^(buy|sell)$")
    order_type: str = Field(default="market", pattern="^(market|limit)$")
    limit_price: Optional[float] = Field(default=None, gt=0)
    strategy_id: Optional[str] = None
    reasoning: Optional[str] = Field(default=None, max_length=500)


class OrderResponse(BaseModel):
    """Trade order response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    alpaca_order_id: Optional[str] = None
    symbol: str
    side: str
    qty: float
    order_type: str
    status: str
    limit_price: Optional[float] = None
    filled_price: Optional[float] = None
    created_at: datetime


class PositionResponse(BaseModel):
    """Current position in a security."""
    symbol: str
    qty: float
    avg_entry_price: float
    current_price: float
    market_value: float
    unrealized_pl: float
    unrealized_pl_pct: float


class PortfolioResponse(BaseModel):
    """Full portfolio summary."""
    equity: float
    cash: float
    buying_power: float
    total_pl: float
    total_pl_pct: float
    positions: list[PositionResponse]


class PortfolioHistoryResponse(BaseModel):
    """Portfolio value over time."""
    timestamps: list[str]
    equity: list[float]
    profit_loss: list[float]
    profit_loss_pct: list[float]


class SymbolSearchResponse(BaseModel):
    """Stock/ETF search result."""
    ticker: str
    name: str
    type: str


class QuoteResponse(BaseModel):
    """Latest price quote."""
    symbol: str
    price: float
    change: float
    change_pct: float
    volume: int = 0
    timestamp: str


class CompanyInfoResponse(BaseModel):
    """Company details."""
    ticker: str
    name: str
    description: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    homepage_url: Optional[str] = None


class TradeHistoryResponse(BaseModel):
    """Trade history item."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    symbol: str
    side: str
    qty: float
    order_type: str
    status: str
    filled_price: Optional[float] = None
    strategy_id: Optional[str] = None
    reasoning: Optional[str] = None
    created_at: datetime

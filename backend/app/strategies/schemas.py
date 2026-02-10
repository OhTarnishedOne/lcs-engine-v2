"""
Strategy Schemas

Pydantic models for strategy request/response validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class StrategyGenerateRequest(BaseModel):
    """Request to generate a new strategy."""
    strategy_type: Optional[str] = None  # If None, auto-select based on profile
    preferences: Optional[dict] = None   # Optional overrides


class AssetAllocation(BaseModel):
    """Single asset in a strategy portfolio."""
    ticker: str
    name: str
    allocation_pct: float
    rationale: str


class StrategyResponse(BaseModel):
    """Full strategy response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    strategy_type: str
    risk_level: int
    time_horizon: str
    assets: list[AssetAllocation]
    rationale: str
    risks: str
    learning_points: list[str]
    created_at: datetime


class StrategyListResponse(BaseModel):
    """List of strategies."""
    strategies: list[StrategyResponse]
    total: int


class StrategyCompareRequest(BaseModel):
    """Request to compare strategies."""
    strategy_ids: list[str] = Field(..., min_length=2, max_length=3)


class StrategyCompareResponse(BaseModel):
    """Strategy comparison response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    strategies: list[StrategyResponse]
    comparison_text: str
    created_at: datetime


class StrategyExplainRequest(BaseModel):
    """Request to explain a strategy."""
    question: str = Field(..., min_length=1, max_length=500)


class StrategyExplainResponse(BaseModel):
    """Strategy explanation response."""
    strategy_id: str
    question: str
    explanation: str

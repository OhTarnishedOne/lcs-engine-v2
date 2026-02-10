"""
Probability Lab Schemas

Pydantic models for prediction markets and calibration.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MarketResponse(BaseModel):
    """Prediction market details."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: Optional[str] = None
    category: str
    market_probability: Optional[float] = None  # Hidden until after prediction
    close_date: datetime
    is_resolved: bool = False
    resolution: Optional[str] = None
    explainer: Optional[str] = None
    investing_connection: Optional[str] = None


class MarketListResponse(BaseModel):
    """List of prediction markets."""
    markets: list[MarketResponse]
    total: int


class SubmitPredictionRequest(BaseModel):
    """Request to submit a prediction."""
    market_id: str
    probability: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = Field(default=None, max_length=1000)


class PredictionResponse(BaseModel):
    """User prediction with market details."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    market_id: str
    market_title: str
    predicted_probability: float
    market_probability: float  # Revealed after submission
    reasoning: Optional[str] = None
    brier_score: Optional[float] = None
    is_resolved: bool = False
    resolution: Optional[str] = None
    created_at: datetime


class PredictionListResponse(BaseModel):
    """List of user predictions."""
    predictions: list[PredictionResponse]
    total: int


class BiasInfo(BaseModel):
    """Cognitive bias information."""
    name: str
    description: str
    tip: str
    investing_connection: str


class CalibrationBucket(BaseModel):
    """Calibration data for a probability bucket."""
    bucket_start: float
    bucket_end: float
    predicted_avg: float
    actual_rate: float
    count: int


class CalibrationResponse(BaseModel):
    """User calibration and bias report."""
    total_predictions: int
    resolved_predictions: int
    average_brier_score: Optional[float] = None
    calibration_curve: list[CalibrationBucket]
    detected_biases: list[BiasInfo]

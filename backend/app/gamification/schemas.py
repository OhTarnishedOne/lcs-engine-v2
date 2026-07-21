"""Pydantic schemas for the gamification API."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TrendDirection(str, Enum):
    improving = "improving"
    stable = "stable"
    declining = "declining"


class CalibrationScoreResponse(BaseModel):
    user_id: UUID
    calibration_score: Optional[float] = Field(
        None, description="User-facing 0–100 score. Null until minimum sample met."
    )
    brier_score: Optional[float] = Field(
        None, description="Raw Brier score (0 = perfect, lower is better)."
    )
    score_family: Optional[str] = Field(
        None, description="Current score family / tier name."
    )
    trend: Optional[TrendDirection] = None
    resolved_predictions: int
    minimum_sample_met: bool
    last_updated: Optional[datetime] = None


class ScoreHistoryPoint(BaseModel):
    date: datetime
    calibration_score: Optional[float]
    brier_score: Optional[float]
    predictions_resolved: int


class FamilyTransition(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date: datetime
    from_family: str = Field(alias="from")
    to_family: str = Field(alias="to")


class ScoreHistoryResponse(BaseModel):
    user_id: UUID
    period: str
    points: list[ScoreHistoryPoint]
    score_family_transitions: list[FamilyTransition]


class EarnedBadge(BaseModel):
    badge_id: str
    name: str
    earned_at: datetime
    criteria_summary: str


class InProgressBadge(BaseModel):
    badge_id: str
    name: str
    progress: float = Field(ge=0.0, le=1.0)
    criteria_summary: str


class BadgesResponse(BaseModel):
    earned: list[EarnedBadge]
    in_progress: list[InProgressBadge]


class EvaluateRequest(BaseModel):
    prediction_id: UUID


class EvaluateResponse(BaseModel):
    prediction_id: UUID
    brier_delta: Optional[float] = Field(
        None, description="Change in rolling Brier score from this resolution."
    )
    new_calibration_score: Optional[float]
    family_changed: bool
    new_family: Optional[str] = None
    badges_awarded: list[str] = []

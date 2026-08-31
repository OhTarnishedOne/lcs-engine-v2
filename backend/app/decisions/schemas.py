"""Pydantic schemas for the canonical Decision API."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.gamification import DecisionDomain, OutcomeSource


class DecisionCreateRequest(BaseModel):
    question: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    domain: DecisionDomain = DecisionDomain.INVESTING
    reasoning: Optional[str] = None
    falsification: Optional[str] = None
    resolution_date: Optional[datetime] = None
    is_curated: bool = False
    question_id: Optional[UUID] = None
    lock: bool = True


class DecisionUpdateRequest(BaseModel):
    """
    Partial update. `confidence`, `reasoning`, and `falsification` are the
    locked forecast fields — editing any of them on a locked decision is
    rejected with HTTP 400.
    """

    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    falsification: Optional[str] = None
    resolution_date: Optional[datetime] = None


class DecisionResolveRequest(BaseModel):
    outcome_binary: bool
    outcome_source: OutcomeSource = OutcomeSource.SELF_REPORTED
    outcome_notes: Optional[str] = None


class DecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question: str
    domain: DecisionDomain
    confidence: float
    reasoning: Optional[str] = None
    falsification: Optional[str] = None
    status: str
    is_curated: bool = False
    locked_at: Optional[datetime] = None
    resolution_date: Optional[datetime] = None
    outcome_binary: Optional[bool] = None
    outcome_source: Optional[str] = None
    outcome_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    brier_score: Optional[float] = None
    calibration_delta: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DecisionListResponse(BaseModel):
    total: int
    decisions: list[DecisionResponse]


class DecisionResolveResponse(BaseModel):
    decision_id: UUID
    already_resolved: bool
    brier_score: Optional[float] = None
    is_calibrated: Optional[bool] = None
    calibration_score: Optional[float] = None
    tier: Optional[str] = None
    tier_advanced: bool = False
    badges_awarded: list[str] = []


class ReviewCreateRequest(BaseModel):
    outcome_attribution: Optional[str] = None
    was_process_sound: Optional[bool] = None
    identified_bias: Optional[str] = None
    luck_vs_process: Optional[str] = Field(
        default=None, description='"luck", "process", or "both".'
    )
    thesis_revised: bool = False
    self_flagged_bias_before_ai: bool = False
    triggers_avoided_revenge: bool = False


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    decision_id: UUID
    outcome_attribution: Optional[str] = None
    was_process_sound: Optional[bool] = None
    identified_bias: Optional[str] = None
    luck_vs_process: Optional[str] = None
    thesis_revised: bool = False
    self_flagged_bias_before_ai: bool = False
    reflection_points: int = 0
    triggers_good_loser: bool = False
    triggers_humble_winner: bool = False
    triggers_avoided_revenge: bool = False
    created_at: Optional[datetime] = None


class ReviewSubmitResponse(BaseModel):
    review: ReviewResponse
    reflection_score: Optional[float] = None
    badges_awarded: list[str] = []


class JournalEntry(BaseModel):
    decision: DecisionResponse
    review: Optional[ReviewResponse] = None


class JournalResponse(BaseModel):
    total: int
    entries: list[JournalEntry]


class WeaknessSignalResponse(BaseModel):
    slug: str
    title: str
    severity: float
    detail: str
    sample_size: int
    metric: dict = {}


class DiagnosisResponse(BaseModel):
    state: str = Field(description='"building" or "active".')
    resolved_count: int
    primary_weakness: Optional[str] = None
    summary: str
    signals: list[WeaknessSignalResponse] = []

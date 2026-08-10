"""Pydantic schemas for the training-intervention API."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InterventionStartRequest(BaseModel):
    # Optional: if omitted, the current diagnosis' primary weakness is used.
    weakness_slug: Optional[str] = None


class InterventionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    weakness_slug: str
    intervention_type: str
    title: str
    description: str
    target_count: int
    progress_count: int
    status: str
    metric_key: Optional[str] = None
    baseline_metric: Optional[float] = None
    post_metric: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class InterventionStartResponse(BaseModel):
    created: bool
    intervention: InterventionResponse


class InterventionListResponse(BaseModel):
    total: int
    interventions: list[InterventionResponse]

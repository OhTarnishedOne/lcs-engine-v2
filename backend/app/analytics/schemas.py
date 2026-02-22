from pydantic import BaseModel, Field
from typing import Optional


class AnalyticsEventPayload(BaseModel):
    event_name: str
    event_properties: Optional[dict] = None
    path: Optional[str] = None
    duration_ms: Optional[int] = None


class AnalyticsEventBatch(BaseModel):
    session_id: str
    events: list[AnalyticsEventPayload] = Field(..., max_length=50)


class AnalyticsEventResponse(BaseModel):
    accepted: int
    rejected: int

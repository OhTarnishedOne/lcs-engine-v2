from typing import Optional
from pydantic import BaseModel


class DistributionItem(BaseModel):
    value: Optional[str] = None
    count: int


class OnboardingStatsResponse(BaseModel):
    total_started: int
    total_completed: int
    completion_rate: float

    persona_distribution: list[DistributionItem]
    experience_level_distribution: list[DistributionItem]
    biggest_barrier_distribution: list[DistributionItem]
    primary_goal_distribution: list[DistributionItem]

    avg_completion_seconds: Optional[float] = None

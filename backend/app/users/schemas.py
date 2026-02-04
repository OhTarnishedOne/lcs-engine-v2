from pydantic import BaseModel, ConfigDict


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    risk_tolerance: str | None = None
    investment_horizon: str | None = None
    experience_level: str | None = None
    goals: list[str] | None = None
    interests: list[str] | None = None
    onboarding_complete: bool = False


class ProfileUpdate(BaseModel):
    risk_tolerance: str | None = None
    investment_horizon: str | None = None
    experience_level: str | None = None
    goals: list[str] | None = None
    interests: list[str] | None = None


class OnboardingData(BaseModel):
    risk_tolerance: str
    investment_horizon: str
    experience_level: str
    goals: list[str]
    interests: list[str] | None = None

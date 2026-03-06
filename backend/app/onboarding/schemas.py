from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, field_validator


# === Question/Section Schemas ===

class QuestionOption(BaseModel):
    value: Any
    label: str
    emoji: Optional[str] = None


class Question(BaseModel):
    key: str
    text: str
    type: str  # "single_select", "multi_select", "boolean", "text"
    required: bool = True
    order: int
    options: Optional[list[QuestionOption]] = None
    placeholder: Optional[str] = None
    conditional: Optional[dict[str, Any]] = None


class Section(BaseModel):
    section: int
    title: str
    subtitle: str
    questions: list[Question]


class OnboardingQuestionsResponse(BaseModel):
    sections: list[Section]
    total_questions: int


class SingleSectionResponse(BaseModel):
    section: Section
    total_sections: int
    is_last_section: bool


# === Request Schemas ===

class SaveResponsesRequest(BaseModel):
    section: int
    responses: dict[str, Any]  # {question_key: answer_value}


class SaveSingleResponseRequest(BaseModel):
    question_key: str
    answer_value: Any


class SaveTapResponseRequest(BaseModel):
    key: str
    value: Any  # str or list[str]


class SaveSectionPathRequest(BaseModel):
    responses: dict[str, Any]  # {question_key: answer_value}


class CompleteOnboardingRequest(BaseModel):
    responses: dict[str, Any]  # All responses if submitting at once


# === Response Schemas ===

class SaveResponsesResponse(BaseModel):
    section: int
    saved_count: int
    next_section: Optional[int]
    is_complete: bool = False


class OnboardingProgressResponse(BaseModel):
    sections_completed: list[int]
    current_section: Optional[int]
    questions_answered: int
    total_questions: int
    percent_complete: int
    is_complete: bool
    tap_responses: Optional[dict] = None


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str

    # Section 1
    experience_level: Optional[str] = None
    current_situation: Optional[str] = None
    has_investment_account: Optional[bool] = None
    has_retirement_account: Optional[bool] = None

    # Section 2
    barriers: Optional[list[str]] = None
    biggest_barrier: Optional[str] = None

    # Section 3
    primary_goal: Optional[str] = None
    specific_goal_description: Optional[str] = None
    time_horizon: Optional[str] = None

    # Section 4
    risk_tolerance: Optional[str] = None
    loss_reaction: Optional[str] = None
    monthly_investable: Optional[str] = None

    # Section 5
    learning_preference: Optional[str] = None
    time_commitment: Optional[str] = None
    interests: Optional[list[str]] = None

    # Conversation-derived
    motivation: Optional[str] = None
    life_context: Optional[str] = None
    emotional_relationship: Optional[str] = None
    goals: Optional[list[str]] = None

    # Computed
    persona: Optional[str] = None
    persona_description: Optional[str] = None
    recommended_path: Optional[str] = None

    # Status
    onboarding_completed: bool = False
    onboarding_completed_at: Optional[datetime] = None


class UpdateProfileRequest(BaseModel):
    """Partial update for editable profile fields."""
    primary_goal: Optional[str] = None
    specific_goal_description: Optional[str] = None
    time_horizon: Optional[str] = None
    risk_tolerance: Optional[str] = None
    monthly_investable: Optional[str] = None
    learning_preference: Optional[str] = None
    time_commitment: Optional[str] = None
    interests: Optional[list[str]] = None
    motivation: Optional[str] = None
    goals: Optional[list[str]] = None


class RawProfileResponse(BaseModel):
    """Canonical DB fields — editable raw values."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str

    # Section 1
    experience_level: Optional[str] = None
    current_situation: Optional[str] = None
    has_investment_account: Optional[bool] = None
    has_retirement_account: Optional[bool] = None

    # Section 2
    barriers: Optional[list[str]] = None
    biggest_barrier: Optional[str] = None

    # Section 3
    primary_goal: Optional[str] = None
    specific_goal_description: Optional[str] = None
    time_horizon: Optional[str] = None

    # Section 4
    risk_tolerance: Optional[str] = None
    loss_reaction: Optional[str] = None
    monthly_investable: Optional[str] = None

    # Section 5
    learning_preference: Optional[str] = None
    time_commitment: Optional[str] = None
    interests: Optional[list[str]] = None

    # Conversation-derived
    motivation: Optional[str] = None
    life_context: Optional[str] = None
    emotional_relationship: Optional[str] = None
    goals: Optional[list[str]] = None

    # Status
    onboarding_completed: bool = False
    onboarding_completed_at: Optional[datetime] = None


class DerivedProfileResponse(BaseModel):
    """Computed server-side from raw profile data. Never stored directly."""
    persona: Optional[str] = None
    persona_label: Optional[str] = None
    persona_description: Optional[str] = None
    recommended_path: Optional[str] = None

    experience_summary: Optional[str] = None
    goals_summary: Optional[str] = None
    risk_summary: Optional[str] = None
    interests_summary: Optional[str] = None
    learning_summary: Optional[str] = None
    about_you_summary: Optional[str] = None


class FullProfileResponse(BaseModel):
    """Combined raw + derived profile response."""
    raw: RawProfileResponse
    derived: DerivedProfileResponse


class PersonalizedTip(BaseModel):
    title: str
    description: str
    action: Optional[str] = None


class WelcomeResponse(BaseModel):
    greeting: str  # "Welcome! We're glad you're here."
    acknowledgment: str  # "You mentioned you're not sure where to start..."
    encouragement: str  # "That's exactly why we built LCS."
    recommended_action: str  # "start_basics" | "try_probability_lab" | "explore_strategies"
    recommended_action_label: str  # "Start with the Basics"
    recommended_action_description: str  # "A 5-minute intro to how investing works"
    personalized_tips: list[PersonalizedTip]
    persona: Optional[str] = None
    persona_description: Optional[str] = None


class OnboardingResponseRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_key: str
    question_text: str
    answer_value: str
    answer_display: str
    section: int
    question_order: int
    created_at: datetime


# === Conversational Onboarding Schemas ===

class OnboardingChatRequest(BaseModel):
    messages: list[dict]  # [{"role": "user"|"assistant", "content": "..."}]
    tap_responses: Optional[dict] = None


class OnboardingChatCompleteRequest(BaseModel):
    messages: list[dict]


class OnboardingConversationCompleteRequest(BaseModel):
    tap_responses: dict
    messages: list[dict]


VALID_EXPERIENCE_LEVELS = {"none", "beginner", "intermediate", "advanced"}
VALID_PRIMARY_GOALS = {"learn_basics", "start_investing", "grow_wealth", "retirement", "specific_goal", "side_income", "support_family", "understand_news"}
VALID_RISK_TOLERANCES = {"conservative", "moderate", "aggressive"}
VALID_INTERESTS = {"stocks", "etfs", "bonds", "crypto", "real_estate", "retirement", "options", "not_sure"}
VALID_LEARNING_PREFERENCES = {"read", "watch", "do", "discuss"}
VALID_LEARNING_STYLES = {"detailed", "concise", "examples", "actionable", "deep_dive"}


class ExtractedProfile(BaseModel):
    experience_level: str = "beginner"
    primary_goal: str = "learn_basics"
    risk_tolerance: str = "moderate"
    interests: list[str] = ["stocks", "etfs"]
    learning_preference: str = "do"
    goals: list[str] = ["learn_basics"]
    motivation: Optional[str] = None
    life_context: Optional[str] = None
    emotional_relationship: Optional[str] = None
    additional_context: Optional[str] = None

    @field_validator("experience_level")
    @classmethod
    def validate_experience_level(cls, v: str) -> str:
        if v in VALID_EXPERIENCE_LEVELS:
            return v
        return "beginner"

    @field_validator("primary_goal")
    @classmethod
    def validate_primary_goal(cls, v: str) -> str:
        if v in VALID_PRIMARY_GOALS:
            return v
        return "learn_basics"

    @field_validator("risk_tolerance")
    @classmethod
    def validate_risk_tolerance(cls, v: str) -> str:
        if v in VALID_RISK_TOLERANCES:
            return v
        return "moderate"

    @field_validator("interests")
    @classmethod
    def validate_interests(cls, v: list) -> list[str]:
        valid = [i for i in v if i in VALID_INTERESTS]
        return valid if valid else ["stocks", "etfs"]

    @field_validator("learning_preference")
    @classmethod
    def validate_learning_preference(cls, v: str) -> str:
        if v in VALID_LEARNING_PREFERENCES:
            return v
        return "do"

    @field_validator("goals")
    @classmethod
    def validate_goals(cls, v: list) -> list[str]:
        valid = [g for g in v if g in VALID_PRIMARY_GOALS]
        return valid if valid else ["learn_basics"]

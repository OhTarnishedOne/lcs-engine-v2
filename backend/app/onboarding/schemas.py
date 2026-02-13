from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


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

    # Computed
    persona: Optional[str] = None
    persona_description: Optional[str] = None
    recommended_path: Optional[str] = None

    # Status
    onboarding_completed: bool = False
    onboarding_completed_at: Optional[datetime] = None


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

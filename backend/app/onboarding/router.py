"""
Onboarding Router

Endpoints for the onboarding flow:
- Get questions (all or by section)
- Save responses (progressive or all at once)
- Complete onboarding
- Get progress
- Get profile
- Get personalized welcome
"""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..db.models import User
from ..config.onboarding_questions import get_total_questions
from .service import OnboardingService
from .schemas import (
    OnboardingQuestionsResponse,
    SingleSectionResponse,
    SaveResponsesRequest,
    SaveResponsesResponse,
    SaveSingleResponseRequest,
    SaveSectionPathRequest,
    CompleteOnboardingRequest,
    UpdateProfileRequest,
    UserProfileResponse,
    RawProfileResponse,
    FullProfileResponse,
    OnboardingProgressResponse,
    WelcomeResponse,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


def get_onboarding_service(db: Session = Depends(get_db)) -> OnboardingService:
    return OnboardingService(db)


def _build_user_profile_response(profile) -> UserProfileResponse:
    """Helper to build UserProfileResponse from a profile model."""
    return UserProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        experience_level=profile.experience_level,
        current_situation=profile.current_situation,
        has_investment_account=profile.has_investment_account,
        has_retirement_account=profile.has_retirement_account,
        barriers=profile.barriers,
        biggest_barrier=profile.biggest_barrier,
        primary_goal=profile.primary_goal,
        specific_goal_description=profile.specific_goal_description,
        time_horizon=profile.time_horizon,
        risk_tolerance=profile.risk_tolerance,
        loss_reaction=profile.loss_reaction,
        monthly_investable=profile.monthly_investable,
        learning_preference=profile.learning_preference,
        time_commitment=profile.time_commitment,
        interests=profile.interests,
        persona=profile.persona,
        persona_description=profile.persona_description,
        recommended_path=profile.recommended_path,
        onboarding_completed=profile.onboarding_completed,
        onboarding_completed_at=profile.onboarding_completed_at,
    )


def _build_raw_profile_response(profile) -> RawProfileResponse:
    """Helper to build RawProfileResponse from a profile model."""
    return RawProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        experience_level=profile.experience_level,
        current_situation=profile.current_situation,
        has_investment_account=profile.has_investment_account,
        has_retirement_account=profile.has_retirement_account,
        barriers=profile.barriers,
        biggest_barrier=profile.biggest_barrier,
        primary_goal=profile.primary_goal,
        specific_goal_description=profile.specific_goal_description,
        time_horizon=profile.time_horizon,
        risk_tolerance=profile.risk_tolerance,
        loss_reaction=profile.loss_reaction,
        monthly_investable=profile.monthly_investable,
        learning_preference=profile.learning_preference,
        time_commitment=profile.time_commitment,
        interests=profile.interests,
        onboarding_completed=profile.onboarding_completed,
        onboarding_completed_at=profile.onboarding_completed_at,
    )


@router.get("/questions", response_model=OnboardingQuestionsResponse)
def get_questions(
    section: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    service: OnboardingService = Depends(get_onboarding_service)
) -> OnboardingQuestionsResponse:
    """
    Get onboarding questions.

    - If `section` is provided, returns just that section.
    - Otherwise returns all sections.
    """
    sections = service.get_questions(section)
    return OnboardingQuestionsResponse(
        sections=sections,
        total_questions=get_total_questions()
    )


@router.get("/questions/{section_number}", response_model=SingleSectionResponse)
def get_section_questions(
    section_number: int,
    current_user: User = Depends(get_current_user),
    service: OnboardingService = Depends(get_onboarding_service)
) -> SingleSectionResponse:
    """Get questions for a specific section."""
    sections = service.get_questions(section_number)
    return SingleSectionResponse(
        section=sections[0],
        total_sections=5,
        is_last_section=(section_number == 5)
    )


@router.post("/responses", response_model=SaveResponsesResponse)
def save_responses(
    request: SaveResponsesRequest,
    current_user: User = Depends(get_current_user),
    service: OnboardingService = Depends(get_onboarding_service)
) -> SaveResponsesResponse:
    """
    Save responses for a section.

    This supports progressive onboarding where users save as they go.
    """
    saved_count, next_section = service.save_section(
        user_id=current_user.id,
        section=request.section,
        responses=request.responses
    )
    return SaveResponsesResponse(
        section=request.section,
        saved_count=saved_count,
        next_section=next_section,
        is_complete=(next_section is None)
    )


@router.post("/sections/{section_number}", response_model=SaveResponsesResponse)
def save_section_responses(
    section_number: int,
    request: SaveSectionPathRequest,
    current_user: User = Depends(get_current_user),
    service: OnboardingService = Depends(get_onboarding_service)
) -> SaveResponsesResponse:
    """Save responses for a section using path parameter."""
    saved_count, next_section = service.save_section(
        user_id=current_user.id,
        section=section_number,
        responses=request.responses
    )
    return SaveResponsesResponse(
        section=section_number,
        saved_count=saved_count,
        next_section=next_section,
        is_complete=(next_section is None)
    )


@router.post("/response", response_model=dict)
def save_single_response(
    request: SaveSingleResponseRequest,
    current_user: User = Depends(get_current_user),
    service: OnboardingService = Depends(get_onboarding_service)
) -> dict:
    """Save a single question response."""
    response = service.save_response(
        user_id=current_user.id,
        question_key=request.question_key,
        answer_value=request.answer_value
    )
    return {
        "question_key": response.question_key,
        "saved": True
    }


@router.post("/complete", response_model=UserProfileResponse)
def complete_onboarding(
    request: Optional[CompleteOnboardingRequest] = None,
    current_user: User = Depends(get_current_user),
    service: OnboardingService = Depends(get_onboarding_service)
) -> UserProfileResponse:
    """
    Finalize onboarding and generate profile.

    Can optionally include all responses in the request body,
    or rely on previously saved responses.
    """
    responses = request.responses if request else None
    profile = service.complete_onboarding(
        user_id=current_user.id,
        all_responses=responses
    )
    return _build_user_profile_response(profile)


@router.get("/progress", response_model=OnboardingProgressResponse)
def get_progress(
    current_user: User = Depends(get_current_user),
    service: OnboardingService = Depends(get_onboarding_service)
) -> OnboardingProgressResponse:
    """Get onboarding progress."""
    return service.get_onboarding_progress(current_user.id)


@router.get("/profile", response_model=FullProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    service: OnboardingService = Depends(get_onboarding_service)
) -> FullProfileResponse:
    """Get user's profile with raw fields and derived summaries."""
    profile = service.get_profile(current_user.id)
    if not profile:
        from ..common.errors import NotFoundError
        raise NotFoundError("Profile not found. Please complete onboarding first.")

    raw = _build_raw_profile_response(profile)
    derived = service.compute_derived_profile(profile)
    return FullProfileResponse(raw=raw, derived=derived)


@router.patch("/profile", response_model=FullProfileResponse)
def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    service: OnboardingService = Depends(get_onboarding_service)
) -> FullProfileResponse:
    """Update editable raw profile fields. Recomputes derived profile."""
    profile = service.get_profile(current_user.id)
    if not profile:
        from ..common.errors import NotFoundError
        raise NotFoundError("Profile not found. Please complete onboarding first.")

    updates = request.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(profile, field, value)

    # Recompute persona after raw field changes
    persona, persona_desc = service._generate_persona(profile)
    profile.persona = persona
    profile.persona_description = persona_desc

    db = service.db
    db.commit()
    db.refresh(profile)

    raw = _build_raw_profile_response(profile)
    derived = service.compute_derived_profile(profile)
    return FullProfileResponse(raw=raw, derived=derived)


@router.get("/welcome", response_model=WelcomeResponse)
def get_welcome(
    current_user: User = Depends(get_current_user),
    service: OnboardingService = Depends(get_onboarding_service)
) -> WelcomeResponse:
    """
    Get personalized welcome message and recommendations.

    Only available after completing onboarding.
    """
    return service.get_personalized_welcome(current_user.id)

"""
Onboarding Router

Endpoints for the onboarding flow:
- Get questions (all or by section)
- Save responses (progressive or all at once)
- Complete onboarding
- Get progress
- Get profile
- Get personalized welcome
- Conversational AI onboarding (chat, complete, skip)
- Hybrid tap+chat (complete-conversation)
"""

import json
import logging
from datetime import datetime, UTC
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user, get_ai_client
from ..db.models import User, UserProfile
from ..integrations import ResilientAIClient
from ..config.onboarding_questions import get_total_questions
from .service import OnboardingService
from .schemas import (
    OnboardingQuestionsResponse,
    SingleSectionResponse,
    SaveResponsesRequest,
    SaveResponsesResponse,
    SaveSingleResponseRequest,
    SaveTapResponseRequest,
    SaveSectionPathRequest,
    CompleteOnboardingRequest,
    UpdateProfileRequest,
    UserProfileResponse,
    RawProfileResponse,
    FullProfileResponse,
    OnboardingProgressResponse,
    WelcomeResponse,
    OnboardingChatRequest,
    OnboardingChatCompleteRequest,
    OnboardingConversationCompleteRequest,
    ExtractedProfile,
)
from .coverage import compute_coverage, get_completion_status, REQUIRED_TOPICS
from .prompts import (
    ONBOARDING_CHAT_SYSTEM_PROMPT,
    ONBOARDING_EXTRACTION_PROMPT,
    COMPLETION_INSTRUCTION_CONTINUE,
    COMPLETION_INSTRUCTION_WRAP_UP,
)

logger = logging.getLogger(__name__)

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
        barriers=_coerce_to_list(profile.barriers),
        biggest_barrier=profile.biggest_barrier,
        primary_goal=profile.primary_goal,
        specific_goal_description=profile.specific_goal_description,
        time_horizon=profile.time_horizon,
        risk_tolerance=profile.risk_tolerance,
        loss_reaction=profile.loss_reaction,
        monthly_investable=profile.monthly_investable,
        learning_preference=profile.learning_preference,
        time_commitment=profile.time_commitment,
        interests=_coerce_to_list(profile.interests),
        motivation=profile.motivation,
        life_context=profile.life_context,
        emotional_relationship=profile.emotional_relationship,
        goals=_coerce_to_list(profile.goals),
        persona=profile.persona,
        persona_description=profile.persona_description,
        recommended_path=profile.recommended_path,
        onboarding_completed=profile.onboarding_completed,
        onboarding_completed_at=profile.onboarding_completed_at,
    )


def _coerce_to_list(value) -> list[str] | None:
    """Coerce a DB value to list[str]. Handles single strings stored without JSON array wrapper."""
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value]
    return None


def _build_raw_profile_response(profile) -> RawProfileResponse:
    """Helper to build RawProfileResponse from a profile model."""
    return RawProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        experience_level=profile.experience_level,
        current_situation=profile.current_situation,
        has_investment_account=profile.has_investment_account,
        has_retirement_account=profile.has_retirement_account,
        barriers=_coerce_to_list(profile.barriers),
        biggest_barrier=profile.biggest_barrier,
        primary_goal=profile.primary_goal,
        specific_goal_description=profile.specific_goal_description,
        time_horizon=profile.time_horizon,
        risk_tolerance=profile.risk_tolerance,
        loss_reaction=profile.loss_reaction,
        monthly_investable=profile.monthly_investable,
        learning_preference=profile.learning_preference,
        time_commitment=profile.time_commitment,
        interests=_coerce_to_list(profile.interests),
        motivation=profile.motivation,
        life_context=profile.life_context,
        emotional_relationship=profile.emotional_relationship,
        goals=_coerce_to_list(profile.goals),
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


@router.post("/save-tap-response")
def save_tap_response(
    request: SaveTapResponseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Save a single tap screen response to the user profile's tap_responses JSON."""
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()

    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    existing = dict(profile.tap_responses or {})
    existing[request.key] = request.value
    profile.tap_responses = existing

    db.commit()

    return {"saved": True, "completed_screens": len(existing)}


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


# =============================================================
# Conversational AI Onboarding Endpoints
# =============================================================

def _format_tap_context(tap_responses: dict | None) -> dict:
    """Format tap responses into display strings for the system prompt."""
    if not tap_responses:
        return {
            "experience": "not provided",
            "goals": "not provided",
            "risk": "not provided",
            "interests": "not provided",
            "learning_style": "not provided",
        }

    return {
        "experience": tap_responses.get("experience_level", "not provided"),
        "goals": ", ".join(tap_responses["goals"]) if isinstance(tap_responses.get("goals"), list) else tap_responses.get("goals", "not provided"),
        "risk": tap_responses.get("risk_tolerance", "not provided"),
        "interests": ", ".join(tap_responses["interests"]) if isinstance(tap_responses.get("interests"), list) else tap_responses.get("interests", "not provided"),
        "learning_style": tap_responses.get("learning_style", "not provided"),
    }


@router.post("/chat")
async def onboarding_chat(
    request: OnboardingChatRequest,
    current_user: User = Depends(get_current_user),
    ai_client: ResilientAIClient = Depends(get_ai_client),
):
    """
    Conversational onboarding chat endpoint (streaming SSE).

    Send the full message history and receive a streamed AI response.
    The AI tutor asks deeper questions informed by tap screen responses.

    Response format:
    ```
    data: {"type": "start"}
    data: {"type": "token", "content": "Hello"}
    data: {"type": "done", "completion_status": "continue"|"wrap_up"}
    ```
    """
    messages = request.messages
    tap_responses = request.tap_responses

    # Compute topic coverage from user messages
    coverage = compute_coverage(messages)
    turn_count = sum(1 for m in messages if m.get("role") == "user")
    completion_status = get_completion_status(coverage, turn_count, messages)

    # Build dynamic system prompt
    covered = [t for t in REQUIRED_TOPICS if coverage.get(t, False)]
    uncovered = [t for t in REQUIRED_TOPICS if not coverage.get(t, False)]

    completion_instruction = (
        COMPLETION_INSTRUCTION_WRAP_UP
        if completion_status == "wrap_up"
        else COMPLETION_INSTRUCTION_CONTINUE
    )

    # Format tap context for the system prompt
    tap_context = _format_tap_context(tap_responses)

    system_prompt = ONBOARDING_CHAT_SYSTEM_PROMPT.format(
        experience=tap_context["experience"],
        goals=tap_context["goals"],
        risk=tap_context["risk"],
        interests=tap_context["interests"],
        learning_style=tap_context["learning_style"],
        uncovered_topics=", ".join(uncovered) if uncovered else "none",
        covered_topics=", ".join(covered) if covered else "none",
        completion_instruction=completion_instruction,
    )

    # Format messages for the AI client (only role + content)
    ai_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]

    async def event_stream():
        try:
            yield f"data: {json.dumps({'type': 'start'})}\n\n"

            async for chunk in ai_client.chat_stream(
                messages=ai_messages,
                system_prompt=system_prompt,
                max_tokens=512,
            ):
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'completion_status': completion_status})}\n\n"
        except Exception as e:
            logger.error(f"Onboarding chat stream error: {type(e).__name__}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': 'Something went wrong. Please try again.'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# Map extraction values to UserProfile DB values
EXPERIENCE_LEVEL_MAP = {
    "none": "never",
    "a_little": "beginner",
    "some": "intermediate",
    "regular": "advanced",
    # Also accept direct DB values
    "never": "never",
    "beginner": "beginner",
    "intermediate": "intermediate",
    "advanced": "advanced",
}

LEARNING_STYLE_MAP = {
    "detailed": "read",
    "examples": "do",
    "actionable": "watch",
    "deep_dive": "discuss",
    # Also accept direct DB values
    "read": "read",
    "watch": "watch",
    "do": "do",
    "discuss": "discuss",
}

RISK_TOLERANCE_MAP = {
    "conservative": "conservative",
    "moderate": "moderate",
    "aggressive": "aggressive",
}


@router.post("/chat/complete")
async def onboarding_chat_complete(
    request: OnboardingChatCompleteRequest,
    current_user: User = Depends(get_current_user),
    ai_client: ResilientAIClient = Depends(get_ai_client),
    db: Session = Depends(get_db),
):
    """
    Extract structured profile from onboarding conversation transcript.
    (Legacy endpoint — kept for backward compatibility.)

    Calls Claude to extract profile data, validates it, creates UserProfile,
    and marks onboarding as complete.
    """
    try:
        # Build transcript text from messages
        transcript_lines = []
        for msg in request.messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            transcript_lines.append(f"{role}: {content}")
        transcript_text = "\n".join(transcript_lines)

        # Call AI to extract profile
        extracted_data = await ai_client.chat_json(
            messages=[{"role": "user", "content": transcript_text}],
            system_prompt=ONBOARDING_EXTRACTION_PROMPT,
        )

        # Validate with Pydantic (coerces invalid values to defaults)
        extracted = ExtractedProfile(**extracted_data)

        # Get or create UserProfile
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()

        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)

        # Map extracted fields to DB model
        profile.experience_level = EXPERIENCE_LEVEL_MAP.get(
            extracted.experience_level, "beginner"
        )
        profile.primary_goal = extracted.primary_goal
        profile.risk_tolerance = extracted.risk_tolerance
        profile.interests = extracted.interests
        profile.learning_preference = extracted.learning_preference

        # Set reasonable defaults for fields not extracted via chat
        profile.barriers = ["none"]
        profile.biggest_barrier = None
        profile.time_horizon = "3_to_5_years"
        profile.monthly_investable = "not_sure"
        profile.loss_reaction = "wait_and_see"
        profile.current_situation = None
        profile.time_commitment = "flexible"
        profile.has_investment_account = False
        profile.has_retirement_account = False

        # Store conversation-derived fields
        profile.motivation = extracted.motivation
        profile.life_context = extracted.life_context
        profile.emotional_relationship = extracted.emotional_relationship

        # Generate persona using existing service logic
        service = OnboardingService(db)
        persona, persona_desc = service._generate_persona(profile)
        profile.persona = persona
        profile.persona_description = persona_desc

        # Mark onboarding complete
        profile.onboarding_completed = True
        profile.onboarding_completed_at = datetime.now(UTC)

        db.commit()
        db.refresh(profile)

        # Build response dict
        profile_dict = {
            "experience_level": profile.experience_level,
            "primary_goal": profile.primary_goal,
            "risk_tolerance": profile.risk_tolerance,
            "interests": profile.interests,
            "learning_preference": profile.learning_preference,
            "persona": profile.persona,
            "additional_context": extracted.additional_context,
        }

        return {"ok": True, "profile": profile_dict}

    except Exception as e:
        logger.error(f"Onboarding extraction failed: {type(e).__name__}: {e}")
        return {"ok": False, "error": "extraction_failed"}


@router.post("/complete-conversation")
async def complete_conversation(
    request: OnboardingConversationCompleteRequest,
    current_user: User = Depends(get_current_user),
    ai_client: ResilientAIClient = Depends(get_ai_client),
    db: Session = Depends(get_db),
):
    """
    Complete the hybrid tap+chat onboarding.

    Merges structured tap data with AI-extracted conversation data.
    Tap data → experience_level, primary_goal, goals, risk_tolerance, interests, learning_preference
    Extracted data → motivation, life_context, emotional_relationship
    """
    tap = request.tap_responses
    messages = request.messages

    try:
        # Extract conversation-derived fields (if there are messages)
        extracted_motivation = None
        extracted_life_context = None
        extracted_emotional_relationship = None

        if messages and any(m.get("role") == "user" for m in messages):
            try:
                transcript_lines = []
                for msg in messages:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    transcript_lines.append(f"{role}: {content}")
                transcript_text = "\n".join(transcript_lines)

                extracted_data = await ai_client.chat_json(
                    messages=[{"role": "user", "content": transcript_text}],
                    system_prompt=ONBOARDING_EXTRACTION_PROMPT,
                )

                extracted_motivation = extracted_data.get("motivation")
                extracted_life_context = extracted_data.get("life_context")
                extracted_emotional_relationship = extracted_data.get("emotional_relationship")
            except Exception as e:
                logger.warning(f"Conversation extraction failed, using tap data only: {e}")

        # Get or create UserProfile
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()

        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)

        # Map tap data to DB fields
        experience_raw = tap.get("experience_level", "a_little")
        profile.experience_level = EXPERIENCE_LEVEL_MAP.get(experience_raw, "beginner")

        # Goals: first selected → primary_goal, all stored as goals JSON
        tap_goals = tap.get("goals", ["learn_basics"])
        if isinstance(tap_goals, list) and tap_goals:
            profile.primary_goal = tap_goals[0]
            profile.goals = tap_goals
        else:
            profile.primary_goal = "learn_basics"
            profile.goals = ["learn_basics"]

        profile.risk_tolerance = RISK_TOLERANCE_MAP.get(
            tap.get("risk_tolerance", "moderate"), "moderate"
        )

        tap_interests = tap.get("interests", ["stocks", "etfs"])
        profile.interests = tap_interests if isinstance(tap_interests, list) else ["stocks", "etfs"]

        learning_style_raw = tap.get("learning_style", "examples")
        profile.learning_preference = LEARNING_STYLE_MAP.get(learning_style_raw, "do")

        # Set reasonable defaults for fields not in tap flow
        profile.barriers = ["none"]
        profile.biggest_barrier = None
        profile.time_horizon = "3_to_5_years"
        profile.monthly_investable = "not_sure"
        profile.loss_reaction = "wait_and_see"
        profile.current_situation = None
        profile.time_commitment = "flexible"
        profile.has_investment_account = False
        profile.has_retirement_account = False

        # Store conversation-derived fields
        profile.motivation = extracted_motivation
        profile.life_context = extracted_life_context
        profile.emotional_relationship = extracted_emotional_relationship

        # Generate persona
        service = OnboardingService(db)
        persona, persona_desc = service._generate_persona(profile)
        profile.persona = persona
        profile.persona_description = persona_desc

        # Mark onboarding complete
        profile.onboarding_completed = True
        profile.onboarding_completed_at = datetime.now(UTC)

        db.commit()
        db.refresh(profile)

        return {"ok": True, "profile": {
            "experience_level": profile.experience_level,
            "primary_goal": profile.primary_goal,
            "risk_tolerance": profile.risk_tolerance,
            "interests": profile.interests,
            "learning_preference": profile.learning_preference,
            "persona": profile.persona,
            "motivation": profile.motivation,
            "life_context": profile.life_context,
            "emotional_relationship": profile.emotional_relationship,
        }}

    except Exception as e:
        logger.error(f"Complete conversation failed: {type(e).__name__}: {e}")
        return {"ok": False, "error": "completion_failed"}


@router.post("/skip")
async def skip_onboarding(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Skip onboarding and create profile with safe defaults.
    """
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()

    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    # Set safe defaults
    profile.experience_level = "beginner"
    profile.primary_goal = "learn_basics"
    profile.risk_tolerance = "moderate"
    profile.interests = ["stocks", "etfs"]
    profile.learning_preference = "do"
    profile.barriers = ["none"]
    profile.biggest_barrier = None
    profile.time_horizon = "3_to_5_years"
    profile.monthly_investable = "not_sure"
    profile.loss_reaction = "wait_and_see"
    profile.current_situation = None
    profile.time_commitment = "flexible"
    profile.has_investment_account = False
    profile.has_retirement_account = False
    profile.goals = ["learn_basics"]

    # Generate persona
    service = OnboardingService(db)
    persona, persona_desc = service._generate_persona(profile)
    profile.persona = persona
    profile.persona_description = persona_desc

    profile.onboarding_completed = True
    profile.onboarding_completed_at = datetime.now(UTC)

    db.commit()

    return {"ok": True}

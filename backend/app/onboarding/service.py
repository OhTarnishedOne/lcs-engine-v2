"""
Onboarding Service

Handles all onboarding business logic including:
- Question retrieval and validation
- Response saving (progressive or all-at-once)
- Profile creation and persona generation
- Personalized welcome message generation
"""

import json
from datetime import datetime, UTC
from typing import Any, Optional

from sqlalchemy.orm import Session

from ..db.models import User, UserProfile, OnboardingResponse
from ..config.onboarding_questions import (
    ONBOARDING_SECTIONS,
    BARRIER_DESCRIPTIONS,
    PERSONA_DEFINITIONS,
    get_section,
    get_question_by_key,
    get_option_label,
    get_total_questions,
    get_required_question_keys,
)
from ..common.errors import BadRequestError, NotFoundError
from .schemas import (
    Section,
    Question,
    QuestionOption,
    OnboardingProgressResponse,
    WelcomeResponse,
    PersonalizedTip,
)


class OnboardingService:
    def __init__(self, db: Session):
        self.db = db

    def get_questions(self, section: Optional[int] = None) -> list[Section]:
        """
        Return onboarding questions.
        If section specified, return just that section.
        Otherwise return all sections.
        """
        sections_to_return = []

        if section is not None:
            section_data = get_section(section)
            if not section_data:
                raise NotFoundError(f"Section {section} not found")
            sections_to_return = [section_data]
        else:
            sections_to_return = ONBOARDING_SECTIONS

        return [self._convert_section(s) for s in sections_to_return]

    def _convert_section(self, section_data: dict) -> Section:
        """Convert raw section dict to Section schema."""
        questions = []
        for q in section_data["questions"]:
            options = None
            if q.get("options") and q["options"] != "dynamic":
                options = [
                    QuestionOption(
                        value=opt["value"],
                        label=opt["label"],
                        emoji=opt.get("emoji")
                    )
                    for opt in q["options"]
                ]

            questions.append(Question(
                key=q["key"],
                text=q["text"],
                type=q["type"],
                required=q.get("required", True),
                order=q.get("order", 0),
                options=options,
                placeholder=q.get("placeholder"),
                conditional=q.get("conditional")
            ))

        return Section(
            section=section_data["section"],
            title=section_data["title"],
            subtitle=section_data["subtitle"],
            questions=questions
        )

    def save_response(
        self,
        user_id: str,
        question_key: str,
        answer_value: Any
    ) -> OnboardingResponse:
        """
        Save a single question response.
        Supports progressive onboarding (save as user goes).
        """
        result = get_question_by_key(question_key)
        if not result:
            raise BadRequestError(f"Unknown question key: {question_key}")

        question, section_num = result

        # Get display value
        if isinstance(answer_value, list):
            display_parts = [get_option_label(question_key, v) or str(v) for v in answer_value]
            answer_display = ", ".join(display_parts)
            answer_str = json.dumps(answer_value)
        elif isinstance(answer_value, bool):
            answer_display = "Yes" if answer_value else "No"
            answer_str = json.dumps(answer_value)
        else:
            answer_display = get_option_label(question_key, answer_value) or str(answer_value)
            answer_str = str(answer_value)

        # Check if response already exists, update if so
        existing = self.db.query(OnboardingResponse).filter(
            OnboardingResponse.user_id == user_id,
            OnboardingResponse.question_key == question_key
        ).first()

        if existing:
            existing.answer_value = answer_str
            existing.answer_display = answer_display
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Create new response
        response = OnboardingResponse(
            user_id=user_id,
            question_key=question_key,
            question_text=question["text"],
            answer_value=answer_str,
            answer_display=answer_display,
            section=section_num,
            question_order=question.get("order", 0)
        )
        self.db.add(response)
        self.db.commit()
        self.db.refresh(response)
        return response

    def save_section(
        self,
        user_id: str,
        section: int,
        responses: dict[str, Any]
    ) -> tuple[int, Optional[int]]:
        """
        Save all responses for a section at once.
        Returns (saved_count, next_section or None if complete)
        """
        section_data = get_section(section)
        if not section_data:
            raise BadRequestError(f"Invalid section: {section}")

        saved_count = 0
        for question in section_data["questions"]:
            key = question["key"]
            if key in responses:
                self.save_response(user_id, key, responses[key])
                saved_count += 1

        # Determine next section
        next_section = section + 1 if section < 5 else None

        return saved_count, next_section

    def complete_onboarding(
        self,
        user_id: str,
        all_responses: Optional[dict[str, Any]] = None
    ) -> UserProfile:
        """
        Finalize onboarding:
        1. If responses provided, save them all
        2. Validate all required questions answered
        3. Create/update UserProfile
        4. Generate persona
        5. Mark onboarding complete
        """
        # Save any provided responses
        if all_responses:
            for key, value in all_responses.items():
                if value is not None:
                    self.save_response(user_id, key, value)

        # Get all saved responses
        saved_responses = self.db.query(OnboardingResponse).filter(
            OnboardingResponse.user_id == user_id
        ).all()

        response_dict = {}
        for r in saved_responses:
            # Parse JSON values back
            try:
                response_dict[r.question_key] = json.loads(r.answer_value)
            except (json.JSONDecodeError, TypeError):
                response_dict[r.question_key] = r.answer_value

        # Validate required questions (basic validation)
        required_keys = get_required_question_keys()
        missing = [k for k in required_keys if k not in response_dict]
        if missing:
            raise BadRequestError(f"Missing required questions: {', '.join(missing)}")

        # Get or create user profile
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)

        # Populate profile from responses
        profile.experience_level = response_dict.get("experience_level")
        profile.current_situation = response_dict.get("current_situation")
        profile.has_investment_account = response_dict.get("has_investment_account")
        profile.has_retirement_account = response_dict.get("has_retirement_account")

        profile.barriers = response_dict.get("barriers")
        profile.biggest_barrier = response_dict.get("biggest_barrier")

        profile.primary_goal = response_dict.get("primary_goal")
        profile.specific_goal_description = response_dict.get("specific_goal_description")
        profile.time_horizon = response_dict.get("time_horizon")

        profile.risk_tolerance = response_dict.get("risk_tolerance")
        profile.loss_reaction = response_dict.get("loss_reaction")
        profile.monthly_investable = response_dict.get("monthly_investable")

        profile.learning_preference = response_dict.get("learning_preference")
        profile.time_commitment = response_dict.get("time_commitment")
        profile.interests = response_dict.get("interests")

        # Generate persona (rule-based for now, can be Claude-enhanced later)
        persona, persona_desc = self._generate_persona(profile)
        profile.persona = persona
        profile.persona_description = persona_desc

        profile.onboarding_completed = True
        profile.onboarding_completed_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(profile)

        return profile

    def _generate_persona(self, profile: UserProfile) -> tuple[str, str]:
        """
        Generate a persona based on profile.
        Uses rule-based logic. Can be enhanced with Claude later.
        """
        # Analyze key factors
        is_beginner = profile.experience_level in ("never", "curious")
        is_risk_averse = profile.risk_tolerance in ("very_conservative", "conservative")
        has_specific_goal = profile.primary_goal == "specific_goal"
        is_skeptical = "dont_trust_markets" in (profile.barriers or [])
        has_bad_experience = "bad_experience" in (profile.barriers or [])
        is_time_pressed = profile.time_commitment in ("5_min_daily", "30_min_weekly")
        wants_hands_on = profile.learning_preference == "do"

        # Determine persona
        if has_bad_experience:
            persona = "rebuilding_confidence"
        elif is_beginner and is_risk_averse:
            persona = "cautious_beginner"
        elif is_skeptical:
            persona = "skeptical_explorer"
        elif has_specific_goal:
            persona = "goal_focused"
        elif is_time_pressed:
            persona = "time_pressed"
        elif wants_hands_on or not is_beginner:
            persona = "eager_learner"
        else:
            persona = "cautious_beginner"

        persona_info = PERSONA_DEFINITIONS.get(persona, PERSONA_DEFINITIONS["cautious_beginner"])
        return persona, persona_info["description"]

    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user's profile."""
        return self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

    def get_personalized_welcome(self, user_id: str) -> WelcomeResponse:
        """
        Generate personalized welcome message and recommendations.
        Based on profile, addresses their biggest barrier and gives clear next step.
        """
        profile = self.get_profile(user_id)
        if not profile or not profile.onboarding_completed:
            raise BadRequestError("Onboarding not completed")

        # Get barrier-specific messaging
        biggest_barrier = profile.biggest_barrier
        if not biggest_barrier and profile.barriers:
            biggest_barrier = profile.barriers[0] if profile.barriers[0] != "none" else None

        if biggest_barrier and biggest_barrier in BARRIER_DESCRIPTIONS:
            barrier_info = BARRIER_DESCRIPTIONS[biggest_barrier]
            acknowledgment = barrier_info["acknowledgment"]
            encouragement = barrier_info["encouragement"]
        else:
            acknowledgment = "Thanks for sharing a bit about yourself"
            encouragement = "We're here to help you on your investing journey."

        # Determine recommended action based on profile
        if profile.experience_level in ("never", "curious"):
            recommended_action = "start_basics"
            recommended_action_label = "Start with the Basics"
            recommended_action_description = "A 5-minute intro to how investing works — no jargon, just clarity."
        elif profile.learning_preference == "do":
            recommended_action = "try_probability_lab"
            recommended_action_label = "Try the Probability Lab"
            recommended_action_description = "Practice making predictions and sharpen your decision-making skills."
        elif profile.primary_goal in ("retirement", "specific_goal"):
            recommended_action = "explore_strategies"
            recommended_action_label = "Explore Investment Strategies"
            recommended_action_description = "See personalized strategy recommendations based on your goals."
        else:
            recommended_action = "start_basics"
            recommended_action_label = "Start with the Basics"
            recommended_action_description = "Build a solid foundation before diving deeper."

        # Generate personalized tips
        tips = self._generate_tips(profile)

        return WelcomeResponse(
            greeting="Welcome! We're glad you're here.",
            acknowledgment=acknowledgment,
            encouragement=encouragement,
            recommended_action=recommended_action,
            recommended_action_label=recommended_action_label,
            recommended_action_description=recommended_action_description,
            personalized_tips=tips,
            persona=profile.persona,
            persona_description=profile.persona_description
        )

    def _generate_tips(self, profile: UserProfile) -> list[PersonalizedTip]:
        """Generate personalized tips based on profile."""
        tips = []

        # Tip based on learning preference
        if profile.learning_preference == "read":
            tips.append(PersonalizedTip(
                title="Reading materials ready",
                description="We've got articles and guides tailored to your level."
            ))
        elif profile.learning_preference == "watch":
            tips.append(PersonalizedTip(
                title="Video content available",
                description="Short, digestible videos to learn at your pace."
            ))
        elif profile.learning_preference == "do":
            tips.append(PersonalizedTip(
                title="Hands-on practice",
                description="Our paper trading simulator lets you practice risk-free."
            ))
        elif profile.learning_preference == "discuss":
            tips.append(PersonalizedTip(
                title="AI-powered chat",
                description="Ask questions anytime — our AI assistant is here to help."
            ))

        # Tip based on risk tolerance
        if profile.risk_tolerance in ("very_conservative", "conservative"):
            tips.append(PersonalizedTip(
                title="Start small, stay safe",
                description="We'll show you low-risk options that match your comfort level."
            ))

        # Tip based on time commitment
        if profile.time_commitment in ("5_min_daily", "30_min_weekly"):
            tips.append(PersonalizedTip(
                title="Bite-sized learning",
                description="All our lessons are designed for busy schedules."
            ))

        # Tip based on interests
        if profile.interests:
            if "crypto" in profile.interests:
                tips.append(PersonalizedTip(
                    title="Crypto basics included",
                    description="We cover cryptocurrency fundamentals and risks."
                ))
            elif "retirement" in profile.interests:
                tips.append(PersonalizedTip(
                    title="Retirement planning",
                    description="Learn about 401(k)s, IRAs, and long-term strategies."
                ))

        return tips[:4]  # Limit to 4 tips

    def get_onboarding_progress(self, user_id: str) -> OnboardingProgressResponse:
        """
        Return onboarding progress:
        - sections_completed
        - current_section
        - percent_complete
        """
        # Check if already completed
        profile = self.get_profile(user_id)
        if profile and profile.onboarding_completed:
            return OnboardingProgressResponse(
                sections_completed=[1, 2, 3, 4, 5],
                current_section=None,
                questions_answered=get_total_questions(),
                total_questions=get_total_questions(),
                percent_complete=100,
                is_complete=True
            )

        # Get all responses
        responses = self.db.query(OnboardingResponse).filter(
            OnboardingResponse.user_id == user_id
        ).all()

        # Group by section
        sections_with_responses: set[int] = set()
        for r in responses:
            sections_with_responses.add(r.section)

        # Determine completed sections (all required questions answered)
        sections_completed = []
        for section_data in ONBOARDING_SECTIONS:
            section_num = section_data["section"]
            section_responses = [r for r in responses if r.section == section_num]
            response_keys = {r.question_key for r in section_responses}

            # Check if all required questions for this section are answered
            required_keys = [
                q["key"] for q in section_data["questions"]
                if q.get("required", False) and "conditional" not in q
            ]

            if all(k in response_keys for k in required_keys):
                sections_completed.append(section_num)

        # Determine current section
        if not sections_completed:
            current_section = 1
        elif len(sections_completed) >= 5:
            current_section = None
        else:
            current_section = max(sections_completed) + 1

        # Calculate progress
        questions_answered = len(responses)
        total_questions = get_total_questions()
        percent_complete = int((questions_answered / total_questions) * 100) if total_questions > 0 else 0

        return OnboardingProgressResponse(
            sections_completed=sorted(sections_completed),
            current_section=current_section,
            questions_answered=questions_answered,
            total_questions=total_questions,
            percent_complete=min(percent_complete, 99),  # Cap at 99 until fully complete
            is_complete=False
        )

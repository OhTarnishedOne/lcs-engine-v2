"""
Reflection service — submit and fetch the review of a resolved decision.

Submitting a review is the "Reflect" step of the lifecycle: it records how the
user attributed the outcome, evaluates reflection badges (Good Loser, Humble
Winner, Avoided Revenge, Revised Thesis) via the badge evaluator, and refreshes
the reflection score family.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.gamification import (
    Decision,
    DecisionReview,
    DecisionStatus,
    UserGamificationProfile,
)
from app.services.gamification.badge_evaluator import (
    PointsBadgeEvaluator,
    PointsBadgeResult,
)
from app.services.gamification.score_family_updater import (
    ScoreFamilyUpdate,
    ScoreFamilyUpdater,
)


class DecisionNotResolvedError(Exception):
    """A review was submitted for a decision that has not resolved yet."""


class ReviewAlreadyExistsError(Exception):
    """A decision may only be reviewed once."""


@dataclass
class ReviewResult:
    review: DecisionReview
    badge_result: PointsBadgeResult
    score_update: ScoreFamilyUpdate


class ReviewService:
    def __init__(self, db: Session):
        self.db = db

    def _get_or_create_profile(self, user_id: UUID) -> UserGamificationProfile:
        profile = (
            self.db.query(UserGamificationProfile)
            .filter(UserGamificationProfile.user_id == user_id)
            .first()
        )
        if profile is None:
            profile = UserGamificationProfile(user_id=user_id)
            self.db.add(profile)
            self.db.flush()
        return profile

    def get_review(self, decision: Decision) -> Optional[DecisionReview]:
        return (
            self.db.query(DecisionReview)
            .filter(DecisionReview.decision_id == decision.id)
            .first()
        )

    def submit_review(
        self,
        decision: Decision,
        *,
        outcome_attribution: Optional[str] = None,
        was_process_sound: Optional[bool] = None,
        identified_bias: Optional[str] = None,
        luck_vs_process: Optional[str] = None,
        thesis_revised: bool = False,
        self_flagged_bias_before_ai: bool = False,
        triggers_avoided_revenge: bool = False,
    ) -> ReviewResult:
        if (
            decision.status != DecisionStatus.RESOLVED
            or decision.outcome_binary is None
        ):
            raise DecisionNotResolvedError(str(decision.id))

        if self.get_review(decision) is not None:
            raise ReviewAlreadyExistsError(str(decision.id))

        review = DecisionReview(
            decision_id=decision.id,
            user_id=decision.user_id,
            outcome_attribution=outcome_attribution,
            was_process_sound=was_process_sound,
            identified_bias=identified_bias,
            luck_vs_process=luck_vs_process,
            thesis_revised=thesis_revised,
            self_flagged_bias_before_ai=self_flagged_bias_before_ai,
            triggers_avoided_revenge=triggers_avoided_revenge,
        )
        self.db.add(review)
        self.db.flush()

        # Record which reflection archetypes this review represents, for the
        # journal (mirrors the conditions the badge evaluator scores on).
        outcome = bool(decision.outcome_binary)
        review.triggers_good_loser = (
            not outcome
            and was_process_sound is True
            and bool(outcome_attribution)
        )
        review.triggers_humble_winner = (
            outcome
            and was_process_sound is False
            and bool(outcome_attribution)
        )

        profile = self._get_or_create_profile(decision.user_id)

        badge_result = PointsBadgeEvaluator(self.db).on_review_submitted(
            review, decision, profile
        )
        review.reflection_points = badge_result.total_points_awarded

        score_update = ScoreFamilyUpdater(self.db).update_after_review(
            decision, review, profile
        )

        self.db.flush()

        return ReviewResult(
            review=review,
            badge_result=badge_result,
            score_update=score_update,
        )

# app/services/gamification/badge_evaluator.py
# v2 — all four fixes applied:
#   FIX #1: PROCESS_BUILDER uses correct BadgeSlug
#   FIX #2: Badge points only written when badge is newly earned
#   FIX #3: call_number passed explicitly to avoid event-order coupling
#   FIX #4: last_trend_bonus_at guards calibration trend bonus

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.gamification import (
    BadgeSlug,
    Decision,
    DecisionReview,
    DecisionStatus,
    InsightLoop,
    PointsLedger,
    UserBadge,
    UserGamificationProfile,
    UserScoreSnapshot,
)
from app.services.gamification.score_family_updater import ScoreFamilyUpdate


@dataclass
class PointsBadgeResult:
    user_id:              UUID
    total_points_awarded: int
    points_breakdown:     dict
    badges_earned:        list[BadgeSlug]
    streak_days:          int
    streak_updated:       bool
    streak_broken:        bool
    new_total_points:     int


class PointsBadgeEvaluator:

    POINTS = {
        "log_decision":          10,
        "add_reasoning":         20,
        "add_falsification":     15,
        "use_curated":            5,
        "ai_tutor_engagement":   10,
        "decision_resolved":     15,
        "calibrated_outcome":    25,
        "write_review":          20,
        "correct_attribution":   25,
        "self_flagged_bias":     30,
        "insight_loop_complete": 50,
        "bias_reduced":          75,
        "streak_7_day":          75,
        "streak_30_day":        300,
        "calibration_streak_5": 100,
        "calibration_trend":     40,
        "domain_transfer":       60,
    }

    BADGE_POINTS = {
        BadgeSlug.FIRST_CALL:             25,
        BadgeSlug.WHAT_WOULD_CHANGE:      50,
        BadgeSlug.PROCESS_BUILDER:        75,   # FIX #1
        BadgeSlug.SEVEN_DAY_STREAK:       75,
        BadgeSlug.THIRTY_DAY_STREAK:     300,
        BadgeSlug.CALIBRATED_RUN:        100,
        BadgeSlug.GOOD_LOSER:             75,
        BadgeSlug.HUMBLE_WINNER:          75,
        BadgeSlug.AVOIDED_REVENGE:        50,
        BadgeSlug.REVISED_THESIS:         40,
        BadgeSlug.BIAS_CORRECTED:         75,
        BadgeSlug.LOOP_CLOSED:           100,
        BadgeSlug.SKILL_TRANSFERRED:      60,
        BadgeSlug.STABLE_UNDER_PRESSURE: 250,
    }

    def __init__(self, db: Session):
        self.db = db

    # -----------------------------------------------------------------------
    # Event 1: Decision logged
    # -----------------------------------------------------------------------

    def on_decision_logged(
        self,
        decision: Decision,
        profile:  UserGamificationProfile,
    ) -> PointsBadgeResult:
        points = {}
        badges = []

        # Process points
        points["log_decision"] = self.POINTS["log_decision"]
        if decision.reasoning:
            points["add_reasoning"] = self.POINTS["add_reasoning"]
        if decision.falsification:
            points["add_falsification"] = self.POINTS["add_falsification"]
        if decision.is_curated:
            points["use_curated"] = self.POINTS["use_curated"]

        # Increment BEFORE badge checks so call_number is accurate
        # FIX #3: total_calls updated here, passed explicitly where needed
        profile.total_calls += 1

        # --- Badges (FIX #2: points only added when badge is NEW) ---

        # First Call
        if profile.total_calls == 1:
            if self._try_award_badge(
                profile.user_id, BadgeSlug.FIRST_CALL,
                decision.id, None, badges
            ):
                points["first_call_badge"] = self.BADGE_POINTS[BadgeSlug.FIRST_CALL]

        # What Would Change (5 decisions with falsification)
        if decision.falsification:
            count = (
                self.db.query(Decision)
                .filter(
                    Decision.user_id == decision.user_id,
                    Decision.falsification.isnot(None),
                )
                .count()
            )
            if count >= 5:
                if self._try_award_badge(
                    profile.user_id, BadgeSlug.WHAT_WOULD_CHANGE,
                    decision.id, None, badges
                ):
                    points["what_would_change_badge"] = self.BADGE_POINTS[BadgeSlug.WHAT_WOULD_CHANGE]

        # Process Builder (10 decisions with BOTH reasoning AND falsification)
        # FIX #1: uses PROCESS_BUILDER not WHAT_WOULD_CHANGE
        if decision.reasoning and decision.falsification:
            full_count = (
                self.db.query(Decision)
                .filter(
                    Decision.user_id == decision.user_id,
                    Decision.reasoning.isnot(None),
                    Decision.falsification.isnot(None),
                )
                .count()
            )
            if full_count >= 10:
                if self._try_award_badge(
                    profile.user_id, BadgeSlug.PROCESS_BUILDER,
                    decision.id, None, badges
                ):
                    points["process_builder_badge"] = self.BADGE_POINTS[BadgeSlug.PROCESS_BUILDER]

        # Streak
        streak_updated, streak_broken = self._update_streak(profile)
        streak_points = self._check_streak_badges(profile, decision.id, badges)
        points.update(streak_points)

        total = self._commit_points(profile, points, "process", decision.id, None)

        return PointsBadgeResult(
            user_id=profile.user_id,
            total_points_awarded=total,
            points_breakdown=points,
            badges_earned=badges,
            streak_days=profile.logging_streak_days,
            streak_updated=streak_updated,
            streak_broken=streak_broken,
            new_total_points=profile.total_points,
        )

    # -----------------------------------------------------------------------
    # Event 2: Decision resolved
    # -----------------------------------------------------------------------

    def on_decision_resolved(
        self,
        decision:      Decision,
        is_calibrated: bool,
        profile:       UserGamificationProfile,
        score_update:  ScoreFamilyUpdate,
    ) -> PointsBadgeResult:
        points = {}
        badges = []

        points["decision_resolved"] = self.POINTS["decision_resolved"]

        if is_calibrated:
            points["calibrated_outcome"] = self.POINTS["calibrated_outcome"]
            profile.calibration_streak += 1

            if profile.calibration_streak >= 5:
                # FIX #2: only add points if badge is newly earned
                if self._try_award_badge(
                    profile.user_id, BadgeSlug.CALIBRATED_RUN,
                    decision.id, None, badges
                ):
                    points["calibration_streak_5"] = self.POINTS["calibration_streak_5"]
        else:
            profile.calibration_streak = 0

        # FIX #4: calibration trend is idempotent via last_trend_bonus_at
        if self._calibration_trending_up(decision.user_id, profile):
            points["calibration_trend"] = self.POINTS["calibration_trend"]

        # Milestone points from ScoreFamilyUpdate
        if score_update.milestone_points > 0:
            points.update(score_update.milestone_breakdown)

        total = self._commit_points(profile, points, "calibration", decision.id, None)

        return PointsBadgeResult(
            user_id=profile.user_id,
            total_points_awarded=total,
            points_breakdown=points,
            badges_earned=badges,
            streak_days=profile.logging_streak_days,
            streak_updated=False,
            streak_broken=False,
            new_total_points=profile.total_points,
        )

    # -----------------------------------------------------------------------
    # Event 3: Review submitted
    # -----------------------------------------------------------------------

    def on_review_submitted(
        self,
        review:   DecisionReview,
        decision: Decision,
        profile:  UserGamificationProfile,
    ) -> PointsBadgeResult:
        points = {}
        badges = []

        points["write_review"] = self.POINTS["write_review"]
        profile.reviewed_calls += 1

        if review.outcome_attribution and review.luck_vs_process:
            points["correct_attribution"] = self.POINTS["correct_attribution"]

        if review.self_flagged_bias_before_ai:
            points["self_flagged_bias"] = self.POINTS["self_flagged_bias"]

        outcome = bool(decision.outcome_binary)

        # Good Loser: WRONG call + SOUND process + honest review
        # FIX #2: points only if badge is newly earned
        if not outcome and review.was_process_sound is True and review.outcome_attribution:
            if self._try_award_badge(
                profile.user_id, BadgeSlug.GOOD_LOSER,
                decision.id, review.id, badges
            ):
                points["good_loser_badge"] = self.BADGE_POINTS[BadgeSlug.GOOD_LOSER]

        # Humble Winner: RIGHT call + WEAK process + honest admission
        if outcome and review.was_process_sound is False and review.outcome_attribution:
            if self._try_award_badge(
                profile.user_id, BadgeSlug.HUMBLE_WINNER,
                decision.id, review.id, badges
            ):
                points["humble_winner_badge"] = self.BADGE_POINTS[BadgeSlug.HUMBLE_WINNER]

        # Avoided Revenge
        if review.triggers_avoided_revenge:
            if self._try_award_badge(
                profile.user_id, BadgeSlug.AVOIDED_REVENGE,
                decision.id, review.id, badges
            ):
                points["avoided_revenge_badge"] = self.BADGE_POINTS[BadgeSlug.AVOIDED_REVENGE]

        # Revised Thesis
        if review.thesis_revised:
            if self._try_award_badge(
                profile.user_id, BadgeSlug.REVISED_THESIS,
                decision.id, review.id, badges
            ):
                points["revised_thesis_badge"] = self.BADGE_POINTS[BadgeSlug.REVISED_THESIS]

        total = self._commit_points(profile, points, "reflection", decision.id, review.id)

        return PointsBadgeResult(
            user_id=profile.user_id,
            total_points_awarded=total,
            points_breakdown=points,
            badges_earned=badges,
            streak_days=profile.logging_streak_days,
            streak_updated=False,
            streak_broken=False,
            new_total_points=profile.total_points,
        )

    # -----------------------------------------------------------------------
    # Event 4: Insight loop completed
    # -----------------------------------------------------------------------

    def on_insight_loop_completed(
        self,
        loop:    InsightLoop,
        profile: UserGamificationProfile,
    ) -> PointsBadgeResult:
        points = {}
        badges = []

        points["insight_loop_complete"] = self.POINTS["insight_loop_complete"]

        completed = (
            self.db.query(InsightLoop)
            .filter(
                InsightLoop.user_id == profile.user_id,
                InsightLoop.status == "completed",
            )
            .count()
        )

        # FIX #2: points only if badge is newly earned
        if completed == 1:
            if self._try_award_badge(
                profile.user_id, BadgeSlug.LOOP_CLOSED,
                None, None, badges
            ):
                points["loop_closed_badge"] = self.BADGE_POINTS[BadgeSlug.LOOP_CLOSED]

        if loop.improvement_delta and loop.improvement_delta >= 10:
            if self._try_award_badge(
                profile.user_id, BadgeSlug.BIAS_CORRECTED,
                None, None, badges
            ):
                points["bias_corrected_badge"] = self.BADGE_POINTS[BadgeSlug.BIAS_CORRECTED]

        if loop.domain != "investing":
            investing_resolved = (
                self.db.query(Decision)
                .filter(
                    Decision.user_id == profile.user_id,
                    Decision.domain == "investing",
                    Decision.status == DecisionStatus.RESOLVED,
                )
                .count()
            )
            if investing_resolved >= 30:
                if self._try_award_badge(
                    profile.user_id, BadgeSlug.SKILL_TRANSFERRED,
                    None, None, badges
                ):
                    points["skill_transferred_badge"] = self.BADGE_POINTS[BadgeSlug.SKILL_TRANSFERRED]

        total = self._commit_points(profile, points, "improvement", None, None)

        return PointsBadgeResult(
            user_id=profile.user_id,
            total_points_awarded=total,
            points_breakdown=points,
            badges_earned=badges,
            streak_days=profile.logging_streak_days,
            streak_updated=False,
            streak_broken=False,
            new_total_points=profile.total_points,
        )

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _try_award_badge(
        self,
        user_id:     UUID,
        slug:        BadgeSlug,
        decision_id: Optional[UUID],
        review_id:   Optional[UUID],
        badges_list: list,
    ) -> bool:
        """
        Award badge if not already earned. Idempotent.
        Returns True ONLY if newly awarded — caller gates point award on this.
        FIX #2: return value now used by all callers.
        """
        existing = (
            self.db.query(UserBadge)
            .filter(
                UserBadge.user_id == user_id,
                UserBadge.badge_slug == slug,
            )
            .first()
        )
        if existing:
            return False

        badge = UserBadge(
            user_id=user_id,
            badge_slug=slug,
            triggered_by_decision_id=decision_id,
            triggered_by_review_id=review_id,
            points_awarded=self.BADGE_POINTS.get(slug, 0),
            earned_at=datetime.utcnow(),
        )
        self.db.add(badge)
        self.db.flush()
        badges_list.append(slug)
        return True

    def _commit_points(
        self,
        profile:     UserGamificationProfile,
        points:      dict,
        category:    str,
        decision_id: Optional[UUID],
        review_id:   Optional[UUID],
    ) -> int:
        total = 0
        for reason, amount in points.items():
            profile.total_points += amount
            total += amount
            entry = PointsLedger(
                user_id=profile.user_id,
                points=amount,
                reason=reason.replace("_", " ").title(),
                category=category,
                decision_id=decision_id,
                review_id=review_id,
                running_total=profile.total_points,
            )
            self.db.add(entry)
        self.db.flush()
        return total

    def _update_streak(
        self,
        profile: UserGamificationProfile,
    ) -> tuple[bool, bool]:
        now   = datetime.utcnow()
        today = now.date()

        if profile.logging_streak_last_date is None:
            profile.logging_streak_days      = 1
            profile.logging_streak_last_date = now
            return True, False

        last  = profile.logging_streak_last_date.date()
        delta = (today - last).days

        if delta == 0:
            return False, False

        if delta == 1:
            profile.logging_streak_days += 1
            profile.logging_streak_last_date = now
            return True, False

        if delta == 2 and profile.grace_days_used < 1:
            profile.grace_days_used += 1
            profile.logging_streak_days += 1
            profile.logging_streak_last_date = now
            return True, False

        # Broken
        profile.logging_streak_days      = 1
        profile.logging_streak_last_date = now
        return True, True

    def _check_streak_badges(
        self,
        profile:     UserGamificationProfile,
        decision_id: UUID,
        badges_list: list,
    ) -> dict:
        points = {}

        if profile.logging_streak_days >= 7:
            if self._try_award_badge(
                profile.user_id, BadgeSlug.SEVEN_DAY_STREAK,
                decision_id, None, badges_list
            ):
                points["streak_7_day"] = self.POINTS["streak_7_day"]

        if profile.logging_streak_days >= 30:
            if self._try_award_badge(
                profile.user_id, BadgeSlug.THIRTY_DAY_STREAK,
                decision_id, None, badges_list
            ):
                points["streak_30_day"] = self.POINTS["streak_30_day"]

        return points

    def _calibration_trending_up(
        self,
        user_id: UUID,
        profile: UserGamificationProfile,  # FIX #4: profile passed in for guard
    ) -> bool:
        """
        Returns True if calibration improved meaningfully over last 30 days.
        FIX #4: Awards at most once per 30-day window via last_trend_bonus_at.
        """
        # Idempotency guard
        if profile.last_trend_bonus_at:
            days_since = (datetime.utcnow() - profile.last_trend_bonus_at).days
            if days_since < 30:
                return False

        now = datetime.utcnow()

        earliest_recent = (
            self.db.query(UserScoreSnapshot)
            .filter(
                UserScoreSnapshot.user_id == user_id,
                UserScoreSnapshot.snapshot_at >= now - timedelta(days=30),
            )
            .order_by(UserScoreSnapshot.snapshot_at.asc())
            .first()
        )

        latest = (
            self.db.query(UserScoreSnapshot)
            .filter(UserScoreSnapshot.user_id == user_id)
            .order_by(UserScoreSnapshot.snapshot_at.desc())
            .first()
        )

        if not earliest_recent or not latest:
            return False

        is_trending = (
            latest.calibration_score is not None
            and earliest_recent.calibration_score is not None
            and latest.calibration_score > earliest_recent.calibration_score + 2.0
        )

        if is_trending:
            profile.last_trend_bonus_at = datetime.utcnow()  # Set guard
            self.db.flush()

        return is_trending

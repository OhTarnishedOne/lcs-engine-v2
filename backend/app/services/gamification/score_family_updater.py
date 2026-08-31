# app/services/gamification/score_family_updater.py
# v2 — FIX #3 applied:
#   _process_score now takes explicit call_number argument
#   eliminates event-order coupling with PointsBadgeEvaluator

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.gamification import (
    Decision,
    DecisionReview,
    DecisionStatus,
    InsightLoop,
    TierLevel,
    UserGamificationProfile,
    UserScoreSnapshot,
)
from app.services.gamification.brier import (
    BrierScoreCalculator,
    calculate_average_brier,
    convert_brier_to_calibration_score,
)


@dataclass
class ScoreFamilyUpdate:
    user_id:           UUID
    decision_id:       UUID
    process_score:     float
    calibration_score: Optional[float]
    reflection_score:  Optional[float]
    improvement_score: Optional[float]
    lcs_score:         float
    previous_tier:     TierLevel
    new_tier:          TierLevel
    tier_advanced:     bool
    total_calls:       int
    resolved_calls:    int
    calibration_just_unlocked: bool
    improvement_just_unlocked: bool
    milestone_points:    int
    milestone_breakdown: dict = field(default_factory=dict)


class ScoreFamilyUpdater:

    # ADR-001: score visible at 5 (provisional), established at 10
    CALIBRATION_VISIBLE = 5
    CALIBRATION_ESTABLISHED = 10
    IMPROVEMENT_UNLOCK = 30

    def __init__(self, db: Session):
        self.db = db

    def update_after_resolution(
        self,
        decision: Decision,
        profile:  UserGamificationProfile,
    ) -> ScoreFamilyUpdate:
        """
        Called after a decision resolves.
        NOTE: PointsBadgeEvaluator.on_decision_logged() must have already
        incremented profile.total_calls before this is called.
        FIX #3: _process_score receives call_number explicitly.
        """
        previous_tier  = profile.tier
        resolved_calls = profile.resolved_calls + 1

        # FIX #3: pass total_calls explicitly — no hidden dependency on event order
        process_score = self._process_score(
            profile, decision, call_number=profile.total_calls
        )

        calibration_score, calibration_just_unlocked = self._calibration_score(
            decision.user_id, profile, resolved_calls
        )

        reflection_score = self._reflection_score(decision.user_id, profile)

        improvement_score, improvement_just_unlocked = self._improvement_score(
            decision.user_id, profile, resolved_calls
        )

        lcs_score = self._composite(
            process_score, calibration_score,
            reflection_score, improvement_score, resolved_calls,
        )

        new_tier      = self._evaluate_tier(
            resolved_calls, process_score,
            calibration_score, improvement_score, profile
        )
        tier_advanced = new_tier != previous_tier

        milestone_points, milestone_breakdown = self._milestone_points(
            calibration_just_unlocked, improvement_just_unlocked,
            tier_advanced, new_tier
        )

        # Persist
        profile.process_score     = round(process_score, 2)
        profile.calibration_score = round(calibration_score, 2) if calibration_score is not None else None
        profile.reflection_score  = round(reflection_score, 2) if reflection_score is not None else None
        profile.improvement_score = round(improvement_score, 2) if improvement_score is not None else None
        profile.lcs_score         = round(lcs_score, 2)
        profile.tier              = new_tier
        profile.resolved_calls    = resolved_calls

        if tier_advanced:
            profile.tier_updated_at = datetime.utcnow()

        self.db.flush()
        self._write_snapshot(profile, decision.id, resolved_calls)

        return ScoreFamilyUpdate(
            user_id=decision.user_id,
            decision_id=decision.id,
            process_score=profile.process_score,
            calibration_score=profile.calibration_score,
            reflection_score=profile.reflection_score,
            improvement_score=profile.improvement_score,
            lcs_score=profile.lcs_score,
            previous_tier=previous_tier,
            new_tier=new_tier,
            tier_advanced=tier_advanced,
            total_calls=profile.total_calls,
            resolved_calls=resolved_calls,
            calibration_just_unlocked=calibration_just_unlocked,
            improvement_just_unlocked=improvement_just_unlocked,
            milestone_points=milestone_points,
            milestone_breakdown=milestone_breakdown,
        )

    def update_after_review(
        self,
        decision: Decision,
        review:   DecisionReview,
        profile:  UserGamificationProfile,
    ) -> ScoreFamilyUpdate:
        """
        Called after a decision review is submitted.

        A review does not resolve anything, so process/calibration and the tier
        are left as-is (tier transitions and milestone bonuses stay a
        resolution-time event). It recomputes the reflection family — which is
        exactly what a review changes — and the improvement family and composite
        that depend on it, then writes a fresh snapshot so the user sees their
        reflection reflected immediately.
        """
        resolved_calls    = profile.resolved_calls
        process_score     = profile.process_score or 0.0
        calibration_score = profile.calibration_score

        reflection_score = self._reflection_score(decision.user_id, profile)
        improvement_score, _ = self._improvement_score(
            decision.user_id, profile, resolved_calls
        )
        lcs_score = self._composite(
            process_score, calibration_score,
            reflection_score, improvement_score, resolved_calls,
        )

        profile.reflection_score  = round(reflection_score, 2) if reflection_score is not None else None
        profile.improvement_score = round(improvement_score, 2) if improvement_score is not None else None
        profile.lcs_score         = round(lcs_score, 2)

        self.db.flush()
        self._write_snapshot(profile, decision.id, resolved_calls)

        return ScoreFamilyUpdate(
            user_id=decision.user_id,
            decision_id=decision.id,
            process_score=profile.process_score or 0.0,
            calibration_score=profile.calibration_score,
            reflection_score=profile.reflection_score,
            improvement_score=profile.improvement_score,
            lcs_score=profile.lcs_score,
            previous_tier=profile.tier,
            new_tier=profile.tier,
            tier_advanced=False,
            total_calls=profile.total_calls,
            resolved_calls=resolved_calls,
            calibration_just_unlocked=False,
            improvement_just_unlocked=False,
            milestone_points=0,
            milestone_breakdown={},
        )

    # -----------------------------------------------------------------------
    # FIX #3: call_number is now an explicit parameter
    # -----------------------------------------------------------------------

    def _process_score(
        self,
        profile:     UserGamificationProfile,
        decision:    Decision,
        call_number: int,  # FIX #3: explicit, not read from profile
    ) -> float:
        """
        Rolling average of process quality per decision (0–100).
            Confidence stated (required):  15 pts base
            Reasoning written:            +40 pts
            Falsification stated:         +30 pts
            Curated question used:        +15 pts
        """
        decision_process = 15
        if decision.reasoning:
            decision_process += 40
        if decision.falsification:
            decision_process += 30
        if decision.is_curated:
            decision_process += 15

        if call_number <= 1:
            return float(decision_process)

        previous_total = profile.process_score * (call_number - 1)
        return (previous_total + decision_process) / call_number

    # -----------------------------------------------------------------------
    # Remaining methods unchanged from v1
    # -----------------------------------------------------------------------

    def _calibration_score(
        self,
        user_id:        UUID,
        profile:        UserGamificationProfile,
        resolved_calls: int,
    ) -> tuple[Optional[float], bool]:
        if resolved_calls < self.CALIBRATION_VISIBLE:
            return None, False

        just_unlocked = (
            resolved_calls == self.CALIBRATION_VISIBLE
            and profile.calibration_score is None
        )

        resolved = (
            self.db.query(Decision)
            .filter(
                Decision.user_id == user_id,
                Decision.status == DecisionStatus.RESOLVED,
                Decision.confidence.isnot(None),
                Decision.outcome_binary.isnot(None),
            )
            .all()
        )

        if not resolved:
            return None, just_unlocked

        brier_scores = [
            BrierScoreCalculator.calculate_brier_score(d.confidence, bool(d.outcome_binary))
            for d in resolved
        ]
        avg_brier         = calculate_average_brier(brier_scores)
        calibration_score = convert_brier_to_calibration_score(avg_brier)
        return calibration_score, just_unlocked

    def _reflection_score(
        self,
        user_id: UUID,
        profile: UserGamificationProfile,
    ) -> Optional[float]:
        reviews = (
            self.db.query(DecisionReview)
            .filter(DecisionReview.user_id == user_id)
            .all()
        )
        if not reviews:
            return None

        resolved     = max(profile.resolved_calls, 1)
        n            = len(reviews)
        completion   = min(n / resolved, 1.0) * 40
        attributed   = sum(1 for r in reviews if r.outcome_attribution)
        attr_qual    = (attributed / n) * 30
        self_flagged = sum(1 for r in reviews if r.self_flagged_bias_before_ai)
        bias_qual    = min((self_flagged / n) * 3, 1.0) * 30

        return round(completion + attr_qual + bias_qual, 2)

    def _improvement_score(
        self,
        user_id:        UUID,
        profile:        UserGamificationProfile,
        resolved_calls: int,
    ) -> tuple[Optional[float], bool]:
        if resolved_calls < self.IMPROVEMENT_UNLOCK:
            return None, False

        just_unlocked = (
            resolved_calls == self.IMPROVEMENT_UNLOCK
            and profile.improvement_score is None
        )

        trend_score = self._calibration_trend(user_id)

        bias_score = 50.0
        if profile.known_biases:
            reducing   = sum(1 for b in profile.known_biases if b.get("trend") == "reducing")
            bias_score = min((reducing / len(profile.known_biases)) * 100, 100)

        completed_loops = (
            self.db.query(InsightLoop)
            .filter(
                InsightLoop.user_id == user_id,
                InsightLoop.status == "completed",
            )
            .count()
        )
        loop_score = min(completed_loops * 25, 100)

        improvement = (
            trend_score * 0.50 +
            bias_score  * 0.30 +
            loop_score  * 0.20
        )
        return round(improvement, 2), just_unlocked

    def _calibration_trend(self, user_id: UUID) -> float:
        now       = datetime.utcnow()
        snapshots = (
            self.db.query(UserScoreSnapshot)
            .filter(UserScoreSnapshot.user_id == user_id)
            .order_by(UserScoreSnapshot.snapshot_at.desc())
            .limit(120)
            .all()
        )
        if len(snapshots) < 2:
            return 50.0

        recent   = [s for s in snapshots if s.snapshot_at >= now - timedelta(days=30)]
        baseline = [s for s in snapshots if s.snapshot_at < now - timedelta(days=30)]
        if not recent or not baseline:
            return 50.0

        recent_cal   = sum(s.calibration_score or 0 for s in recent) / len(recent)
        baseline_cal = sum(s.calibration_score or 0 for s in baseline) / len(baseline)
        delta        = recent_cal - baseline_cal
        return min(max(50 + (delta / 20) * 50, 0), 100)

    def _composite(
        self,
        process:        float,
        calibration:    Optional[float],
        reflection:     Optional[float],
        improvement:    Optional[float],
        resolved_calls: int,
    ) -> float:
        improvement_weight = min(0.10 + (resolved_calls / 1000), 0.20)
        active = {"process": (process, 0.30)}
        if calibration is not None:
            active["calibration"] = (calibration, 0.35)
        if reflection is not None:
            active["reflection"]  = (reflection, 0.25)
        if improvement is not None:
            active["improvement"] = (improvement, improvement_weight)

        total_weight = sum(w for _, w in active.values())
        composite    = sum(score * (w / total_weight) for score, w in active.values())
        return round(composite, 2)

    def _evaluate_tier(
        self,
        resolved_calls:    int,
        process_score:     float,
        calibration_score: Optional[float],
        improvement_score: Optional[float],
        profile:           UserGamificationProfile,
    ) -> TierLevel:
        cal = calibration_score or 0
        imp = improvement_score or 0

        if resolved_calls >= 150 and process_score >= 75 and cal >= 75 and imp >= 75:
            return TierLevel.ARCHITECT
        if resolved_calls >= 75 and cal >= 60 and imp >= 70:
            return TierLevel.STRATEGIC
        if resolved_calls >= 30 and cal >= 60:
            return TierLevel.CALIBRATED
        if resolved_calls >= 10 and process_score >= 50 and profile.reviewed_calls >= 1:
            return TierLevel.REFLECTIVE
        return TierLevel.INSTINCTIVE

    def _milestone_points(
        self,
        calibration_unlocked: bool,
        improvement_unlocked: bool,
        tier_advanced:        bool,
        new_tier:             TierLevel,
    ) -> tuple[int, dict]:
        points    = 0
        breakdown = {}
        if calibration_unlocked:
            points += 100
            breakdown["calibration_score_unlocked"] = 100
        if improvement_unlocked:
            points += 150
            breakdown["improvement_score_unlocked"] = 150
        if tier_advanced:
            tier_pts = {
                TierLevel.REFLECTIVE: 100,
                TierLevel.CALIBRATED: 200,
                TierLevel.STRATEGIC:  350,
                TierLevel.ARCHITECT:  500,
            }
            p = tier_pts.get(new_tier, 0)
            points += p
            breakdown[f"tier_advanced_{new_tier.value}"] = p
        return points, breakdown

    def _write_snapshot(
        self,
        profile:        UserGamificationProfile,
        triggered_by:   UUID,
        resolved_calls: int,
    ) -> None:
        snapshot = UserScoreSnapshot(
            user_id=profile.user_id,
            process_score=profile.process_score or 0,
            calibration_score=profile.calibration_score or 0,
            reflection_score=profile.reflection_score or 0,
            improvement_score=profile.improvement_score or 0,
            lcs_score=profile.lcs_score,
            tier=profile.tier,
            total_calls=profile.total_calls,
            resolved_calls=resolved_calls,
            reviewed_calls=profile.reviewed_calls,
            triggered_by=triggered_by,
        )
        self.db.add(snapshot)
        self.db.flush()

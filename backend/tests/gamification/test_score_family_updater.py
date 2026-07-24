# tests/gamification/test_score_family_updater.py
"""
Unit tests for score_family_updater.py

Tests the four score family computations, composite weighting,
tier advancement, and snapshot writing — all with a mocked DB session.

Run: pytest tests/gamification/test_score_family_updater.py -v
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call
from uuid import uuid4

from app.db.models.gamification import (
    Decision, DecisionDomain, DecisionReview, DecisionStatus,
    InsightLoop, TierLevel, UserGamificationProfile, UserScoreSnapshot,
)
from app.services.gamification.score_family_updater import (
    ScoreFamilyUpdate, ScoreFamilyUpdater,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_profile(**kwargs) -> UserGamificationProfile:
    """Create a minimal UserGamificationProfile for testing."""
    p = MagicMock(spec=UserGamificationProfile)
    p.user_id            = kwargs.get("user_id", uuid4())
    p.process_score      = kwargs.get("process_score", 0.0)
    p.calibration_score  = kwargs.get("calibration_score", None)
    p.reflection_score   = kwargs.get("reflection_score", None)
    p.improvement_score  = kwargs.get("improvement_score", None)
    p.lcs_score          = kwargs.get("lcs_score", 0.0)
    p.tier               = kwargs.get("tier", TierLevel.INSTINCTIVE)
    p.tier_updated_at    = kwargs.get("tier_updated_at", None)
    p.total_calls        = kwargs.get("total_calls", 1)
    p.resolved_calls     = kwargs.get("resolved_calls", 0)
    p.reviewed_calls     = kwargs.get("reviewed_calls", 0)
    p.known_biases       = kwargs.get("known_biases", None)
    return p


def make_decision(**kwargs) -> Decision:
    d = MagicMock(spec=Decision)
    d.id             = kwargs.get("id", uuid4())
    d.user_id        = kwargs.get("user_id", uuid4())
    d.confidence     = kwargs.get("confidence", 0.7)
    d.outcome_binary = kwargs.get("outcome_binary", True)
    d.reasoning      = kwargs.get("reasoning", "My thesis here.")
    d.falsification  = kwargs.get("falsification", "If CPI drops below 3%.")
    d.is_curated     = kwargs.get("is_curated", False)
    d.status         = DecisionStatus.RESOLVED
    d.domain         = DecisionDomain.INVESTING
    return d


def make_db_session(resolved_decisions=None, reviews=None, snapshots=None, loops=None):
    """Build a mock SQLAlchemy session."""
    db = MagicMock()

    def query_side_effect(model):
        q = MagicMock()

        if model == Decision:
            q.filter.return_value.all.return_value = resolved_decisions or []
        elif model == DecisionReview:
            q.filter.return_value.all.return_value = reviews or []
        elif model == UserScoreSnapshot:
            q.filter.return_value.order_by.return_value.limit.return_value.all.return_value = snapshots or []
            q.filter.return_value.order_by.return_value.first.return_value = (
                snapshots[-1] if snapshots else None
            )
        elif model == InsightLoop:
            q.filter.return_value.count.return_value = loops or 0

        return q

    db.query.side_effect = query_side_effect
    db.flush = MagicMock()
    db.add   = MagicMock()
    return db


# ---------------------------------------------------------------------------
# Process Score tests
# ---------------------------------------------------------------------------

class TestProcessScore:

    def test_first_call_full_process(self):
        """First call with reasoning + falsification → 85 pts"""
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)
        profile = make_profile(total_calls=1, process_score=0.0)
        decision = make_decision(reasoning="analysis", falsification="if wrong")

        score = updater._process_score(profile, decision, call_number=1)

        # 15 (base) + 40 (reasoning) + 30 (falsification) = 85
        assert score == 85.0

    def test_first_call_no_reasoning_no_falsification(self):
        """First call with only confidence → 15 pts"""
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)
        profile = make_profile(total_calls=1, process_score=0.0)
        decision = make_decision(reasoning=None, falsification=None)

        score = updater._process_score(profile, decision, call_number=1)
        assert score == 15.0

    def test_curated_question_bonus(self):
        """Curated question adds +15"""
        db       = make_db_session()
        updater  = ScoreFamilyUpdater(db)
        profile  = make_profile(total_calls=1, process_score=0.0)
        decision = make_decision(reasoning=None, falsification=None, is_curated=True)

        score = updater._process_score(profile, decision, call_number=1)
        assert score == 30.0  # 15 base + 15 curated

    def test_rolling_average_second_call(self):
        """Second call rolls correctly with previous score."""
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)

        # First call scored 85, now on call 2 with 15pts (no reasoning/falsification)
        profile  = make_profile(total_calls=2, process_score=85.0)
        decision = make_decision(reasoning=None, falsification=None)

        score = updater._process_score(profile, decision, call_number=2)
        # Rolling: (85 * 1 + 15) / 2 = 50.0
        assert score == pytest.approx(50.0, abs=0.01)

    def test_call_number_explicit_prevents_order_coupling(self):
        """
        FIX #3: call_number is explicit.
        Passing different call_numbers gives different results,
        proving the computation is independent of profile.total_calls state.
        """
        db       = make_db_session()
        updater  = ScoreFamilyUpdater(db)
        profile  = make_profile(total_calls=5, process_score=60.0)
        decision = make_decision(reasoning="analysis", falsification=None)

        # call_number=5 (total_calls after increment)
        score_5 = updater._process_score(profile, decision, call_number=5)
        # call_number=6 (if total_calls was incremented again)
        score_6 = updater._process_score(profile, decision, call_number=6)

        # They should differ — proving call_number drives the computation
        assert score_5 != score_6

    def test_process_score_never_exceeds_100(self):
        """Max process score per decision is 100."""
        db       = make_db_session()
        updater  = ScoreFamilyUpdater(db)
        profile  = make_profile(total_calls=1, process_score=0.0)
        decision = make_decision(
            reasoning="analysis",
            falsification="if wrong",
            is_curated=True,
        )
        score = updater._process_score(profile, decision, call_number=1)
        # 15 + 40 + 30 + 15 = 100
        assert score == 100.0

    def test_being_wrong_does_not_affect_process_score(self):
        """
        Process score must not be affected by outcome.
        A wrong call with great process earns the same as a right call with great process.
        """
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)

        profile_right = make_profile(total_calls=1, process_score=0.0)
        profile_wrong = make_profile(total_calls=1, process_score=0.0)

        decision_right = make_decision(outcome_binary=True,  reasoning="analysis", falsification="if wrong")
        decision_wrong = make_decision(outcome_binary=False, reasoning="analysis", falsification="if wrong")

        score_right = updater._process_score(profile_right, decision_right, call_number=1)
        score_wrong = updater._process_score(profile_wrong, decision_wrong, call_number=1)

        assert score_right == score_wrong


# ---------------------------------------------------------------------------
# Calibration Score tests
# ---------------------------------------------------------------------------

class TestCalibrationScore:

    def test_hidden_before_5_calls(self):
        """Calibration Score must be None before 5 resolved decisions (ADR-001)."""
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)
        profile = make_profile(calibration_score=None)

        for resolved_calls in range(1, 5):
            score, unlocked = updater._calibration_score(uuid4(), profile, resolved_calls)
            assert score is None, f"Should be None at {resolved_calls} calls"
            assert unlocked is False

    def test_unlocks_at_5_calls(self):
        """Calibration Score becomes visible at 5 resolved decisions (ADR-001 provisional)."""
        decisions = [
            MagicMock(
                confidence=0.7,
                outcome_binary=True,
                status=DecisionStatus.RESOLVED,
            )
            for _ in range(5)
        ]
        db = make_db_session(resolved_decisions=decisions)
        updater = ScoreFamilyUpdater(db)
        profile = make_profile(calibration_score=None)

        score, unlocked = updater._calibration_score(uuid4(), profile, resolved_calls=5)

        assert score is not None
        assert unlocked is True

    def test_not_flagged_as_unlocked_if_already_had_score(self):
        """If calibration_score was already set, just_unlocked is False."""
        decisions = [
            MagicMock(confidence=0.7, outcome_binary=True, status=DecisionStatus.RESOLVED)
            for _ in range(5)
        ]
        db = make_db_session(resolved_decisions=decisions)
        updater = ScoreFamilyUpdater(db)
        profile = make_profile(calibration_score=72.0)  # Already had a score

        _, unlocked = updater._calibration_score(uuid4(), profile, resolved_calls=5)
        assert unlocked is False

    def test_calibration_score_uses_brier_formula(self):
        """
        With all decisions at 70% confidence, outcome True:
        Brier = (0.7-1)^2 = 0.09 each
        avg_brier = 0.09
        calibration_score = 100 * (1 - 2 * 0.09) = 82.0 (ADR-001)
        """
        decisions = [
            MagicMock(confidence=0.7, outcome_binary=True, status=DecisionStatus.RESOLVED)
            for _ in range(5)
        ]
        db      = make_db_session(resolved_decisions=decisions)
        updater = ScoreFamilyUpdater(db)
        profile = make_profile(calibration_score=None)

        score, _ = updater._calibration_score(uuid4(), profile, resolved_calls=5)
        assert score == pytest.approx(82.0, abs=0.1)

    def test_calibration_score_in_range(self):
        """Calibration score must always be 0–100."""
        decisions = [
            MagicMock(confidence=0.5, outcome_binary=True, status=DecisionStatus.RESOLVED)
            for _ in range(15)
        ]
        db      = make_db_session(resolved_decisions=decisions)
        updater = ScoreFamilyUpdater(db)
        profile = make_profile(calibration_score=None)

        score, _ = updater._calibration_score(uuid4(), profile, resolved_calls=15)
        assert 0.0 <= score <= 100.0


# ---------------------------------------------------------------------------
# Reflection Score tests
# ---------------------------------------------------------------------------

class TestReflectionScore:

    def test_none_before_first_review(self):
        """Reflection Score is None until first review exists."""
        db      = make_db_session(reviews=[])
        updater = ScoreFamilyUpdater(db)
        profile = make_profile(resolved_calls=5)

        score = updater._reflection_score(uuid4(), profile)
        assert score is None

    def test_unlocks_after_first_review(self):
        """After one review, reflection score is a real number."""
        review = MagicMock(
            outcome_attribution="Because market shifted.",
            self_flagged_bias_before_ai=False,
        )
        db      = make_db_session(reviews=[review])
        updater = ScoreFamilyUpdater(db)
        profile = make_profile(resolved_calls=5)

        score = updater._reflection_score(uuid4(), profile)
        assert score is not None
        assert isinstance(score, float)

    def test_self_flagged_bias_improves_score(self):
        """Self-flagging bias before AI rewards more than not flagging."""
        review_no_flag = MagicMock(
            outcome_attribution="Market moved unexpectedly.",
            self_flagged_bias_before_ai=False,
        )
        review_flagged = MagicMock(
            outcome_attribution="I was overconfident in tech.",
            self_flagged_bias_before_ai=True,
        )

        db_no  = make_db_session(reviews=[review_no_flag])
        db_yes = make_db_session(reviews=[review_flagged])

        updater = ScoreFamilyUpdater(MagicMock())

        profile = make_profile(resolved_calls=1)

        updater.db = db_no
        score_no = updater._reflection_score(uuid4(), profile)

        updater.db = db_yes
        score_yes = updater._reflection_score(uuid4(), profile)

        assert score_yes > score_no

    def test_completion_rate_affects_score(self):
        """More reviews relative to resolved calls = higher completion rate."""
        review = MagicMock(
            outcome_attribution="Thesis held.",
            self_flagged_bias_before_ai=False,
        )

        # 1 review / 1 resolved = 100% completion
        db_high  = make_db_session(reviews=[review])
        profile_high = make_profile(resolved_calls=1)

        # 1 review / 10 resolved = 10% completion
        db_low   = make_db_session(reviews=[review])
        profile_low  = make_profile(resolved_calls=10)

        updater = ScoreFamilyUpdater(MagicMock())

        updater.db = db_high
        score_high = updater._reflection_score(uuid4(), profile_high)

        updater.db = db_low
        score_low = updater._reflection_score(uuid4(), profile_low)

        assert score_high > score_low


# ---------------------------------------------------------------------------
# Improvement Score tests
# ---------------------------------------------------------------------------

class TestImprovementScore:

    def test_hidden_before_30_calls(self):
        """Improvement Score must be None before 30 resolved decisions."""
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)
        profile = make_profile(improvement_score=None)

        for n in range(1, 30):
            score, unlocked = updater._improvement_score(uuid4(), profile, resolved_calls=n)
            assert score is None
            assert unlocked is False

    def test_unlocks_at_30_calls(self):
        """Improvement Score unlocks at exactly 30 resolved decisions."""
        db      = make_db_session(loops=0)
        updater = ScoreFamilyUpdater(db)
        profile = make_profile(improvement_score=None, known_biases=None)

        with patch.object(updater, '_calibration_trend', return_value=60.0):
            score, unlocked = updater._improvement_score(uuid4(), profile, resolved_calls=30)

        assert score is not None
        assert unlocked is True

    def test_not_unlocked_if_already_had_score(self):
        db      = make_db_session(loops=0)
        updater = ScoreFamilyUpdater(db)
        profile = make_profile(improvement_score=55.0, known_biases=None)

        with patch.object(updater, '_calibration_trend', return_value=60.0):
            _, unlocked = updater._improvement_score(uuid4(), profile, resolved_calls=30)

        assert unlocked is False

    def test_completed_loops_improve_score(self):
        """More completed insight loops → higher improvement score."""
        db_no_loops  = make_db_session(loops=0)
        db_one_loop  = make_db_session(loops=1)
        db_four_loops = make_db_session(loops=4)

        profile = make_profile(improvement_score=None, known_biases=None)

        updater = ScoreFamilyUpdater(MagicMock())

        with patch.object(updater, '_calibration_trend', return_value=50.0):
            updater.db = db_no_loops
            score_0, _ = updater._improvement_score(uuid4(), profile, resolved_calls=30)

            updater.db = db_one_loop
            score_1, _ = updater._improvement_score(uuid4(), profile, resolved_calls=30)

            updater.db = db_four_loops
            score_4, _ = updater._improvement_score(uuid4(), profile, resolved_calls=30)

        assert score_4 > score_1 > score_0

    def test_improvement_score_in_range(self):
        """Improvement Score must always be 0–100."""
        db      = make_db_session(loops=10)
        updater = ScoreFamilyUpdater(db)
        profile = make_profile(improvement_score=None, known_biases=None)

        with patch.object(updater, '_calibration_trend', return_value=100.0):
            score, _ = updater._improvement_score(uuid4(), profile, resolved_calls=50)

        assert 0.0 <= score <= 100.0


# ---------------------------------------------------------------------------
# Composite LCS Score tests
# ---------------------------------------------------------------------------

class TestComposite:

    def test_only_process_when_others_hidden(self):
        """When calibration/reflection/improvement are None, composite = process score."""
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)
        score   = updater._composite(
            process=70.0,
            calibration=None,
            reflection=None,
            improvement=None,
            resolved_calls=5,
        )
        assert score == pytest.approx(70.0, abs=0.01)

    def test_weights_sum_to_100_percent(self):
        """With all families active, composite is weighted average summing to 1.0."""
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)

        # All families = 100 → composite should be 100
        score = updater._composite(
            process=100.0,
            calibration=100.0,
            reflection=100.0,
            improvement=100.0,
            resolved_calls=50,
        )
        assert score == pytest.approx(100.0, abs=0.01)

    def test_all_families_zero_gives_zero(self):
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)
        score   = updater._composite(
            process=0.0,
            calibration=0.0,
            reflection=0.0,
            improvement=0.0,
            resolved_calls=50,
        )
        assert score == pytest.approx(0.0, abs=0.01)

    def test_improvement_weight_scales_with_calls(self):
        """
        At 100+ calls, improvement weight increases.
        A higher improvement score should move the composite more
        at 100 calls than at 30 calls.
        """
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)

        base = dict(process=60.0, calibration=60.0, reflection=60.0)

        score_30  = updater._composite(**base, improvement=100.0, resolved_calls=30)
        score_100 = updater._composite(**base, improvement=100.0, resolved_calls=100)

        # Higher improvement weight at 100 calls should lift the composite
        assert score_100 > score_30

    def test_composite_in_range(self):
        """Composite score must always be 0–100."""
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)

        test_cases = [
            (50, None, None, None, 1),
            (80, 70, None, None, 10),
            (60, 65, 55, None, 25),
            (70, 72, 60, 45, 50),
            (90, 85, 80, 75, 150),
        ]

        for process, cal, ref, imp, calls in test_cases:
            score = updater._composite(process, cal, ref, imp, calls)
            assert 0.0 <= score <= 100.0, (
                f"Composite out of range: {score} for "
                f"({process}, {cal}, {ref}, {imp}, {calls})"
            )


# ---------------------------------------------------------------------------
# Tier evaluation tests
# ---------------------------------------------------------------------------

class TestTierEvaluation:

    def test_instinctive_by_default(self):
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)
        profile = make_profile(reviewed_calls=0)

        tier = updater._evaluate_tier(0, 0.0, None, None, profile)
        assert tier == TierLevel.INSTINCTIVE

    def test_reflective_requires_calls_process_and_review(self):
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)

        # All conditions met
        profile = make_profile(reviewed_calls=1)
        tier = updater._evaluate_tier(10, 55.0, None, None, profile)
        assert tier == TierLevel.REFLECTIVE

        # Missing review
        profile_no_review = make_profile(reviewed_calls=0)
        tier = updater._evaluate_tier(10, 55.0, None, None, profile_no_review)
        assert tier == TierLevel.INSTINCTIVE

        # Not enough calls
        profile = make_profile(reviewed_calls=1)
        tier = updater._evaluate_tier(9, 55.0, None, None, profile)
        assert tier == TierLevel.INSTINCTIVE

        # Process score too low
        tier = updater._evaluate_tier(10, 40.0, None, None, profile)
        assert tier == TierLevel.INSTINCTIVE

    def test_calibrated_requires_calls_and_calibration_score(self):
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)
        profile = make_profile(reviewed_calls=5)

        tier = updater._evaluate_tier(30, 70.0, 65.0, None, profile)
        assert tier == TierLevel.CALIBRATED

        # Calibration score too low
        tier = updater._evaluate_tier(30, 70.0, 55.0, None, profile)
        assert tier != TierLevel.CALIBRATED

    def test_architect_requires_all_scores_high(self):
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)
        profile = make_profile(reviewed_calls=20)

        tier = updater._evaluate_tier(150, 80.0, 80.0, 80.0, profile)
        assert tier == TierLevel.ARCHITECT

        # Missing one threshold
        tier = updater._evaluate_tier(150, 80.0, 70.0, 80.0, profile)
        assert tier != TierLevel.ARCHITECT

    def test_volume_alone_cannot_reach_architect(self):
        """
        The whole point: you can't level up through volume alone.
        1000 calls with zero scores → Instinctive.
        """
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)
        profile = make_profile(reviewed_calls=0)

        tier = updater._evaluate_tier(1000, 0.0, 0.0, 0.0, profile)
        assert tier == TierLevel.INSTINCTIVE


# ---------------------------------------------------------------------------
# Milestone points tests
# ---------------------------------------------------------------------------

class TestMilestonePoints:

    def test_calibration_unlock_gives_100_points(self):
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)
        pts, breakdown = updater._milestone_points(
            calibration_unlocked=True,
            improvement_unlocked=False,
            tier_advanced=False,
            new_tier=TierLevel.INSTINCTIVE,
        )
        assert pts == 100
        assert "calibration_score_unlocked" in breakdown

    def test_improvement_unlock_gives_150_points(self):
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)
        pts, breakdown = updater._milestone_points(
            calibration_unlocked=False,
            improvement_unlocked=True,
            tier_advanced=False,
            new_tier=TierLevel.INSTINCTIVE,
        )
        assert pts == 150
        assert "improvement_score_unlocked" in breakdown

    def test_tier_advancement_points(self):
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)

        tier_map = {
            TierLevel.REFLECTIVE: 100,
            TierLevel.CALIBRATED: 200,
            TierLevel.STRATEGIC:  350,
            TierLevel.ARCHITECT:  500,
        }

        for tier, expected_pts in tier_map.items():
            pts, _ = updater._milestone_points(
                calibration_unlocked=False,
                improvement_unlocked=False,
                tier_advanced=True,
                new_tier=tier,
            )
            assert pts == expected_pts, f"Expected {expected_pts} for {tier}, got {pts}"

    def test_no_milestones_gives_zero(self):
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)
        pts, breakdown = updater._milestone_points(
            calibration_unlocked=False,
            improvement_unlocked=False,
            tier_advanced=False,
            new_tier=TierLevel.INSTINCTIVE,
        )
        assert pts == 0
        assert breakdown == {}


# ---------------------------------------------------------------------------
# Snapshot writing
# ---------------------------------------------------------------------------

class TestWriteSnapshot:

    def test_snapshot_is_written_to_db(self):
        db      = make_db_session()
        updater = ScoreFamilyUpdater(db)
        profile = make_profile(
            process_score=70.0,
            calibration_score=65.0,
            reflection_score=55.0,
            improvement_score=None,
            lcs_score=64.5,
            tier=TierLevel.REFLECTIVE,
            total_calls=15,
            reviewed_calls=3,
        )

        triggered_by = uuid4()
        updater._write_snapshot(profile, triggered_by, resolved_calls=12)

        db.add.assert_called_once()
        db.flush.assert_called()

        added = db.add.call_args[0][0]
        assert isinstance(added, UserScoreSnapshot)
        assert added.user_id  == profile.user_id
        assert added.lcs_score == profile.lcs_score
        assert added.tier      == profile.tier

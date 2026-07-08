# tests/gamification/test_brier.py
"""
Unit tests for brier.py

Brier Score is the mathematical spine of LCS Engine calibration.
These tests should pass at 100% before any other gamification code is merged.

Run: pytest tests/gamification/test_brier.py -v
"""

import pytest
from app.services.gamification.brier import (
    BrierScoreCalculator,
    calculate_brier_score,
    calculate_average_brier,
    convert_brier_to_calibration_score,
)


# ---------------------------------------------------------------------------
# calculate_brier_score
# ---------------------------------------------------------------------------

class TestCalculateBrierScore:

    def test_perfect_confidence_correct_outcome(self):
        """100% confident, outcome True → BS = 0.0"""
        assert calculate_brier_score(1.0, True) == 0.0

    def test_perfect_confidence_wrong_outcome(self):
        """100% confident, outcome False → BS = 1.0 (worst possible)"""
        assert calculate_brier_score(1.0, False) == 1.0

    def test_zero_confidence_correct_outcome(self):
        """0% confident, outcome True → BS = 1.0 (worst possible)"""
        assert calculate_brier_score(0.0, True) == 1.0

    def test_zero_confidence_wrong_outcome(self):
        """0% confident, outcome False → BS = 0.0 (perfect)"""
        assert calculate_brier_score(0.0, False) == 0.0

    def test_fifty_percent_either_outcome(self):
        """50% confident → BS = 0.25 regardless of outcome"""
        assert calculate_brier_score(0.5, True)  == 0.25
        assert calculate_brier_score(0.5, False) == 0.25

    def test_seventy_percent_correct(self):
        """The example from the product spec: 70% confident, outcome True"""
        # BS = (0.70 - 1)^2 = (-0.30)^2 = 0.09
        assert calculate_brier_score(0.7, True) == pytest.approx(0.09, abs=1e-6)

    def test_seventy_percent_wrong(self):
        """70% confident, outcome False"""
        # BS = (0.70 - 0)^2 = 0.49
        assert calculate_brier_score(0.7, False) == pytest.approx(0.49, abs=1e-6)

    def test_returns_float(self):
        result = calculate_brier_score(0.6, True)
        assert isinstance(result, float)

    def test_confidence_out_of_range_high(self):
        with pytest.raises(ValueError, match="0.0 and 1.0"):
            calculate_brier_score(1.01, True)

    def test_confidence_out_of_range_low(self):
        with pytest.raises(ValueError, match="0.0 and 1.0"):
            calculate_brier_score(-0.01, True)

    def test_confidence_percentage_gives_helpful_error(self):
        """Passing 72 instead of 0.72 should raise with a helpful message."""
        with pytest.raises(ValueError, match="divide by 100"):
            calculate_brier_score(72.0, True)

    def test_boundary_values(self):
        """Boundary confidence values 0.0 and 1.0 are valid."""
        assert calculate_brier_score(0.0, False) == 0.0
        assert calculate_brier_score(1.0, True)  == 0.0

    def test_result_always_between_0_and_1(self):
        """BS must always be in [0, 1]."""
        test_cases = [
            (0.1, True), (0.9, False), (0.5, True),
            (0.3, False), (0.8, True), (0.01, False),
        ]
        for conf, out in test_cases:
            score = calculate_brier_score(conf, out)
            assert 0.0 <= score <= 1.0, f"BS out of range for ({conf}, {out}): {score}"


# ---------------------------------------------------------------------------
# calculate_average_brier
# ---------------------------------------------------------------------------

class TestCalculateAverageBrier:

    def test_single_score(self):
        assert calculate_average_brier([0.09]) == pytest.approx(0.09, abs=1e-6)

    def test_two_scores_average(self):
        assert calculate_average_brier([0.09, 0.25]) == pytest.approx(0.17, abs=1e-6)

    def test_all_zeros(self):
        """Perfect calibration across all calls."""
        assert calculate_average_brier([0.0, 0.0, 0.0]) == 0.0

    def test_all_ones(self):
        """Worst possible calibration across all calls."""
        assert calculate_average_brier([1.0, 1.0, 1.0]) == 1.0

    def test_mixed_scores(self):
        scores = [0.0, 0.25, 0.09, 1.0]
        expected = sum(scores) / len(scores)
        assert calculate_average_brier(scores) == pytest.approx(expected, abs=1e-6)

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="empty"):
            calculate_average_brier([])

    def test_returns_float(self):
        assert isinstance(calculate_average_brier([0.1, 0.2]), float)

    def test_result_between_0_and_1(self):
        scores = [0.04, 0.36, 0.09, 0.16, 0.01]
        result = calculate_average_brier(scores)
        assert 0.0 <= result <= 1.0


# ---------------------------------------------------------------------------
# convert_brier_to_calibration_score
# ---------------------------------------------------------------------------

class TestConvertBrierToCalibrationScore:

    def test_perfect_brier_gives_100(self):
        """avg_brier=0.0 → Calibration Score = 100"""
        assert convert_brier_to_calibration_score(0.0) == 100.0

    def test_worst_brier_gives_0(self):
        """avg_brier=1.0 → Calibration Score = 0"""
        assert convert_brier_to_calibration_score(1.0) == 0.0

    def test_half_brier_gives_50(self):
        """avg_brier=0.5 → Calibration Score = 50"""
        assert convert_brier_to_calibration_score(0.5) == 50.0

    def test_formula_correctness(self):
        """CS = 100 * (1 - avg_brier)"""
        avg_brier = 0.09
        expected  = 100 * (1 - avg_brier)
        assert convert_brier_to_calibration_score(avg_brier) == pytest.approx(expected, abs=1e-4)

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            convert_brier_to_calibration_score(1.01)
        with pytest.raises(ValueError):
            convert_brier_to_calibration_score(-0.01)

    def test_result_in_0_100(self):
        for brier in [0.0, 0.1, 0.25, 0.5, 0.75, 1.0]:
            score = convert_brier_to_calibration_score(brier)
            assert 0.0 <= score <= 100.0


# ---------------------------------------------------------------------------
# BrierScoreCalculator.calculate (single decision)
# ---------------------------------------------------------------------------

class TestCalculateSingleDecision:

    def test_well_calibrated_returns_calibrated(self):
        """88% confident, outcome True: gap = 12pp → calibrated"""
        result = BrierScoreCalculator.calculate(0.88, True)
        assert result.is_calibrated is True
        assert result.severity == "calibrated"

    def test_overconfident_severe(self):
        """95% confident, outcome False: gap = 95pp → severe"""
        result = BrierScoreCalculator.calculate(0.95, False)
        assert result.overconfident is True
        assert result.severity == "severe"
        assert result.is_calibrated is False

    def test_underconfident_moderate(self):
        """30% confident, outcome True: gap = 70pp → severe"""
        result = BrierScoreCalculator.calculate(0.3, True)
        assert result.underconfident is True
        assert result.is_calibrated is False

    def test_exactly_at_calibration_threshold(self):
        """Gap of exactly 15pp → calibrated"""
        result = BrierScoreCalculator.calculate(0.65, True)
        # gap = |0.65 - 1.0| = 0.35 → 35pp → NOT calibrated
        assert result.is_calibrated is False

        result2 = BrierScoreCalculator.calculate(0.85, True)
        # gap = |0.85 - 1.0| = 0.15 → 15pp → calibrated
        assert result2.is_calibrated is True

    def test_brier_score_matches_formula(self):
        """BrierResult.brier_score must match manual calculation."""
        conf, outcome = 0.72, True
        result = BrierScoreCalculator.calculate(conf, outcome)
        expected_bs = (conf - 1.0) ** 2
        assert result.brier_score == pytest.approx(expected_bs, abs=1e-6)

    def test_diagnosis_is_non_empty_string(self):
        result = BrierScoreCalculator.calculate(0.6, False)
        assert isinstance(result.diagnosis, str)
        assert len(result.diagnosis) > 10

    def test_result_is_immutable(self):
        """BrierResult is a frozen dataclass."""
        result = BrierScoreCalculator.calculate(0.5, True)
        with pytest.raises((AttributeError, TypeError)):
            result.brier_score = 0.99  # type: ignore


# ---------------------------------------------------------------------------
# BrierScoreCalculator.calculate_rolling
# ---------------------------------------------------------------------------

class TestCalculateRolling:

    def test_minimum_one_decision(self):
        result = BrierScoreCalculator.calculate_rolling([(0.7, True)])
        assert result.total_decisions == 1

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            BrierScoreCalculator.calculate_rolling([])

    def test_calibration_score_in_range(self):
        decisions = [(0.7, True), (0.6, False), (0.8, True), (0.4, False)]
        result = BrierScoreCalculator.calculate_rolling(decisions)
        assert 0.0 <= result.calibration_score <= 100.0

    def test_calibration_score_formula(self):
        """calibration_score = 100 * (1 - average_brier)"""
        decisions = [(0.7, True), (0.5, False)]
        result    = BrierScoreCalculator.calculate_rolling(decisions)
        briers    = [
            calculate_brier_score(c, o) for c, o in decisions
        ]
        expected_cs = convert_brier_to_calibration_score(
            calculate_average_brier(briers)
        )
        assert result.calibration_score == pytest.approx(expected_cs, abs=1e-4)

    def test_overconfidence_bias_positive_when_overconfident(self):
        """All overconfident calls → positive bias."""
        decisions = [(0.9, False), (0.8, False), (0.95, False)]
        result = BrierScoreCalculator.calculate_rolling(decisions)
        assert result.overconfidence_bias > 0

    def test_overconfidence_bias_negative_when_underconfident(self):
        """All underconfident calls → negative bias."""
        decisions = [(0.1, True), (0.2, True), (0.15, True)]
        result = BrierScoreCalculator.calculate_rolling(decisions)
        assert result.overconfidence_bias < 0

    def test_calibrated_count_accuracy(self):
        """2 calibrated, 1 not → calibrated_count = 2"""
        decisions = [
            (0.85, True),   # gap = 15pp → calibrated
            (0.90, True),   # gap = 10pp → calibrated
            (0.20, True),   # gap = 80pp → not calibrated
        ]
        result = BrierScoreCalculator.calculate_rolling(decisions)
        assert result.calibrated_count == 2

    def test_diagnosis_is_string(self):
        decisions = [(0.7, True), (0.6, False)]
        result = BrierScoreCalculator.calculate_rolling(decisions)
        assert isinstance(result.diagnosis, str)
        assert len(result.diagnosis) > 3

    def test_perfect_calibration_gives_high_score(self):
        """
        A user who always states exactly the right confidence
        should have calibration_score near 100.
        """
        # Approximate perfect calibration: 80% confidence, always right
        decisions = [(0.8, True)] * 20
        result = BrierScoreCalculator.calculate_rolling(decisions)
        # Not 100 (would need p=1.0 always), but should be high
        assert result.calibration_score > 90

    def test_worst_calibration_gives_low_score(self):
        """Always 100% confident, always wrong → calibration_score near 0."""
        decisions = [(1.0, False)] * 10
        result = BrierScoreCalculator.calculate_rolling(decisions)
        assert result.calibration_score == 0.0

    def test_diagnosis_slugs_are_valid(self):
        valid_diagnoses = {
            "exceptional", "good", "good_overconfident",
            "good_underconfident", "developing_overconfident",
            "developing_underconfident", "developing_mixed",
            "needs_work_overconfident", "needs_work_underconfident",
        }
        decisions = [(0.6, True), (0.4, False), (0.7, True)]
        result = BrierScoreCalculator.calculate_rolling(decisions)
        assert result.diagnosis in valid_diagnoses


# ---------------------------------------------------------------------------
# Regression tests — specific scenarios from the product spec
# ---------------------------------------------------------------------------

class TestProductSpecScenarios:

    def test_spec_example_70_percent_correct(self):
        """
        From the LCS spec:
            Prediction: 70%, Outcome: Yes
            Brier = (0.70 - 1)^2 = 0.09
        """
        bs = calculate_brier_score(0.70, True)
        assert bs == pytest.approx(0.09, abs=1e-6)

    def test_calibration_score_from_spec_example(self):
        """
        From the LCS spec:
            Calibration Score = 100 * (1 - average_brier)
        With average_brier = 0.09 → CS = 91.0
        """
        cs = convert_brier_to_calibration_score(0.09)
        assert cs == pytest.approx(91.0, abs=1e-4)

    def test_good_loser_scenario(self):
        """
        Good Loser: wrong outcome, but the process was sound.
        Brier score will be high (bad), but that's correct —
        the calibration hit is acknowledged, not hidden.
        The badge is awarded by the badge evaluator, not here.
        This test confirms the math doesn't lie.
        """
        # User said 80% confident (sound reasoning), outcome was False
        bs = calculate_brier_score(0.80, False)
        # BS = (0.8 - 0)^2 = 0.64 — high Brier, honest penalty
        assert bs == pytest.approx(0.64, abs=1e-6)
        result = BrierScoreCalculator.calculate(0.80, False)
        assert result.overconfident is True
        assert result.is_calibrated is False

    def test_humble_winner_scenario(self):
        """
        Humble Winner: right outcome, but user admitted shaky reasoning.
        Brier score will be good, but the badge isn't earned here —
        it's earned in the review. Math just confirms the outcome.
        """
        # User said 60% confident (shaky reasoning), outcome was True
        bs = calculate_brier_score(0.60, True)
        # BS = (0.6 - 1)^2 = 0.16 — not great, gap = 40pp
        assert bs == pytest.approx(0.16, abs=1e-6)
        result = BrierScoreCalculator.calculate(0.60, True)
        assert result.underconfident is True

# app/services/gamification/brier.py
"""
LCS Engine — Brier Score Calculator

The mathematical spine of the Calibration Score.

Philosophy:
    You are not being graded on whether you guessed right.
    You are being trained to know how confident you should have been.

Brier Score formula (binary outcomes):
    BS = (confidence - outcome)²

    confidence ∈ [0.0, 1.0]  — user's stated probability
    outcome    ∈ {0.0, 1.0}  — 1.0 if event occurred, 0.0 if not

    Lower Brier = better calibration.
    Perfect calibration = 0.0. Worst possible = 1.0.

User-facing Calibration Score (inverted, higher = better):
    Calibration Score = 100 * (1 - 2 * average_brier), clamped to [0, 100]

Visible at 5 resolved decisions (provisional); established at 10.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BrierResult:
    """
    Result of a single Brier Score calculation.
    Immutable — confidence and outcome are locked at resolution time.
    """
    confidence: float           # User's stated probability (0.0–1.0)
    outcome: float              # Resolved outcome (0.0 or 1.0)
    brier_score: float          # Raw score (0.0–1.0, lower = better)
    calibration_gap_pct: float  # abs(confidence - outcome) as percentage points (0–100)
    is_calibrated: bool         # True if gap ≤ 15 percentage points
    overconfident: bool         # True if confidence > outcome
    underconfident: bool        # True if confidence < outcome
    diagnosis: str              # Human-readable single sentence
    severity: str               # "calibrated" | "mild" | "moderate" | "severe"


@dataclass(frozen=True)
class RollingBrierResult:
    """
    Aggregated Brier Score across multiple resolved decisions.
    The basis for UserGamificationProfile.calibration_score.
    """
    average_brier: float         # Mean BS across all decisions (lower = better)
    calibration_score: float     # 100 * (1 - 2 * average_brier), 0–100 (higher = better)
    total_decisions: int         # Number of decisions included
    calibrated_count: int        # Decisions within ±15pp
    calibration_rate: float      # calibrated_count / total_decisions
    overconfidence_bias: float   # Mean(confidence - outcome); + = overconfident
    diagnosis: str               # Overall characterization


# ---------------------------------------------------------------------------
# Core calculator — stateless, no DB access
# ---------------------------------------------------------------------------

class BrierScoreCalculator:
    """
    Stateless Brier Score calculator.
    All methods are classmethods — no instantiation needed.

    Usage:
        result = BrierScoreCalculator.calculate(confidence=0.72, outcome=True)
        rolling = BrierScoreCalculator.calculate_rolling([
            (0.72, True), (0.40, False), (0.80, True)
        ])
    """

    # Calibration zones (percentage points gap)
    CALIBRATED_THRESHOLD = 15   # ±15pp = well calibrated
    MILD_THRESHOLD       = 25   # ±15–25pp = mild miscalibration
    MODERATE_THRESHOLD   = 40   # ±25–40pp = moderate
                                # >40pp = severe

    # ADR-001: visible at 5 (provisional), established at 10
    CALIBRATION_VISIBLE = 5
    CALIBRATION_ESTABLISHED = 10
    MIN_DECISIONS_TO_SHOW = CALIBRATION_VISIBLE

    # ---------------------------------------------------------------------------
    # 1. calculate_brier_score
    # ---------------------------------------------------------------------------

    @classmethod
    def calculate_brier_score(
        cls,
        confidence: float,
        outcome: bool,
    ) -> float:
        """
        Calculate raw Brier Score for a single decision.

        Args:
            confidence: User's stated probability (0.0–1.0).
                        If user entered 0–100, divide by 100 first.
            outcome:    True if the event occurred, False otherwise.

        Returns:
            Raw Brier Score (float, 0.0–1.0). Lower is better.

        Raises:
            ValueError: If confidence is outside [0.0, 1.0].
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {confidence}. "
                f"If you passed a percentage (e.g. 72), divide by 100 first."
            )

        outcome_float = 1.0 if outcome else 0.0
        return round((confidence - outcome_float) ** 2, 6)

    # ---------------------------------------------------------------------------
    # 2. calculate_average_brier
    # ---------------------------------------------------------------------------

    @classmethod
    def calculate_average_brier(cls, scores: list[float]) -> float:
        """
        Calculate mean Brier Score across multiple resolved decisions.

        Args:
            scores: List of individual Brier Scores from calculate_brier_score().
                    Must have at least 1 item.

        Returns:
            Mean Brier Score (float, 0.0–1.0). Lower is better.

        Raises:
            ValueError: If scores list is empty.
        """
        if not scores:
            raise ValueError("Cannot compute average Brier Score from empty list.")
        return round(sum(scores) / len(scores), 6)

    # ---------------------------------------------------------------------------
    # 3. convert_brier_to_calibration_score
    # ---------------------------------------------------------------------------

    @classmethod
    def convert_brier_to_calibration_score(cls, avg_brier: float) -> float:
        """
        Convert average Brier Score to the user-facing Calibration Score.

        Formula (ADR-001): Calibration Score = 100 * (1 - 2 * avg_brier), clamped [0, 100]

        The inversion means higher = better for the user, which is
        more intuitive than "lower Brier is better."

        Args:
            avg_brier: Mean Brier Score (0.0–1.0).

        Returns:
            Calibration Score (float, 0.0–100.0). Higher is better.
        """
        if not 0.0 <= avg_brier <= 1.0:
            raise ValueError(f"avg_brier must be 0.0–1.0, got {avg_brier}")
        raw = 100.0 * (1.0 - 2.0 * avg_brier)
        return round(max(0.0, min(100.0, raw)), 2)

    # ---------------------------------------------------------------------------
    # 4. calculate — convenience method (single decision, full result)
    # ---------------------------------------------------------------------------

    @classmethod
    def calculate(
        cls,
        confidence: float,
        outcome: bool,
    ) -> BrierResult:
        """
        Full single-decision calculation with diagnosis.
        Calls calculate_brier_score() internally.

        Returns:
            BrierResult dataclass with all fields populated.
        """
        brier_score   = cls.calculate_brier_score(confidence, outcome)
        outcome_float = 1.0 if outcome else 0.0
        gap           = abs(confidence - outcome_float)
        gap_pct       = round(gap * 100, 2)
        is_calibrated = gap_pct <= cls.CALIBRATED_THRESHOLD
        overconfident = confidence > outcome_float
        underconfident = confidence < outcome_float

        severity, diagnosis = cls._diagnose(
            confidence, outcome_float, gap_pct, overconfident
        )

        return BrierResult(
            confidence=confidence,
            outcome=outcome_float,
            brier_score=brier_score,
            calibration_gap_pct=gap_pct,
            is_calibrated=is_calibrated,
            overconfident=overconfident,
            underconfident=underconfident,
            diagnosis=diagnosis,
            severity=severity,
        )

    # ---------------------------------------------------------------------------
    # 5. calculate_rolling — convenience method (multiple decisions, full result)
    # ---------------------------------------------------------------------------

    @classmethod
    def calculate_rolling(
        cls,
        decisions: list[tuple[float, bool]],
    ) -> RollingBrierResult:
        """
        Full rolling calculation across multiple resolved decisions.
        Calls calculate_brier_score() and calculate_average_brier() internally.

        Args:
            decisions: List of (confidence, outcome) tuples.
                       confidence: float 0.0–1.0
                       outcome: bool

        Returns:
            RollingBrierResult with aggregated metrics.
        """
        if not decisions:
            raise ValueError("Need at least one decision for rolling calculation.")

        individual_scores = [
            cls.calculate_brier_score(conf, out)
            for conf, out in decisions
        ]

        average_brier      = cls.calculate_average_brier(individual_scores)
        calibration_score  = cls.convert_brier_to_calibration_score(average_brier)

        calibrated_count = sum(
            1 for conf, out in decisions
            if round(abs(conf - (1.0 if out else 0.0)) * 100, 2) <= cls.CALIBRATED_THRESHOLD
        )
        calibration_rate = round(calibrated_count / len(decisions), 4)

        # Overconfidence bias: mean(confidence - outcome)
        # Positive = overconfident, Negative = underconfident
        overconfidence_bias = round(
            sum(conf - (1.0 if out else 0.0) for conf, out in decisions)
            / len(decisions),
            4,
        )

        diagnosis = cls._rolling_diagnosis(
            calibration_score, overconfidence_bias, calibration_rate
        )

        return RollingBrierResult(
            average_brier=average_brier,
            calibration_score=calibration_score,
            total_decisions=len(decisions),
            calibrated_count=calibrated_count,
            calibration_rate=calibration_rate,
            overconfidence_bias=overconfidence_bias,
            diagnosis=diagnosis,
        )

    # ---------------------------------------------------------------------------
    # Diagnosis helpers (private)
    # ---------------------------------------------------------------------------

    @classmethod
    def _diagnose(
        cls,
        confidence: float,
        outcome: float,
        gap_pct: float,
        overconfident: bool,
    ) -> tuple[str, str]:
        """
        Return (severity, diagnosis) for a single call.
        Severity: "calibrated" | "mild" | "moderate" | "severe"
        """
        conf_pct = round(confidence * 100)

        if gap_pct <= cls.CALIBRATED_THRESHOLD:
            return (
                "calibrated",
                f"Well calibrated — {conf_pct}% confidence, outcome aligned. "
                f"You're within the ±15pt zone.",
            )

        direction = "overconfident" if overconfident else "underconfident"
        gap_str   = f"{gap_pct:.0f}pt"

        if gap_pct <= cls.MILD_THRESHOLD:
            severity = "mild"
            if overconfident:
                msg = (
                    f"Slightly overconfident — you stated {conf_pct}% but the call "
                    f"didn't land. A {gap_str} gap is mild; watch for the pattern."
                )
            else:
                msg = (
                    f"Slightly underconfident — you stated {conf_pct}% and were right. "
                    f"A {gap_str} gap means you knew more than you claimed."
                )

        elif gap_pct <= cls.MODERATE_THRESHOLD:
            severity = "moderate"
            if overconfident:
                msg = (
                    f"Overconfident — {conf_pct}% on a call that didn't resolve. "
                    f"A {gap_str} gap suggests anchoring high. Try narrowing your range."
                )
            else:
                msg = (
                    f"Underconfident — {conf_pct}% on a call that went your way. "
                    f"A {gap_str} gap means you're underselling your read consistently."
                )
        else:
            severity = "severe"
            if overconfident:
                msg = (
                    f"Significantly overconfident — {conf_pct}% on an outcome "
                    f"that went the other way. A {gap_str} gap is a strong signal. "
                    f"Your AI Tutor will flag this pattern if it repeats."
                )
            else:
                msg = (
                    f"Significantly underconfident — {conf_pct}% on a call you got right "
                    f"by a {gap_str} margin. Strong judgment deserves stronger confidence."
                )

        return severity, msg

    @classmethod
    def _rolling_diagnosis(
        cls,
        calibration_score: float,
        overconfidence_bias: float,
        calibration_rate: float,
    ) -> str:
        """
        Characterize overall calibration across all resolved calls.
        Returns a machine-readable slug that the AI Tutor can translate
        into natural language coaching.
        """
        if calibration_score >= 85:
            return "exceptional"

        if calibration_score >= 70:
            if abs(overconfidence_bias) < 0.05:
                return "good"
            return "good_overconfident" if overconfidence_bias > 0 else "good_underconfident"

        if calibration_score >= 55:
            if overconfidence_bias > 0.10:
                return "developing_overconfident"
            if overconfidence_bias < -0.10:
                return "developing_underconfident"
            return "developing_mixed"

        return "needs_work_overconfident" if overconfidence_bias > 0 else "needs_work_underconfident"


# ---------------------------------------------------------------------------
# Convenience functions (module-level, for clean imports)
# ---------------------------------------------------------------------------

def calculate_brier_score(confidence: float, outcome: bool) -> float:
    """Module-level alias. See BrierScoreCalculator.calculate_brier_score."""
    return BrierScoreCalculator.calculate_brier_score(confidence, outcome)


def calculate_average_brier(scores: list[float]) -> float:
    """Module-level alias. See BrierScoreCalculator.calculate_average_brier."""
    return BrierScoreCalculator.calculate_average_brier(scores)


def convert_brier_to_calibration_score(avg_brier: float) -> float:
    """Module-level alias. See BrierScoreCalculator.convert_brier_to_calibration_score."""
    return BrierScoreCalculator.convert_brier_to_calibration_score(avg_brier)

"""
Rules-based weakness / bias detection over a user's decisions.

Deterministic by design: each detector is a pure function of the decision
history and returns either a WeaknessSignal or None. No AI, no randomness —
the structured output here is what an AI explanation layer would later
narrate, never the other way around.

Detected slugs reuse the existing bias vocabulary where it maps
(`overconfidence`, `underconfidence`) and add gamification-specific
process/reflection weaknesses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# Minimum resolved decisions before behavioral weaknesses are trustworthy.
MIN_SAMPLE = 5

# Overconfidence
HIGH_CONVICTION_GAP = 0.25          # confidence >= 0.75 or <= 0.25
MIN_HIGH_CONVICTION = 3
HIGH_CONVICTION_MISS_THRESHOLD = 0.40

# 50/50 clustering (underconfidence)
FIFTY_FIFTY_LOW = 0.40
FIFTY_FIFTY_HIGH = 0.60
FIFTY_FIFTY_CLUSTER_THRESHOLD = 0.50

# Falsification discipline
FALSIFICATION_MISSING_THRESHOLD = 0.60

# Reflection
REFLECTION_MIN_RATE = 0.30

# Process
PROCESS_SCORE_FLOOR = 50.0


@dataclass
class WeaknessSignal:
    slug: str
    title: str
    severity: float                       # 0..1, higher = worse
    detail: str
    sample_size: int
    metric: dict = field(default_factory=dict)


def _pct(x: float) -> int:
    return round(x * 100)


def detect_overconfidence(resolved: list) -> Optional[WeaknessSignal]:
    """
    High-conviction calls (>= 0.75 or <= 0.25) that went the other way. A
    "miss" is being confident in the wrong direction.
    """
    high = [d for d in resolved if abs(d.confidence - 0.5) >= HIGH_CONVICTION_GAP]
    if len(high) < MIN_HIGH_CONVICTION:
        return None

    misses = [d for d in high if (d.confidence > 0.5) != bool(d.outcome_binary)]
    miss_rate = len(misses) / len(high)
    if miss_rate < HIGH_CONVICTION_MISS_THRESHOLD:
        return None

    return WeaknessSignal(
        slug="overconfidence",
        title="Overconfidence on high-conviction calls",
        severity=round(miss_rate, 2),
        detail=(
            f"{_pct(miss_rate)}% of your {len(high)} high-conviction calls "
            f"resolved against you — your certainty is outrunning your accuracy."
        ),
        sample_size=len(high),
        metric={
            "high_conviction_miss_rate": round(miss_rate, 2),
            "high_conviction_count": len(high),
        },
    )


def detect_fifty_fifty_clustering(resolved: list) -> Optional[WeaknessSignal]:
    """Predictions huddling in the 40–60% band — refusing to commit."""
    n = len(resolved)
    if n < MIN_SAMPLE:
        return None

    mid = [d for d in resolved if FIFTY_FIFTY_LOW <= d.confidence <= FIFTY_FIFTY_HIGH]
    cluster_rate = len(mid) / n
    if cluster_rate < FIFTY_FIFTY_CLUSTER_THRESHOLD:
        return None

    return WeaknessSignal(
        slug="underconfidence",
        title="Clustering near 50/50",
        severity=round(cluster_rate, 2),
        detail=(
            f"{_pct(cluster_rate)}% of your calls sit between 40% and 60%. "
            f"50% means no opinion — commit when you have evidence."
        ),
        sample_size=n,
        metric={"fifty_fifty_rate": round(cluster_rate, 2)},
    )


def detect_weak_falsification(decisions: list) -> Optional[WeaknessSignal]:
    """Logging decisions without stating what would change your mind."""
    n = len(decisions)
    if n < MIN_SAMPLE:
        return None

    missing = [d for d in decisions if not d.falsification]
    missing_rate = len(missing) / n
    if missing_rate <= FALSIFICATION_MISSING_THRESHOLD:
        return None

    return WeaknessSignal(
        slug="weak_falsification_discipline",
        title="Weak falsification discipline",
        severity=round(missing_rate, 2),
        detail=(
            f"{_pct(missing_rate)}% of your decisions have no falsification "
            f"condition. Naming what would change your mind is where calibration "
            f"is trained."
        ),
        sample_size=n,
        metric={"falsification_missing_rate": round(missing_rate, 2)},
    )


def detect_reflection_avoidance(
    resolved: list, reviewed_count: int
) -> Optional[WeaknessSignal]:
    """Resolved decisions that never get reviewed."""
    n = len(resolved)
    if n < MIN_SAMPLE:
        return None

    review_rate = reviewed_count / n if n else 0.0
    if review_rate >= REFLECTION_MIN_RATE:
        return None

    return WeaknessSignal(
        slug="reflection_avoidance",
        title="Reflection avoidance",
        severity=round(1.0 - review_rate, 2),
        detail=(
            f"You've reviewed {reviewed_count} of {n} resolved decisions. "
            f"The learning is in the review — outcome tells you little without it."
        ),
        sample_size=n,
        metric={"review_rate": round(review_rate, 2), "reviewed_count": reviewed_count},
    )


def compute_metric(
    slug: str,
    *,
    resolved: list,
    all_decisions: list,
    reviewed_count: int,
) -> Optional[float]:
    """
    Raw metric value for a weakness slug, independent of any threshold. Used to
    capture baseline / post-intervention numbers so before/after comparison is
    honest even once the weakness drops below its detection threshold.
    """
    if slug == "overconfidence":
        high = [d for d in resolved if abs(d.confidence - 0.5) >= HIGH_CONVICTION_GAP]
        if not high:
            return None
        misses = [d for d in high if (d.confidence > 0.5) != bool(d.outcome_binary)]
        return round(len(misses) / len(high), 4)
    if slug == "underconfidence":
        if not resolved:
            return None
        mid = [d for d in resolved if FIFTY_FIFTY_LOW <= d.confidence <= FIFTY_FIFTY_HIGH]
        return round(len(mid) / len(resolved), 4)
    if slug == "weak_falsification_discipline":
        if not all_decisions:
            return None
        missing = [d for d in all_decisions if not d.falsification]
        return round(len(missing) / len(all_decisions), 4)
    if slug == "reflection_avoidance":
        if not resolved:
            return None
        return round(reviewed_count / len(resolved), 4)
    return None


def detect_weak_process(decisions: list, process_score: Optional[float]) -> Optional[WeaknessSignal]:
    """A low process score: thin reasoning / falsification across decisions."""
    if process_score is None or len(decisions) < MIN_SAMPLE:
        return None
    if process_score >= PROCESS_SCORE_FLOOR:
        return None

    severity = round((PROCESS_SCORE_FLOOR - process_score) / PROCESS_SCORE_FLOOR, 2)
    return WeaknessSignal(
        slug="weak_process_discipline",
        title="Weak process discipline",
        severity=max(0.0, min(1.0, severity)),
        detail=(
            f"Your process score is {round(process_score)} / 100. Add reasoning "
            f"and falsification when you log a decision to strengthen it."
        ),
        sample_size=len(decisions),
        metric={"process_score": round(process_score, 2)},
    )

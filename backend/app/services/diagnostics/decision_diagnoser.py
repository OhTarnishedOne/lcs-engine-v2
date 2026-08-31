"""
Decision diagnoser — aggregate deterministic weakness signals into a single
structured diagnosis of what a user should work on next.

This is the "Diagnose weakness" step of the lifecycle. It produces structured
output (a primary weakness plus supporting signals) that an AI tutor can later
narrate — the diagnosis itself never depends on an LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.gamification import (
    Decision,
    DecisionReview,
    DecisionStatus,
    UserGamificationProfile,
)
from app.services.diagnostics.bias_detector import (
    MIN_SAMPLE,
    WeaknessSignal,
    detect_fifty_fifty_clustering,
    detect_overconfidence,
    detect_reflection_avoidance,
    detect_weak_falsification,
    detect_weak_process,
)


@dataclass
class Diagnosis:
    state: str                                  # "building" | "active"
    resolved_count: int
    primary_weakness: Optional[str]
    summary: str
    signals: list[WeaknessSignal] = field(default_factory=list)


class DecisionDiagnoser:
    def __init__(self, db: Session):
        self.db = db

    def diagnose(self, user_id: UUID) -> Diagnosis:
        all_decisions = (
            self.db.query(Decision)
            .filter(Decision.user_id == user_id)
            .all()
        )
        resolved = [
            d
            for d in all_decisions
            if d.status == DecisionStatus.RESOLVED and d.outcome_binary is not None
        ]
        reviewed_count = (
            self.db.query(DecisionReview)
            .filter(DecisionReview.user_id == user_id)
            .count()
        )
        profile = (
            self.db.query(UserGamificationProfile)
            .filter(UserGamificationProfile.user_id == user_id)
            .first()
        )
        process_score = profile.process_score if profile else None

        if len(resolved) < MIN_SAMPLE:
            return Diagnosis(
                state="building",
                resolved_count=len(resolved),
                primary_weakness=None,
                summary=(
                    f"Resolve {MIN_SAMPLE - len(resolved)} more decision(s) to "
                    f"unlock your diagnosis."
                ),
                signals=[],
            )

        candidates = [
            detect_overconfidence(resolved),
            detect_fifty_fifty_clustering(resolved),
            detect_weak_falsification(all_decisions),
            detect_reflection_avoidance(resolved, reviewed_count),
            detect_weak_process(all_decisions, process_score),
        ]
        signals = [s for s in candidates if s is not None]
        # Stable sort by severity desc — detector order breaks ties.
        signals.sort(key=lambda s: s.severity, reverse=True)

        if not signals:
            return Diagnosis(
                state="active",
                resolved_count=len(resolved),
                primary_weakness=None,
                summary=(
                    "No clear weakness stands out right now — your process, "
                    "calibration, and reflection are holding up. Keep logging "
                    "and resolving decisions."
                ),
                signals=[],
            )

        primary = signals[0]
        summary = (
            f"Your biggest opportunity right now is {primary.title.lower()}. "
            f"{primary.detail}"
        )
        return Diagnosis(
            state="active",
            resolved_count=len(resolved),
            primary_weakness=primary.slug,
            summary=summary,
            signals=signals,
        )

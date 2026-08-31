"""
Training intervention service — the "Train weakness" step of the lifecycle.

Given a diagnosed weakness, prescribe a small, measurable mission, track
progress from real subsequent behavior, and — when it completes — capture the
weakness metric again so LCS can tell whether the intervention worked.

Progress is anchor-based (count of qualifying actions minus the count that
existed at start), so it never depends on timestamp precision.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models.gamification import (
    Decision,
    DecisionReview,
    DecisionStatus,
    UserGamificationProfile,
    UserTrainingIntervention,
)
from app.services.diagnostics.bias_detector import compute_metric
from app.services.diagnostics.decision_diagnoser import DecisionDiagnoser

# One mission per weakness. intervention_type drives how progress is counted.
INTERVENTION_CATALOG: dict[str, dict] = {
    "overconfidence": {
        "intervention_type": "premortem",
        "title": "Pre-mortem your high-conviction calls",
        "description": (
            "For your next 3 decisions at 70%+ confidence, write a falsification "
            "condition — one reason you might be wrong — before you commit."
        ),
        "target_count": 3,
        "metric_key": "high_conviction_miss_rate",
    },
    "weak_falsification_discipline": {
        "intervention_type": "falsification",
        "title": "Name what would change your mind",
        "description": (
            "For your next 3 decisions, write a falsification condition before "
            "you commit."
        ),
        "target_count": 3,
        "metric_key": "falsification_missing_rate",
    },
    "reflection_avoidance": {
        "intervention_type": "reflection",
        "title": "Close the loop",
        "description": "Review your next 3 resolved decisions before moving on.",
        "target_count": 3,
        "metric_key": "review_rate",
    },
    "underconfidence": {
        "intervention_type": "commit",
        "title": "Commit past 50/50",
        "description": (
            "For your next 3 decisions, push your estimate outside the 40–60% "
            "band and note the evidence that justifies it."
        ),
        "target_count": 3,
        "metric_key": "fifty_fifty_rate",
    },
}


class NoActionableWeaknessError(Exception):
    """No diagnosed weakness maps to a trainable intervention right now."""


@dataclass
class InterventionView:
    intervention: UserTrainingIntervention
    created: bool


class InterventionService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------ helpers

    def _gather(self, user_id: UUID):
        all_decisions = (
            self.db.query(Decision).filter(Decision.user_id == user_id).all()
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
        return all_decisions, resolved, reviewed_count

    def _current_metric(self, user_id: UUID, slug: str) -> Optional[float]:
        all_decisions, resolved, reviewed_count = self._gather(user_id)
        return compute_metric(
            slug,
            resolved=resolved,
            all_decisions=all_decisions,
            reviewed_count=reviewed_count,
        )

    def _count_qualifying(self, user_id: UUID, intervention_type: str) -> int:
        if intervention_type in ("premortem", "falsification"):
            query = self.db.query(Decision).filter(
                Decision.user_id == user_id,
                Decision.falsification.isnot(None),
            )
            if intervention_type == "premortem":
                query = query.filter(Decision.confidence >= 0.7)
            return query.count()
        if intervention_type == "reflection":
            return (
                self.db.query(DecisionReview)
                .filter(DecisionReview.user_id == user_id)
                .count()
            )
        if intervention_type == "commit":
            return (
                self.db.query(Decision)
                .filter(
                    Decision.user_id == user_id,
                    or_(Decision.confidence < 0.4, Decision.confidence > 0.6),
                )
                .count()
            )
        return 0

    def _sync_progress(self, intervention: UserTrainingIntervention) -> None:
        if intervention.status != "active":
            return

        total_qualifying = self._count_qualifying(
            intervention.user_id, intervention.intervention_type
        )
        progress = max(0, total_qualifying - intervention.baseline_qualifying_count)
        intervention.progress_count = min(progress, intervention.target_count)

        if progress >= intervention.target_count:
            intervention.status = "completed"
            intervention.completed_at = datetime.utcnow()
            intervention.post_metric = self._current_metric(
                intervention.user_id, intervention.weakness_slug
            )
        self.db.flush()

    # -------------------------------------------------------------------- reads

    def get_active(self, user_id: UUID) -> Optional[UserTrainingIntervention]:
        intervention = (
            self.db.query(UserTrainingIntervention)
            .filter(
                UserTrainingIntervention.user_id == user_id,
                UserTrainingIntervention.status == "active",
            )
            .order_by(UserTrainingIntervention.started_at.desc())
            .first()
        )
        if intervention is not None:
            self._sync_progress(intervention)
        return intervention

    def list_interventions(
        self, user_id: UUID, *, limit: int = 50, offset: int = 0
    ) -> list[UserTrainingIntervention]:
        return (
            self.db.query(UserTrainingIntervention)
            .filter(UserTrainingIntervention.user_id == user_id)
            .order_by(UserTrainingIntervention.started_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    # -------------------------------------------------------------------- start

    def start(
        self, user_id: UUID, weakness_slug: Optional[str] = None
    ) -> InterventionView:
        # One active mission at a time — return the existing one if present.
        active = self.get_active(user_id)
        if active is not None:
            return InterventionView(intervention=active, created=False)

        if weakness_slug is None:
            weakness_slug = DecisionDiagnoser(self.db).diagnose(user_id).primary_weakness

        if not weakness_slug or weakness_slug not in INTERVENTION_CATALOG:
            raise NoActionableWeaknessError(str(weakness_slug))

        spec = INTERVENTION_CATALOG[weakness_slug]
        intervention = UserTrainingIntervention(
            user_id=user_id,
            weakness_slug=weakness_slug,
            intervention_type=spec["intervention_type"],
            title=spec["title"],
            description=spec["description"],
            target_count=spec["target_count"],
            progress_count=0,
            baseline_qualifying_count=self._count_qualifying(
                user_id, spec["intervention_type"]
            ),
            status="active",
            metric_key=spec["metric_key"],
            baseline_metric=self._current_metric(user_id, weakness_slug),
            started_at=datetime.utcnow(),
        )
        self.db.add(intervention)
        self.db.flush()
        return InterventionView(intervention=intervention, created=True)

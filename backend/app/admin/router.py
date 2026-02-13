from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..deps import get_db
from ..db.models import UserProfile
from .schemas import OnboardingStatsResponse, DistributionItem

router = APIRouter(prefix="/admin", tags=["admin"])


def _distribution(db: Session, column, extra_filter=None) -> list[DistributionItem]:
    q = db.query(column, func.count()).filter(column.isnot(None))
    if extra_filter is not None:
        q = q.filter(extra_filter)
    return [DistributionItem(value=val, count=cnt) for val, cnt in q.group_by(column).all()]


@router.get("/onboarding-stats", response_model=OnboardingStatsResponse)
def get_onboarding_stats(db: Session = Depends(get_db)) -> OnboardingStatsResponse:
    """Aggregate onboarding analytics (no auth required)."""
    total_started = db.query(func.count(UserProfile.id)).scalar() or 0
    total_completed = (
        db.query(func.count(UserProfile.id))
        .filter(UserProfile.onboarding_completed.is_(True))
        .scalar()
        or 0
    )
    completion_rate = (total_completed / total_started * 100) if total_started > 0 else 0.0

    completed_filter = UserProfile.onboarding_completed.is_(True)

    persona_dist = _distribution(db, UserProfile.persona, completed_filter)
    experience_dist = _distribution(db, UserProfile.experience_level, completed_filter)
    barrier_dist = _distribution(db, UserProfile.biggest_barrier, completed_filter)
    goal_dist = _distribution(db, UserProfile.primary_goal, completed_filter)

    # Average time to complete (Python-side for SQLite compatibility)
    completed_profiles = (
        db.query(UserProfile)
        .filter(
            completed_filter,
            UserProfile.onboarding_completed_at.isnot(None),
            UserProfile.created_at.isnot(None),
        )
        .all()
    )
    avg_completion_seconds = None
    if completed_profiles:
        deltas = []
        for p in completed_profiles:
            if p.onboarding_completed_at and p.created_at:
                delta = (p.onboarding_completed_at - p.created_at).total_seconds()
                if delta > 0:
                    deltas.append(delta)
        if deltas:
            avg_completion_seconds = sum(deltas) / len(deltas)

    return OnboardingStatsResponse(
        total_started=total_started,
        total_completed=total_completed,
        completion_rate=round(completion_rate, 1),
        persona_distribution=persona_dist,
        experience_level_distribution=experience_dist,
        biggest_barrier_distribution=barrier_dist,
        primary_goal_distribution=goal_dist,
        avg_completion_seconds=avg_completion_seconds,
    )

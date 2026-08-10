"""
Training intervention API.

    POST /api/interventions          start a mission (from the diagnosis, or an
                                     explicit weakness_slug)
    GET  /api/interventions/active   the current active mission, progress synced
    GET  /api/interventions          mission history

Prefix is assigned in main.py: app.include_router(interventions_router, prefix="/api/interventions")
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..db.models import User
from ..deps import get_current_user, get_db
from ..gamification.user_ids import user_id_to_uuid
from ..services.interventions.intervention_service import (
    InterventionService,
    NoActionableWeaknessError,
)
from .schemas import (
    InterventionListResponse,
    InterventionResponse,
    InterventionStartRequest,
    InterventionStartResponse,
)

router = APIRouter(tags=["interventions"])


def _user_uuid(user: User) -> UUID:
    return user_id_to_uuid(user.id)


@router.post("", response_model=InterventionStartResponse)
def start_intervention(
    payload: InterventionStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterventionStartResponse:
    """
    Start a training mission. If one is already active it is returned as-is
    (one mission at a time). With no weakness_slug, the diagnosis' primary
    weakness is used; 409 if there is nothing actionable to train yet.
    """
    service = InterventionService(db)
    try:
        view = service.start(_user_uuid(current_user), payload.weakness_slug)
    except NoActionableWeaknessError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No actionable weakness to train yet.",
        )
    db.commit()
    db.refresh(view.intervention)
    return InterventionStartResponse(
        created=view.created,
        intervention=InterventionResponse.model_validate(view.intervention),
    )


@router.get("/active", response_model=InterventionResponse)
def get_active_intervention(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterventionResponse:
    service = InterventionService(db)
    intervention = service.get_active(_user_uuid(current_user))
    db.commit()  # persist any progress/auto-completion from the sync
    if intervention is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active intervention.",
        )
    return InterventionResponse.model_validate(intervention)


@router.get("", response_model=InterventionListResponse)
def list_interventions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterventionListResponse:
    service = InterventionService(db)
    interventions = service.list_interventions(
        _user_uuid(current_user), limit=limit, offset=offset
    )
    return InterventionListResponse(
        total=len(interventions),
        interventions=[
            InterventionResponse.model_validate(i) for i in interventions
        ],
    )

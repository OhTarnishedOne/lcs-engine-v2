"""
Canonical Decision API.

    POST   /api/decisions            create (log) a decision
    GET    /api/decisions            list the caller's decisions
    GET    /api/decisions/{id}       fetch one
    PATCH  /api/decisions/{id}       partial update (confidence-lock enforced)
    POST   /api/decisions/{id}/resolve  resolve + run the scoring pipeline

Prefix is assigned in main.py: app.include_router(decisions_router, prefix="/api/decisions")
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..db.models import User
from ..db.models.gamification import DecisionStatus
from ..deps import get_current_user, get_db
from ..gamification.user_ids import user_id_to_uuid
from ..services.decisions.decision_service import (
    DecisionLockedError,
    DecisionNotFoundError,
    DecisionService,
)
from .schemas import (
    DecisionCreateRequest,
    DecisionListResponse,
    DecisionResolveRequest,
    DecisionResolveResponse,
    DecisionResponse,
    DecisionUpdateRequest,
)

router = APIRouter(tags=["decisions"])

DECISION_LOCKED_DETAIL = "Decision is locked and cannot be modified"
DECISION_NOT_FOUND_DETAIL = "Decision not found."


def _user_uuid(user: User) -> UUID:
    return user_id_to_uuid(user.id)


@router.post("", response_model=DecisionResponse, status_code=status.HTTP_201_CREATED)
def create_decision(
    payload: DecisionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DecisionResponse:
    service = DecisionService(db)
    decision = service.create_decision(
        user_id=_user_uuid(current_user),
        question=payload.question,
        confidence=payload.confidence,
        domain=payload.domain,
        reasoning=payload.reasoning,
        falsification=payload.falsification,
        resolution_date=payload.resolution_date,
        is_curated=payload.is_curated,
        question_id=payload.question_id,
        lock=payload.lock,
    )
    db.commit()
    db.refresh(decision)
    return DecisionResponse.model_validate(decision)


@router.get("", response_model=DecisionListResponse)
def list_decisions(
    status_filter: Optional[DecisionStatus] = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DecisionListResponse:
    service = DecisionService(db)
    decisions = service.list_decisions(
        _user_uuid(current_user),
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return DecisionListResponse(
        total=len(decisions),
        decisions=[DecisionResponse.model_validate(d) for d in decisions],
    )


@router.get("/{decision_id}", response_model=DecisionResponse)
def get_decision(
    decision_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DecisionResponse:
    service = DecisionService(db)
    try:
        decision = service.get_decision(decision_id, _user_uuid(current_user))
    except DecisionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=DECISION_NOT_FOUND_DETAIL,
        )
    return DecisionResponse.model_validate(decision)


@router.patch("/{decision_id}", response_model=DecisionResponse)
def update_decision(
    decision_id: UUID,
    payload: DecisionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DecisionResponse:
    """
    Partial update. Once `locked_at` is set, any attempt to modify
    `confidence`, `reasoning`, or `falsification` is rejected with HTTP 400.
    """
    service = DecisionService(db)
    try:
        decision = service.get_decision(decision_id, _user_uuid(current_user))
    except DecisionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=DECISION_NOT_FOUND_DETAIL,
        )

    changes = payload.model_dump(exclude_unset=True)
    try:
        service.update_decision(decision, changes)
    except DecisionLockedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=DECISION_LOCKED_DETAIL,
        )

    db.commit()
    db.refresh(decision)
    return DecisionResponse.model_validate(decision)


@router.post("/{decision_id}/resolve", response_model=DecisionResolveResponse)
def resolve_decision(
    decision_id: UUID,
    payload: DecisionResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DecisionResolveResponse:
    """
    Resolve a decision and run the full scoring pipeline (Brier -> score
    families -> badges). Idempotent: re-resolving returns the stored state
    without recomputing or double-counting.
    """
    service = DecisionService(db)
    try:
        decision = service.get_decision(decision_id, _user_uuid(current_user))
    except DecisionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=DECISION_NOT_FOUND_DETAIL,
        )

    result = service.resolve_decision(
        decision,
        outcome_binary=payload.outcome_binary,
        outcome_source=payload.outcome_source,
        outcome_notes=payload.outcome_notes,
    )
    db.commit()
    db.refresh(decision)

    score_update = result.score_update
    badge_result = result.badge_result
    return DecisionResolveResponse(
        decision_id=decision.id,
        already_resolved=result.already_resolved,
        brier_score=decision.brier_score,
        is_calibrated=(result.brier.is_calibrated if result.brier else None),
        calibration_score=(
            score_update.calibration_score if score_update else None
        ),
        tier=(score_update.new_tier.value if score_update else None),
        tier_advanced=(score_update.tier_advanced if score_update else False),
        badges_awarded=(
            [slug.value for slug in badge_result.badges_earned]
            if badge_result
            else []
        ),
    )

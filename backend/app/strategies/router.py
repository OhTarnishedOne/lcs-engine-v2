"""
Strategy Router

API endpoints for AI-generated investment strategies.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user, get_ai_client
from ..db.models import User
from ..integrations import ResilientAIClient
from ..common.errors import NotFoundError, BadRequestError
from .service import StrategyService, VALID_STRATEGY_TYPES
from .schemas import (
    StrategyGenerateRequest,
    StrategyResponse,
    StrategyListResponse,
    StrategyCompareRequest,
    StrategyCompareResponse,
    StrategyExplainRequest,
    StrategyExplainResponse,
    AssetAllocation,
)

router = APIRouter(tags=["strategies"])


def get_strategy_service(
    db: Session = Depends(get_db),
    ai_client: ResilientAIClient = Depends(get_ai_client)
) -> StrategyService:
    return StrategyService(db, ai_client)


def strategy_to_response(strategy) -> StrategyResponse:
    """Convert Strategy model to response schema."""
    assets = [
        AssetAllocation(
            ticker=a.get('ticker', ''),
            name=a.get('name', ''),
            allocation_pct=a.get('allocation_pct', 0),
            rationale=a.get('rationale', '')
        )
        for a in (strategy.assets or [])
    ]
    return StrategyResponse(
        id=strategy.id,
        name=strategy.name,
        description=strategy.description,
        strategy_type=strategy.strategy_type,
        risk_level=strategy.risk_level,
        time_horizon=strategy.time_horizon,
        assets=assets,
        rationale=strategy.rationale,
        risks=strategy.risks,
        learning_points=strategy.learning_points or [],
        created_at=strategy.created_at
    )


@router.post("/generate", response_model=StrategyResponse)
async def generate_strategy(
    request: StrategyGenerateRequest = None,
    current_user: User = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service),
) -> StrategyResponse:
    """
    Generate a new AI-powered investment strategy.

    If strategy_type is not provided, it will be auto-selected based on the user's profile.
    Valid strategy types: value, growth, income, momentum, balanced, index
    """
    if request is None:
        request = StrategyGenerateRequest()

    try:
        strategy = await service.generate_strategy(
            user_id=current_user.id,
            strategy_type=request.strategy_type,
            preferences=request.preferences
        )
        return strategy_to_response(strategy)
    except ValueError as e:
        error_msg = str(e)
        if "Invalid strategy type" in error_msg:
            raise BadRequestError(f"Invalid strategy type. Must be one of: {', '.join(VALID_STRATEGY_TYPES)}")
        elif "Maximum of 10 strategies" in error_msg:
            raise BadRequestError(error_msg)
        else:
            raise HTTPException(status_code=500, detail=error_msg)


@router.get("", response_model=StrategyListResponse)
def list_strategies(
    current_user: User = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service),
) -> StrategyListResponse:
    """List all strategies for the current user."""
    strategies = service.get_strategies(current_user.id)
    return StrategyListResponse(
        strategies=[strategy_to_response(s) for s in strategies],
        total=len(strategies)
    )


@router.get("/{strategy_id}", response_model=StrategyResponse)
def get_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service),
) -> StrategyResponse:
    """Get a specific strategy by ID."""
    strategy = service.get_strategy(current_user.id, strategy_id)
    if not strategy:
        raise NotFoundError("Strategy not found")
    return strategy_to_response(strategy)


@router.delete("/{strategy_id}")
def delete_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service),
) -> dict:
    """Delete a strategy."""
    deleted = service.delete_strategy(current_user.id, strategy_id)
    if not deleted:
        raise NotFoundError("Strategy not found")
    return {"deleted": True, "strategy_id": strategy_id}


@router.post("/compare", response_model=StrategyCompareResponse)
async def compare_strategies(
    request: StrategyCompareRequest,
    current_user: User = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service),
) -> StrategyCompareResponse:
    """
    Compare 2-3 strategies side by side with AI analysis.
    """
    try:
        comparison = await service.compare_strategies(
            user_id=current_user.id,
            strategy_ids=request.strategy_ids
        )

        # Load full strategy details for response
        strategies = []
        for sid in comparison.strategy_ids:
            strategy = service.get_strategy(current_user.id, sid)
            if strategy:
                strategies.append(strategy_to_response(strategy))

        return StrategyCompareResponse(
            id=comparison.id,
            strategies=strategies,
            comparison_text=comparison.comparison_text,
            created_at=comparison.created_at
        )
    except ValueError as e:
        raise BadRequestError(str(e))


@router.post("/{strategy_id}/explain", response_model=StrategyExplainResponse)
async def explain_strategy(
    strategy_id: str,
    request: StrategyExplainRequest,
    current_user: User = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service),
) -> StrategyExplainResponse:
    """
    Get AI explanation for a specific question about a strategy.
    """
    try:
        explanation = await service.explain_strategy(
            user_id=current_user.id,
            strategy_id=strategy_id,
            question=request.question
        )
        return StrategyExplainResponse(
            strategy_id=strategy_id,
            question=request.question,
            explanation=explanation
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise NotFoundError("Strategy not found")
        raise HTTPException(status_code=500, detail=str(e))

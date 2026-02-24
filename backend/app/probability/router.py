"""
Probability Lab Router

API endpoints for prediction markets and calibration.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user, get_kalshi_client
from ..db.models import User
from ..integrations import KalshiClient
from ..integrations.fred import FredClient
from ..settings import get_settings
from .service import ProbabilityService
from .resolution import MarketAutomation
from .schemas import (
    MarketResponse,
    MarketListResponse,
    SubmitPredictionRequest,
    PredictionResponse,
    PredictionListResponse,
    CalibrationResponse,
    CalibrationBucket,
    BiasInfo,
)

router = APIRouter(tags=["probability"])


def get_probability_service(
    db: Session = Depends(get_db),
    kalshi: KalshiClient = Depends(get_kalshi_client),
) -> ProbabilityService:
    return ProbabilityService(db, kalshi)


@router.get("/markets", response_model=MarketListResponse)
async def get_markets(
    current_user: User = Depends(get_current_user),
    service: ProbabilityService = Depends(get_probability_service),
) -> MarketListResponse:
    """List active prediction markets."""
    markets = await service.get_active_markets()

    # Hide market probability in list view (anti-anchoring)
    return MarketListResponse(
        markets=[
            MarketResponse(
                id=m.id,
                title=m.title,
                description=m.description,
                category=m.category,
                market_probability=None,  # Hidden until after prediction
                close_date=m.close_date,
                is_resolved=m.is_resolved,
                resolution=m.resolution,
                explainer=m.explainer,
                investing_connection=m.investing_connection,
            )
            for m in markets
        ],
        total=len(markets),
    )


@router.get("/markets/{market_id}", response_model=MarketResponse)
async def get_market(
    market_id: str,
    current_user: User = Depends(get_current_user),
    service: ProbabilityService = Depends(get_probability_service),
) -> MarketResponse:
    """Get market details. Probability hidden until user has predicted."""
    market = service.get_market(market_id)
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    # Check if user has already predicted
    from ..db.models import UserPrediction
    has_predicted = service.db.query(UserPrediction).filter(
        UserPrediction.user_id == current_user.id,
        UserPrediction.market_id == market_id,
    ).first() is not None

    return MarketResponse(
        id=market.id,
        title=market.title,
        description=market.description,
        category=market.category,
        market_probability=market.market_probability if has_predicted else None,
        close_date=market.close_date,
        is_resolved=market.is_resolved,
        resolution=market.resolution,
        explainer=market.explainer,
        investing_connection=market.investing_connection,
    )


@router.post("/predictions", response_model=PredictionResponse)
async def submit_prediction(
    request: SubmitPredictionRequest,
    current_user: User = Depends(get_current_user),
    service: ProbabilityService = Depends(get_probability_service),
) -> PredictionResponse:
    """
    Submit a prediction.
    Market probability is revealed AFTER submission (anti-anchoring).
    """
    try:
        prediction, market = await service.submit_prediction(
            user_id=current_user.id,
            market_id=request.market_id,
            probability=request.probability,
            reasoning=request.reasoning,
        )

        return PredictionResponse(
            id=prediction.id,
            market_id=prediction.market_id,
            market_title=market.title,
            predicted_probability=prediction.predicted_probability,
            market_probability=market.market_probability or 0.5,
            reasoning=prediction.reasoning,
            brier_score=prediction.brier_score,
            is_resolved=market.is_resolved,
            resolution=market.resolution,
            created_at=prediction.created_at,
        )
    except ValueError as e:
        error_msg = str(e)
        if "already predicted" in error_msg.lower():
            raise HTTPException(status_code=409, detail=error_msg)
        if "closed" in error_msg.lower():
            raise HTTPException(status_code=400, detail=error_msg)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)


@router.get("/predictions", response_model=PredictionListResponse)
async def get_predictions(
    status: str = Query(default="all", pattern="^(all|pending|resolved)$"),
    current_user: User = Depends(get_current_user),
    service: ProbabilityService = Depends(get_probability_service),
) -> PredictionListResponse:
    """Get user's predictions. Status: all, pending, resolved."""
    predictions = await service.get_user_predictions(current_user.id, status)
    return PredictionListResponse(
        predictions=[PredictionResponse(**p) for p in predictions],
        total=len(predictions),
    )


@router.get("/calibration", response_model=CalibrationResponse)
async def get_calibration(
    current_user: User = Depends(get_current_user),
    service: ProbabilityService = Depends(get_probability_service),
) -> CalibrationResponse:
    """Get user's calibration and bias report."""
    data = await service.get_calibration(current_user.id)

    return CalibrationResponse(
        total_predictions=data["total_predictions"],
        resolved_predictions=data["resolved_predictions"],
        average_brier_score=data["average_brier_score"],
        calibration_curve=[
            CalibrationBucket(**b) for b in data["calibration_curve"]
        ],
        detected_biases=[
            BiasInfo(**b) for b in data["detected_biases"]
        ],
    )


@router.post("/resolve-check")
async def check_resolutions(
    current_user: User = Depends(get_current_user),
    service: ProbabilityService = Depends(get_probability_service),
    db: Session = Depends(get_db),
) -> dict:
    """Trigger a manual resolution check for all pending FRED-backed markets."""
    settings = get_settings()
    if not settings.fred_api_key:
        return {
            "message": "FRED API key not configured",
            "resolved_markets": 0,
            "checked_markets": 0,
        }

    fred = FredClient(api_key=settings.fred_api_key)
    try:
        automation = MarketAutomation(db, fred, service)
        result = await automation.check_and_resolve()
        return {
            "message": "Resolution check complete",
            "resolved_markets": len(result["resolved"]),
            "checked_markets": result["checked"],
        }
    finally:
        await fred.close()

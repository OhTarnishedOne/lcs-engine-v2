"""
Probability Lab Router

API endpoints for prediction markets and calibration.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user, get_kalshi_client, get_ai_client
from ..db.models import User, UserProfile
from ..integrations import KalshiClient, ResilientAIClient
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
    MacroStrategyRequest,
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


@router.post("/macro-strategy")
async def get_macro_strategy(
    request: MacroStrategyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_client: ResilientAIClient = Depends(get_ai_client),
):
    """
    Given a user's macro prediction, generate a hypothetical
    investment strategy based on that view + their archetype.
    Pro only.
    """
    if current_user.tier != "pro":
        raise HTTPException(status_code=402, detail="Pro required")

    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()

    archetype = profile.persona if profile else "Balanced Builder"
    risk = profile.risk_tolerance if profile else "moderate"

    prompt = _build_macro_strategy_prompt(
        market_title=request.market_title,
        user_prediction=request.user_prediction,
        archetype=archetype,
        risk_tolerance=risk,
    )

    import json as _json

    response = await ai_client.chat_json(
        messages=[{"role": "user", "content": prompt}],
        system_prompt="You are a financial educator. Respond with valid JSON only.",
    )

    # Frontend expects a JSON string to parse
    return {"strategy": _json.dumps(response)}


def _build_macro_strategy_prompt(
    market_title: str,
    user_prediction: float,
    archetype: str,
    risk_tolerance: str,
) -> str:
    if user_prediction >= 65:
        direction = "likely to come in above expectations (inflationary)"
        implication = "persistent inflation, Fed staying hawkish longer"
    elif user_prediction <= 35:
        direction = "likely to come in below expectations (disinflationary)"
        implication = "cooling inflation, potential for Fed rate cuts"
    else:
        direction = "likely to come in roughly in line with expectations"
        implication = "a soft landing scenario with moderate growth"

    return f"""You are a financial educator helping a user understand how their
macro prediction connects to portfolio strategy.

The user predicted: {market_title}
Their view: {direction} (probability: {user_prediction}%)
Macro implication: {implication}

The user's investor archetype: {archetype}
Their risk tolerance: {risk_tolerance}

Generate a SHORT hypothetical portfolio strategy (not financial advice) that
reflects this macro view, adjusted for their archetype and risk tolerance.

Format your response as JSON with this exact structure:
{{
  "thesis": "One sentence macro thesis based on their prediction",
  "assets": [
    {{"name": "Asset class or ETF example", "allocation": 30, "rationale": "Why this fits the thesis"}},
    {{"name": "...", "allocation": 25, "rationale": "..."}},
    {{"name": "...", "allocation": 25, "rationale": "..."}},
    {{"name": "...", "allocation": 20, "rationale": "..."}}
  ],
  "risk_note": "One sentence on what could invalidate this thesis",
  "learning_point": "One sentence connecting this to a core investing concept"
}}

Be educational, not prescriptive. This is a learning exercise, not a
recommendation. Keep each rationale under 15 words."""


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

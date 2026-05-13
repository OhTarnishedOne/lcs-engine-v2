"""
Trading Router

API endpoints for paper trading.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user, get_alpaca_client, get_polygon_client
from ..db.models import User
from ..integrations import AlpacaClient, PolygonClient
from .service import TradingService
from .schemas import (
    PlaceOrderRequest,
    OrderResponse,
    PositionResponse,
    PortfolioResponse,
    PortfolioHistoryResponse,
    SymbolSearchResponse,
    QuoteResponse,
    CompanyInfoResponse,
    TradeHistoryResponse,
)

router = APIRouter(tags=["trading"])


def get_trading_service(
    db: Session = Depends(get_db),
    alpaca: Optional[AlpacaClient] = Depends(get_alpaca_client),
    polygon: Optional[PolygonClient] = Depends(get_polygon_client),
) -> TradingService:
    return TradingService(db, alpaca, polygon)


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio(
    current_user: User = Depends(get_current_user),
    service: TradingService = Depends(get_trading_service),
) -> PortfolioResponse:
    """Get full portfolio with account balance and positions."""
    try:
        if current_user.is_guest:
            portfolio = await service.get_guest_portfolio(current_user.id)
        else:
            portfolio = await service.get_portfolio(current_user.id)
        return PortfolioResponse(
            equity=portfolio["equity"],
            cash=portfolio["cash"],
            buying_power=portfolio["buying_power"],
            total_pl=portfolio["total_pl"],
            total_pl_pct=portfolio["total_pl_pct"],
            positions=[PositionResponse(**p) for p in portfolio["positions"]],
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio: {e}")


@router.get("/positions", response_model=list[PositionResponse])
async def get_positions(
    current_user: User = Depends(get_current_user),
    service: TradingService = Depends(get_trading_service),
) -> list[PositionResponse]:
    """Get current open positions."""
    try:
        if current_user.is_guest:
            positions = await service.get_guest_positions(current_user.id)
        else:
            positions = await service.get_positions()
        return [PositionResponse(**p) for p in positions]
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get positions: {e}")


@router.get("/positions/{symbol}", response_model=PositionResponse)
async def get_position(
    symbol: str,
    current_user: User = Depends(get_current_user),
    service: TradingService = Depends(get_trading_service),
) -> PositionResponse:
    """Get a single position by symbol."""
    try:
        position = await service.get_position(symbol)
        if not position:
            raise HTTPException(status_code=404, detail=f"No position in {symbol}")
        return PositionResponse(**position)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get position: {e}")


@router.post("/orders", response_model=OrderResponse)
async def place_order(
    request: PlaceOrderRequest,
    current_user: User = Depends(get_current_user),
    service: TradingService = Depends(get_trading_service),
) -> OrderResponse:
    """Place a paper trade order."""
    # Validate limit order has price
    if request.order_type == "limit" and request.limit_price is None:
        raise HTTPException(
            status_code=400,
            detail="Limit orders require a limit_price"
        )

    try:
        if current_user.is_guest:
            trade = await service.place_guest_order(
                user_id=current_user.id,
                symbol=request.symbol,
                qty=request.qty,
                side=request.side,
                order_type=request.order_type,
                limit_price=request.limit_price,
            )
        else:
            trade = await service.place_order(
                user_id=current_user.id,
                symbol=request.symbol,
                qty=request.qty,
                side=request.side,
                order_type=request.order_type,
                limit_price=request.limit_price,
                strategy_id=request.strategy_id,
                reasoning=request.reasoning,
            )
        return OrderResponse(
            id=trade.id,
            alpaca_order_id=trade.alpaca_order_id,
            symbol=trade.symbol,
            side=trade.side,
            qty=trade.qty,
            order_type=trade.order_type,
            status=trade.status,
            limit_price=trade.limit_price,
            filled_price=trade.filled_price,
            created_at=trade.created_at,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_msg = str(e).lower()
        if "insufficient" in error_msg or "buying power" in error_msg:
            raise HTTPException(status_code=400, detail="Insufficient buying power")
        if "symbol" in error_msg and "not found" in error_msg:
            raise HTTPException(status_code=400, detail=f"Invalid symbol: {request.symbol}")
        raise HTTPException(status_code=500, detail=f"Failed to place order: {e}")


@router.get("/orders", response_model=list[dict])
async def get_orders(
    status: str = Query(default="all", pattern="^(open|closed|all)$"),
    current_user: User = Depends(get_current_user),
    service: TradingService = Depends(get_trading_service),
) -> list[dict]:
    """List orders. Status: open, closed, all."""
    try:
        if current_user.is_guest:
            # Guests have no Alpaca orders — return trade log as order history
            trades = service.get_trade_history(current_user.id)
            return [
                {"id": t.id, "symbol": t.symbol, "side": t.side, "qty": t.qty,
                 "order_type": t.order_type, "status": t.status, "filled_price": t.filled_price,
                 "created_at": t.created_at.isoformat() if t.created_at else None}
                for t in trades
            ]
        return await service.get_orders(status)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get orders: {e}")


@router.delete("/orders/{order_id}")
async def cancel_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    service: TradingService = Depends(get_trading_service),
) -> dict:
    """Cancel an open order."""
    try:
        return await service.cancel_order(order_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            raise HTTPException(status_code=404, detail="Order not found")
        raise HTTPException(status_code=500, detail=f"Failed to cancel order: {e}")


@router.get("/history", response_model=list[TradeHistoryResponse])
def get_trade_history(
    current_user: User = Depends(get_current_user),
    service: TradingService = Depends(get_trading_service),
) -> list[TradeHistoryResponse]:
    """Get trade history from local log."""
    trades = service.get_trade_history(current_user.id)
    return [
        TradeHistoryResponse(
            id=t.id,
            symbol=t.symbol,
            side=t.side,
            qty=t.qty,
            order_type=t.order_type,
            status=t.status,
            filled_price=t.filled_price,
            strategy_id=t.strategy_id,
            reasoning=t.reasoning,
            created_at=t.created_at,
        )
        for t in trades
    ]


@router.get("/portfolio/chart", response_model=PortfolioHistoryResponse)
async def get_portfolio_chart(
    period: str = Query(default="1M", pattern="^(1D|1W|1M|3M|1Y)$"),
    current_user: User = Depends(get_current_user),
    service: TradingService = Depends(get_trading_service),
) -> PortfolioHistoryResponse:
    """Get portfolio value history for charting."""
    try:
        history = await service.get_portfolio_history(period)
        return PortfolioHistoryResponse(**history)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio history: {e}")


@router.get("/search", response_model=list[SymbolSearchResponse])
async def search_symbols(
    q: str = Query(..., min_length=1, max_length=50),
    current_user: User = Depends(get_current_user),
    service: TradingService = Depends(get_trading_service),
) -> list[SymbolSearchResponse]:
    """Search for stock/ETF symbols."""
    try:
        results = await service.search_symbols(q)
        return [SymbolSearchResponse(**r) for r in results]
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search symbols: {e}")


@router.get("/quote/{symbol}", response_model=QuoteResponse)
async def get_quote(
    symbol: str,
    current_user: User = Depends(get_current_user),
    service: TradingService = Depends(get_trading_service),
) -> QuoteResponse:
    """Get latest quote for a symbol."""
    try:
        quote = await service.get_quote(symbol)
        return QuoteResponse(**quote)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get quote: {e}")


@router.get("/company/{symbol}", response_model=CompanyInfoResponse)
async def get_company_info(
    symbol: str,
    current_user: User = Depends(get_current_user),
    service: TradingService = Depends(get_trading_service),
) -> CompanyInfoResponse:
    """Get company information."""
    try:
        info = await service.get_company_info(symbol)
        return CompanyInfoResponse(**info)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get company info: {e}")

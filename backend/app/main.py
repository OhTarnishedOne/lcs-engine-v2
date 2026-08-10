import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .settings import get_settings
from .database import SessionLocal
from .auth.router import router as auth_router
from .auth.demo import router as demo_router
from .users.router import router as users_router
from .onboarding.router import router as onboarding_router
from .chat.router import router as chat_router
from .strategies.router import router as strategies_router
from .trading.router import router as trading_router
from .probability.router import router as probability_router
from .decisions.router import router as decisions_router
from .probability.service import ProbabilityService
from .probability.background import market_automation_loop
from .gamification.router import router as gamification_router
from .billing.router import router as billing_router
from .admin.router import router as admin_router
from .admin.dashboard import router as admin_dashboard_router
from .analytics.router import router as analytics_router

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events.

    IMPORTANT: Startup must be fast and never block on external APIs.
    FRED backfill and resolution run in the background loop instead.
    """
    # Startup: seed prediction markets (local DB only — fast)
    db = SessionLocal()
    try:
        service = ProbabilityService(db)
        service.seed_markets_if_empty()
    finally:
        db.close()

    # Start background market automation (handles backfill + resolution + cleanup)
    task = None
    if settings.fred_api_key:
        task = asyncio.create_task(market_automation_loop())
        logger.info("Started market automation background task")

    yield

    # Shutdown: cancel background task
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="LCS Engine API",
    description="Backend API for LCS Engine - Investment Learning Platform",
    version="0.5.0",
    lifespan=lifespan,
)

# CORS configuration
origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(demo_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(onboarding_router, prefix="/api")
app.include_router(chat_router, prefix="/api/chat")
app.include_router(strategies_router, prefix="/api/strategies")
app.include_router(trading_router, prefix="/api/trading")
app.include_router(probability_router, prefix="/api/probability")
app.include_router(billing_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(admin_dashboard_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(gamification_router, prefix="/api/gamification")
app.include_router(decisions_router, prefix="/api/decisions")


@app.get("/")
def root():
    return {"message": "LCS Engine API", "version": "0.5.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}

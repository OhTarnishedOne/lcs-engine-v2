from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .settings import get_settings
from .auth.router import router as auth_router
from .users.router import router as users_router
from .onboarding.router import router as onboarding_router

settings = get_settings()

app = FastAPI(
    title="LCS Engine API",
    description="Backend API for LCS Engine - Investment Learning Platform",
    version="0.2.0",
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
app.include_router(users_router, prefix="/api")
app.include_router(onboarding_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "LCS Engine API", "version": "0.2.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}

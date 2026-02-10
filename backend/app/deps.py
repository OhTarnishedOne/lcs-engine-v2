from typing import Generator

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .database import SessionLocal
from .auth.utils import verify_token
from .common.errors import UnauthorizedError
from .db.models import User
from .integrations import AnthropicClient, OpenAIFallbackClient, ResilientAIClient
from .settings import get_settings

security = HTTPBearer()
settings = get_settings()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = verify_token(token, token_type="access")

    if not payload:
        raise UnauthorizedError("Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UnauthorizedError("User not found")

    return user


def get_anthropic_client() -> AnthropicClient:
    """Get the Anthropic client for AI chat (legacy, use get_ai_client instead)."""
    return AnthropicClient()


def get_ai_client() -> ResilientAIClient:
    """
    Get the resilient AI client with automatic fallback.

    Primary: Anthropic Claude
    Fallback: OpenAI GPT-4o (only if OPENAI_API_KEY is configured)
    """
    anthropic = AnthropicClient()

    openai_fallback = None
    if settings.openai_api_key:
        openai_fallback = OpenAIFallbackClient(api_key=settings.openai_api_key)

    return ResilientAIClient(
        anthropic_client=anthropic,
        openai_client=openai_fallback,
    )

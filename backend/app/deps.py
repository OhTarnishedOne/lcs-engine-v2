from typing import Generator

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .database import SessionLocal
from .auth.utils import verify_token
from .common.errors import UnauthorizedError
from .db.models import User
from .integrations import AnthropicClient

security = HTTPBearer()


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
    """Get the Anthropic client for AI chat."""
    return AnthropicClient()

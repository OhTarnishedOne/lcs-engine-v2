from datetime import datetime, timedelta, UTC
from typing import Any
import hashlib

from jose import jwt, JWTError
import bcrypt

from ..settings import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    # Pre-hash with SHA256 to handle long passwords (bcrypt has 72 byte limit)
    password_bytes = hashlib.sha256(password.encode()).digest()
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = hashlib.sha256(plain_password.encode()).digest()
    return bcrypt.checkpw(password_bytes, hashed_password.encode())


def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_token(token: str, token_type: str = "access") -> dict[str, Any] | None:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None

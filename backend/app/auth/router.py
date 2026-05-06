import logging
import os
import secrets
from datetime import datetime, timedelta, UTC

import resend

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..db.models import User, Profile, PasswordResetToken
from ..common.errors import ConflictError, UnauthorizedError
from .schemas import (
    UserRegister, UserLogin, TokenResponse, TokenRefresh, UserResponse,
    ForgotPasswordRequest, ResetPasswordRequest,
)
from .utils import hash_password, verify_password, create_access_token, create_refresh_token, verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(data: UserRegister, db: Session = Depends(get_db)) -> TokenResponse:
    # Check if user exists
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise ConflictError("Email already registered")

    # Create user
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.flush()

    # Create empty profile
    profile = Profile(user_id=user.id)
    db.add(profile)
    db.commit()

    # Generate tokens
    token_data = {"sub": user.id, "email": user.email}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")

    token_data = {"sub": user.id, "email": user.email}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(data: TokenRefresh, db: Session = Depends(get_db)) -> TokenResponse:
    payload = verify_token(data.refresh_token, token_type="refresh")
    if not payload:
        raise UnauthorizedError("Invalid or expired refresh token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UnauthorizedError("User not found")

    token_data = {"sub": user.id, "email": user.email}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at.isoformat(),
    )


@router.get("/me/calibration")
def get_me_calibration(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Get the user's Calibration Score for dashboard/sidebar display."""
    from ..probability.calibration import compute_calibration_score
    return compute_calibration_score(db, current_user.id)


RESET_SUCCESS_MSG = "If an account exists with this email, a reset link has been sent."


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)) -> dict:
    """Request a password reset link. Always returns success to avoid email enumeration."""
    # Rate limit: max 3 tokens per email per hour
    one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
    recent_count = (
        db.query(PasswordResetToken)
        .join(User, PasswordResetToken.user_id == User.id)
        .filter(User.email == data.email, PasswordResetToken.created_at > one_hour_ago)
        .count()
    )
    if recent_count >= 3:
        return {"message": RESET_SUCCESS_MSG}

    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        return {"message": RESET_SUCCESS_MSG}

    # Generate token
    token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    db.add(reset_token)
    db.commit()

    reset_url = f"https://www.lcsengine.com/reset-password?token={token}"

    # Send reset email via Resend
    resend.api_key = os.environ["RESEND_API_KEY"]
    resend.Emails.send({
        "from": "LCS Engine <noreply@lcsengine.com>",
        "to": [user.email],
        "subject": "Reset your LCS Engine password",
        "html": (
            "<p>Click the link below to reset your password:</p>"
            f'<p><a href="{reset_url}">Reset Password</a></p>'
            "<p>This link expires in 1 hour.</p>"
        ),
    })

    return {"message": RESET_SUCCESS_MSG}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)) -> dict:
    """Reset password using a valid token."""
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == data.token
    ).first()

    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid reset link.")

    if reset_token.used:
        raise HTTPException(status_code=400, detail="This reset link has already been used.")

    if reset_token.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="This reset link has expired.")

    # Validate password length (match registration rules)
    if len(data.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters.")

    # Update password
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset link.")

    user.password_hash = hash_password(data.password)
    reset_token.used = True
    db.commit()

    return {"message": "Password reset successfully."}

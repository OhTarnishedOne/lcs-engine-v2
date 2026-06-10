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
    days_remaining = None
    if current_user.is_guest and current_user.guest_expires_at:
        from datetime import datetime, UTC
        delta = current_user.guest_expires_at - datetime.now(UTC)
        days_remaining = max(0, delta.days + 1)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at.isoformat(),
        is_admin=current_user.is_admin,
        is_guest=current_user.is_guest,
        guest_expires_at=current_user.guest_expires_at.isoformat() if current_user.guest_expires_at else None,
        days_remaining=days_remaining,
    )


@router.delete("/me", status_code=204)
def delete_me(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permanently delete the authenticated user's account and all associated data.
    Requires password confirmation. Cancels any active Stripe subscription.
    """
    password = data.get("password")
    if not password:
        raise HTTPException(status_code=400, detail="Password is required")

    if not verify_password(password, current_user.password_hash):
        raise UnauthorizedError("Invalid password")

    user_id = current_user.id

    # Cancel Stripe subscription if present
    if current_user.stripe_customer_id:
        try:
            import stripe
            from ..settings import get_settings
            s = get_settings()
            stripe.api_key = s.stripe_secret_key
            # List active subscriptions and cancel each
            subs = stripe.Subscription.list(customer=current_user.stripe_customer_id, status="active")
            for sub in subs.auto_paging_iter():
                stripe.Subscription.cancel(sub.id)
                logger.info(f"Cancelled Stripe subscription {sub.id} for user {user_id}")
        except Exception as e:
            # Log but don't block deletion — user's intent is to leave
            logger.warning(f"Failed to cancel Stripe subscription for user {user_id}: {e}")

    # Explicitly delete Strategy/StrategyComparison (their backref relationship
    # causes SQLAlchemy to try nulling user_id before CASCADE fires in SQLite).
    # In Postgres, DB-level CASCADE handles this, but explicit delete is safer.
    from ..db.models import Strategy, StrategyComparison
    db.query(Strategy).filter(Strategy.user_id == user_id).delete()
    db.query(StrategyComparison).filter(StrategyComparison.user_id == user_id).delete()

    # Hard delete user — DB CASCADE handles remaining child records
    db.delete(current_user)
    db.commit()

    logger.info(f"user_deleted user_id={user_id}")

    from fastapi.responses import Response
    response = Response(status_code=204)
    response.delete_cookie("access_token", path="/")
    return response


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

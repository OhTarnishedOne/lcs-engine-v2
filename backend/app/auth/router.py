from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..db.models import User, Profile
from ..common.errors import ConflictError, UnauthorizedError
from .schemas import UserRegister, UserLogin, TokenResponse, TokenRefresh, UserResponse
from .utils import hash_password, verify_password, create_access_token, create_refresh_token, verify_token

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

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..db.models import User, Profile
from ..common.errors import NotFoundError
from .schemas import ProfileResponse, ProfileUpdate, OnboardingData

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile", response_model=ProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise NotFoundError("Profile not found")

    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        risk_tolerance=profile.risk_tolerance,
        investment_horizon=profile.investment_horizon,
        experience_level=profile.experience_level,
        goals=profile.goals.get("items") if profile.goals else None,
        interests=profile.interests.get("items") if profile.interests else None,
        onboarding_complete=profile.onboarding_complete,
    )


@router.put("/profile", response_model=ProfileResponse)
def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise NotFoundError("Profile not found")

    if data.risk_tolerance is not None:
        profile.risk_tolerance = data.risk_tolerance
    if data.investment_horizon is not None:
        profile.investment_horizon = data.investment_horizon
    if data.experience_level is not None:
        profile.experience_level = data.experience_level
    if data.goals is not None:
        profile.goals = {"items": data.goals}
    if data.interests is not None:
        profile.interests = {"items": data.interests}

    db.commit()
    db.refresh(profile)

    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        risk_tolerance=profile.risk_tolerance,
        investment_horizon=profile.investment_horizon,
        experience_level=profile.experience_level,
        goals=profile.goals.get("items") if profile.goals else None,
        interests=profile.interests.get("items") if profile.interests else None,
        onboarding_complete=profile.onboarding_complete,
    )


@router.post("/onboarding", response_model=ProfileResponse)
def complete_onboarding(
    data: OnboardingData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise NotFoundError("Profile not found")

    profile.risk_tolerance = data.risk_tolerance
    profile.investment_horizon = data.investment_horizon
    profile.experience_level = data.experience_level
    profile.goals = {"items": data.goals}
    if data.interests:
        profile.interests = {"items": data.interests}
    profile.onboarding_complete = True

    db.commit()
    db.refresh(profile)

    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        risk_tolerance=profile.risk_tolerance,
        investment_horizon=profile.investment_horizon,
        experience_level=profile.experience_level,
        goals=profile.goals.get("items") if profile.goals else None,
        interests=profile.interests.get("items") if profile.interests else None,
        onboarding_complete=profile.onboarding_complete,
    )

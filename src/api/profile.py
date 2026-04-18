from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session, select

from src.auth.dependencies import get_current_user
from src.db.database import get_session
from src.models.core import User
from src.models.profile import UserProfile


ALLOWED_GENDERS = {"Male", "Female", "Other", "Prefer not to say"}

router = APIRouter(tags=["Profile"])


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: Optional[str]
    full_name: Optional[str]
    gender: Optional[str]
    birthday: Optional[date]
    bio: Optional[str]
    profile_prompt_dismissed: bool
    show_full_name: bool
    show_gender: bool
    show_birthday: bool
    show_email: bool
    show_bio: bool


class PublicProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: Optional[str]
    full_name: Optional[str]
    gender: Optional[str]
    birthday: Optional[date]
    bio: Optional[str]


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[str] = None
    bio: Optional[str] = None
    show_full_name: Optional[bool] = None
    show_gender: Optional[bool] = None
    show_birthday: Optional[bool] = None
    show_email: Optional[bool] = None
    show_bio: Optional[bool] = None


def _get_profile(session: Session, user_id: int) -> Optional[UserProfile]:
    return session.exec(select(UserProfile).where(UserProfile.user_id == user_id)).first()


def _require_valid_gender(gender: str) -> None:
    if gender not in ALLOWED_GENDERS:
        raise HTTPException(status_code=400, detail="Invalid gender value")


def _parse_birthday(raw_birthday: str) -> date:
    try:
        return date.fromisoformat(raw_birthday)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid birthday format") from exc


def _build_self_response(user: User, profile: Optional[UserProfile]) -> ProfileResponse:
    return ProfileResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        gender=profile.gender if profile else None,
        birthday=profile.birthday if profile else None,
        bio=profile.bio if profile else None,
        profile_prompt_dismissed=profile.profile_prompt_dismissed if profile else False,
        show_full_name=profile.show_full_name if profile else True,
        show_gender=profile.show_gender if profile else True,
        show_birthday=profile.show_birthday if profile else True,
        show_email=profile.show_email if profile else True,
        show_bio=profile.show_bio if profile else True,
    )


def _build_public_response(user: User, profile: Optional[UserProfile]) -> PublicProfileResponse:
    show_full_name = profile.show_full_name if profile else True
    show_gender = profile.show_gender if profile else True
    show_birthday = profile.show_birthday if profile else True
    show_email = profile.show_email if profile else True
    show_bio = profile.show_bio if profile else True

    return PublicProfileResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name if show_full_name else None,
        gender=profile.gender if profile and show_gender else None,
        birthday=profile.birthday if profile and show_birthday else None,
        email=user.email if show_email else None,
        bio=profile.bio if profile and show_bio else None,
    )


@router.get("/profile/me", response_model=ProfileResponse)
def read_my_profile(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return _build_self_response(current_user, _get_profile(session, current_user.id))


@router.put("/profile/me", response_model=ProfileResponse)
def update_my_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    profile = _get_profile(session, current_user.id)
    if profile is None:
        profile = UserProfile(user_id=current_user.id)

    if payload.full_name is not None:
        current_user.full_name = payload.full_name
        session.add(current_user)

    if payload.gender is not None:
        _require_valid_gender(payload.gender)
        profile.gender = payload.gender

    if payload.birthday is not None:
        profile.birthday = _parse_birthday(payload.birthday)

    if payload.bio is not None:
        if len(payload.bio) > 300:
            raise HTTPException(status_code=400, detail="Bio must be at most 300 characters")
        profile.bio = payload.bio

    # Saving profile counts as dismissing the first-login prompt.
    profile.profile_prompt_dismissed = True

    if payload.show_full_name is not None:
        profile.show_full_name = payload.show_full_name
    if payload.show_gender is not None:
        profile.show_gender = payload.show_gender
    if payload.show_birthday is not None:
        profile.show_birthday = payload.show_birthday
    if payload.show_email is not None:
        profile.show_email = payload.show_email
    if payload.show_bio is not None:
        profile.show_bio = payload.show_bio

    session.add(profile)
    session.commit()
    session.refresh(profile)
    session.refresh(current_user)
    return _build_self_response(current_user, profile)


@router.get("/users/{user_id}/profile", response_model=PublicProfileResponse)
def read_public_profile(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    profile = _get_profile(session, user_id)
    return _build_public_response(user, profile)


@router.post("/profile/me/dismiss-prompt", response_model=ProfileResponse)
def dismiss_profile_prompt(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    profile = _get_profile(session, current_user.id)
    if profile is None:
        profile = UserProfile(user_id=current_user.id)

    profile.profile_prompt_dismissed = True
    session.add(profile)
    session.commit()
    session.refresh(profile)
    session.refresh(current_user)
    return _build_self_response(current_user, profile)

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session, select
from typing import Optional

from src.auth.dependencies import get_current_user
from src.auth.security import create_access_token, verify_password
from src.db.database import get_session
from src.models.core import User, UserCreate
from src.services.users import create_user_account


router = APIRouter(prefix="/auth", tags=["Auth"])


class AuthRegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None


class AuthLoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: Optional[str] = None


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: AuthRegisterRequest,
    session: Session = Depends(get_session),
):
    user = create_user_account(
        session,
        UserCreate(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
        ),
    )
    return user


@router.post("/login", response_model=TokenResponse)
def login_user(
    payload: AuthLoginRequest,
    session: Session = Depends(get_session),
):
    identifier = payload.email or payload.username
    if not identifier:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="email or username is required",
        )

    statement = select(User).where(
        (User.email == identifier) | (User.username == identifier)
    )
    user = session.exec(statement).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

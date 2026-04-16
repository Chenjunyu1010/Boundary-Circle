from fastapi import HTTPException, status
from sqlmodel import Session, select

from src.auth.security import get_password_hash
from src.models.core import User, UserCreate


def create_user_account(session: Session, user_in: UserCreate) -> User:
    existing_email = session.exec(select(User).where(User.email == user_in.email)).first()
    if existing_email is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    existing_username = session.exec(
        select(User).where(User.username == user_in.username)
    ).first()
    if existing_username is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

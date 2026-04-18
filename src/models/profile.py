from __future__ import annotations

from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel


class UserProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    gender: Optional[str] = None
    birthday: Optional[date] = None
    bio: Optional[str] = None
    profile_prompt_dismissed: bool = False
    show_full_name: bool = True
    show_gender: bool = True
    show_birthday: bool = True
    show_email: bool = True
    show_bio: bool = True

from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

# ==========================================
# User Models
# ==========================================
class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    full_name: Optional[str] = None
    
class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    
class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int


# ==========================================
# Circle Models
# ==========================================
class CircleBase(SQLModel):
    name: str = Field(index=True, unique=True)
    description: str
    category: str = Field(default="General") # e.g., Course, Event, Interest

class Circle(CircleBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    creator_id: int = Field(foreign_key="user.id")

class CircleCreate(CircleBase):
    pass

class CircleRead(CircleBase):
    id: int
    creator_id: int

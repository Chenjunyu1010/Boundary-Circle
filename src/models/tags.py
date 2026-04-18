from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import model_validator
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class TagDataType(str, Enum):
    INTEGER = "integer"
    BOOLEAN = "boolean"
    STRING = "string"
    ENUM = "enum"
    FLOAT = "float"
    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"


class CircleRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"


class TagDefinition(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    circle_id: int = Field(foreign_key="circle.id", index=True)
    name: str
    data_type: TagDataType
    required: bool = Field(default=False)
    options: Optional[str] = Field(default=None)
    max_selections: Optional[int] = Field(default=None)
    description: Optional[str] = Field(default=None)


class UserTag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    circle_id: int = Field(foreign_key="circle.id", index=True)
    tag_definition_id: int = Field(foreign_key="tagdefinition.id")
    value: str


class CircleMember(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "circle_id", name="uq_circle_member_user_circle"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    circle_id: int = Field(foreign_key="circle.id", index=True)
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    role: CircleRole = Field(default=CircleRole.MEMBER)


class TagDefinitionCreate(SQLModel):
    name: str
    data_type: TagDataType
    required: bool = False
    options: Optional[str] = None
    max_selections: Optional[int] = None
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_selection_fields(self):
        if self.data_type != TagDataType.MULTI_SELECT:
            self.max_selections = None
            return self

        if self.max_selections is not None and self.max_selections <= 0:
            raise ValueError("max_selections must be positive")

        return self


class UserTagSubmit(SQLModel):
    tag_definition_id: int
    value: str


class CircleMemberTagRead(SQLModel):
    id: int
    user_id: int
    circle_id: int
    tag_definition_id: int
    tag_name: str
    data_type: TagDataType
    value: str

import json
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class TeamStatus(str, Enum):
    RECRUITING = "Recruiting"
    LOCKED = "Locked"


class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str = ""
    circle_id: int = Field(foreign_key="circle.id", index=True)
    creator_id: int = Field(foreign_key="user.id", index=True)
    max_members: int = Field(default=4, ge=2)
    status: TeamStatus = Field(default=TeamStatus.RECRUITING)
    required_tags_json: str = Field(default="[]")


class TeamMember(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(foreign_key="team.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)


class Invitation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(foreign_key="team.id", index=True)
    inviter_id: int = Field(foreign_key="user.id", index=True)
    invitee_id: int = Field(foreign_key="user.id", index=True)
    status: InvitationStatus = Field(default=InvitationStatus.PENDING)


class TeamCreate(SQLModel):
    name: str
    description: str = ""
    circle_id: int
    max_members: int = Field(ge=2)
    required_tags: list[str] = []


class TeamRead(SQLModel):
    id: int
    name: str
    description: str
    circle_id: int
    creator_id: int
    max_members: int
    current_members: int
    status: TeamStatus
    required_tags: list[str]
    member_ids: list[int]


class InvitationCreate(SQLModel):
    user_id: int
    team_name: Optional[str] = None


class InvitationRead(SQLModel):
    id: int
    team_id: int
    inviter_id: int
    invitee_id: int
    status: InvitationStatus


class InvitationRespond(SQLModel):
    accept: bool


def encode_required_tags(required_tags: list[str]) -> str:
    return json.dumps(required_tags)


def decode_required_tags(required_tags_json: str) -> list[str]:
    try:
        payload = json.loads(required_tags_json)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    return [str(item) for item in payload]

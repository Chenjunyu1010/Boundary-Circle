import json
from enum import Enum
from typing import Optional, Union

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
    required_tag_rules_json: str = Field(default="[]")


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


class TeamRequirementRule(SQLModel):
    tag_name: str
    expected_value: Union[str, list[str], int, float, bool]


class TeamCreate(SQLModel):
    name: str
    description: str = ""
    circle_id: int
    max_members: int = Field(ge=2)
    required_tags: list[str] = []
    required_tag_rules: list[TeamRequirementRule] = []


class TeamRead(SQLModel):
    id: int
    name: str
    description: str
    circle_id: int
    creator_id: int
    creator_username: Optional[str] = None
    creator_full_name: Optional[str] = None
    max_members: int
    current_members: int
    status: TeamStatus
    required_tags: list[str]
    required_tag_rules: list[TeamRequirementRule] = []
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


def encode_required_tag_rules(required_tag_rules: list[TeamRequirementRule]) -> str:
    return json.dumps([rule.model_dump() for rule in required_tag_rules])


def decode_required_tag_rules(required_tag_rules_json: str) -> list[TeamRequirementRule]:
    try:
        payload = json.loads(required_tag_rules_json)
    except json.JSONDecodeError:
        return []

    if not isinstance(payload, list):
        return []

    decoded_rules: list[TeamRequirementRule] = []
    for item in payload:
        if not isinstance(item, dict):
            return []
        try:
            decoded_rules.append(TeamRequirementRule.model_validate(item))
        except Exception:
            return []
    return decoded_rules

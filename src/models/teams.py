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


class InvitationKind(str, Enum):
    INVITE = "invite"
    JOIN_REQUEST = "join_request"


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
    freedom_requirement_text: str = ""
    freedom_requirement_profile_json: str = '{"keywords": []}'


class TeamMember(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(foreign_key="team.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)


class Invitation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(foreign_key="team.id", index=True)
    inviter_id: int = Field(foreign_key="user.id", index=True)
    invitee_id: int = Field(foreign_key="user.id", index=True)
    kind: InvitationKind = Field(default=InvitationKind.INVITE)
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
    freedom_requirement_text: str = ""


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
    freedom_requirement_text: str = ""
    freedom_requirement_profile_keywords: list[str] = []


class InvitationCreate(SQLModel):
    user_id: int
    team_name: Optional[str] = None


class InvitationRead(SQLModel):
    id: int
    team_id: int
    team_name: Optional[str] = None
    inviter_id: int
    inviter_username: Optional[str] = None
    invitee_id: int
    invitee_username: Optional[str] = None
    kind: InvitationKind = InvitationKind.INVITE
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


def empty_freedom_profile() -> dict[str, list[str]]:
    return {"keywords": []}


def normalize_freedom_profile(data: object) -> dict[str, list[str]]:
    if data is None:
        return empty_freedom_profile()
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return empty_freedom_profile()
    if not isinstance(data, dict):
        return empty_freedom_profile()

    keywords = data.get("keywords", [])
    if not isinstance(keywords, list):
        return empty_freedom_profile()

    seen: set[str] = set()
    deduped: list[str] = []
    for item in keywords:
        if isinstance(item, str):
            trimmed = item.strip()
            if trimmed and trimmed not in seen:
                seen.add(trimmed)
                deduped.append(trimmed)
                if len(deduped) >= 5:
                    break

    return {"keywords": deduped}


def decode_freedom_profile(raw: Optional[str]) -> dict[str, list[str]]:
    if raw is None or raw == "":
        return empty_freedom_profile()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return empty_freedom_profile()
    return normalize_freedom_profile(parsed)


def encode_freedom_profile(profile: dict[str, list[str]]) -> str:
    normalized = normalize_freedom_profile(profile)
    return json.dumps(normalized)

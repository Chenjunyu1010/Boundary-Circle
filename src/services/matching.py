from __future__ import annotations

import json
from typing import Any, List, Set

from sqlmodel import Session, select

from src.models.tags import TagDataType, TagDefinition, UserTag
from src.models.teams import (
    Team,
    TeamMember,
    TeamRequirementRule,
    decode_required_tag_rules,
    decode_required_tags,
)


def get_user_tag_names_for_circle(session: Session, user_id: int, circle_id: int) -> Set[str]:
    """Return the set of tag names this user has submitted in a given circle."""
    user_tags = session.exec(
        select(UserTag).where(UserTag.user_id == user_id, UserTag.circle_id == circle_id)
    ).all()
    names: set[str] = set()
    for user_tag in user_tags:
        tag_definition = session.get(TagDefinition, user_tag.tag_definition_id)
        if tag_definition is not None:
            names.add(tag_definition.name)
    return names


def parse_user_tag_value(tag_definition: TagDefinition, raw_value: str) -> Any:
    """Parse a stored user tag value according to its definition type."""
    if tag_definition.data_type == TagDataType.INTEGER:
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            return raw_value
    if tag_definition.data_type == TagDataType.FLOAT:
        try:
            return float(raw_value)
        except (TypeError, ValueError):
            return raw_value
    if tag_definition.data_type == TagDataType.BOOLEAN:
        return str(raw_value).lower() in {"true", "1"}
    if tag_definition.data_type == TagDataType.MULTI_SELECT:
        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return raw_value


def get_user_tag_values_for_circle(session: Session, user_id: int, circle_id: int) -> dict[str, Any]:
    """Return parsed user tag values keyed by tag name for a circle."""
    user_tags = session.exec(
        select(UserTag).where(UserTag.user_id == user_id, UserTag.circle_id == circle_id)
    ).all()
    tag_values: dict[str, Any] = {}
    for user_tag in user_tags:
        tag_definition = session.get(TagDefinition, user_tag.tag_definition_id)
        if tag_definition is None:
            continue
        tag_values[tag_definition.name] = parse_user_tag_value(tag_definition, user_tag.value)
    return tag_values


def get_team_member_ids(session: Session, team_id: int) -> List[int]:
    """Return a list of user IDs that are members of the given team."""
    members = session.exec(
        select(TeamMember).where(TeamMember.team_id == team_id)
    ).all()
    return [member.user_id for member in members]


def build_team_profile(session: Session, team: Team) -> Set[str]:
    """Build a tag profile for a team.

    The profile is defined as the union of:
    - the team's required tag names, and
    - all tag names of current team members within the same circle.
    """
    required_tags = get_team_required_tag_names(team)

    member_ids = get_team_member_ids(session, team.id or 0)
    member_tag_names: Set[str] = set()
    for member_id in member_ids:
        member_tag_names |= get_user_tag_names_for_circle(
            session=session,
            user_id=member_id,
            circle_id=team.circle_id,
        )

    return required_tags | member_tag_names


def get_team_required_tag_names(team: Team) -> Set[str]:
    """Return team requirement names, preferring structured rules when present."""
    structured_rules = decode_required_tag_rules(team.required_tag_rules_json)
    if structured_rules:
        return {rule.tag_name for rule in structured_rules}
    return set(decode_required_tags(team.required_tags_json))


def rule_matches_user_value(rule: TeamRequirementRule, user_value: Any) -> bool:
    """Return whether a parsed user value satisfies a team rule."""
    expected_value = rule.expected_value
    if isinstance(expected_value, list):
        if not isinstance(user_value, list):
            return False
        return bool(set(str(item) for item in expected_value) & set(str(item) for item in user_value))
    return user_value == expected_value


def coverage_score_for_rules(required_rules: list[TeamRequirementRule], user_tag_values: dict[str, Any]) -> float:
    """Compute coverage for structured requirement rules."""
    if not required_rules:
        return 1.0
    matched_count = 0
    for rule in required_rules:
        if rule_matches_user_value(rule, user_tag_values.get(rule.tag_name)):
            matched_count += 1
    return matched_count / float(len(required_rules))


def describe_matched_rules(required_rules: list[TeamRequirementRule], user_tag_values: dict[str, Any]) -> list[str]:
    """Build matched rule descriptions for API responses."""
    matched: list[str] = []
    for rule in required_rules:
        if rule_matches_user_value(rule, user_tag_values.get(rule.tag_name)):
            matched.append(f"{rule.tag_name}={rule.expected_value}")
    return matched


def describe_missing_rules(required_rules: list[TeamRequirementRule], user_tag_values: dict[str, Any]) -> list[str]:
    """Build missing rule descriptions for API responses."""
    missing: list[str] = []
    for rule in required_rules:
        if not rule_matches_user_value(rule, user_tag_values.get(rule.tag_name)):
            missing.append(f"{rule.tag_name}={rule.expected_value}")
    return missing


def coverage_score(required: Set[str], user_tags: Set[str]) -> float:
    """Compute how much of the required tag set is covered by user tags.

    Returns 1.0 when the required set is empty, otherwise
    ``len(required ∩ user_tags) / len(required)``.
    """
    if not required:
        return 1.0
    intersection_size = len(required & user_tags)
    return intersection_size / float(len(required))


def jaccard_score(left: Set[str], right: Set[str]) -> float:
    """Compute the Jaccard similarity between two tag sets.

    Jaccard(A, B) = |A ∩ B| / |A ∪ B|. When both sets are empty, returns 0.0.
    """
    union = left | right
    if not union:
        return 0.0
    intersection_size = len(left & right)
    return intersection_size / float(len(union))


def decode_freedom_keywords(profile_json: str) -> List[str]:
    """Decode freedom profile JSON to list of keywords.

    Uses the same normalization as src.models.teams.decode_freedom_profile
    but returns only the keywords list.
    """
    try:
        profile = json.loads(profile_json) if profile_json else {"keywords": []}
    except json.JSONDecodeError:
        return []
    if not isinstance(profile, dict):
        return []
    keywords = profile.get("keywords", [])
    if not isinstance(keywords, list):
        return []
    return [str(k).strip() for k in keywords if isinstance(k, str) and str(k).strip()]


def compute_freedom_score(user_keywords: List[str], team_keywords: List[str]) -> float:
    """Compute freedom overlap score as intersection over team requirements.

    freedom_score = len(user_keywords ∩ team_keywords) / len(team_keywords)
    Returns 0.0 when team_keywords is empty.
    """
    if not team_keywords:
        return 0.0
    user_set = set(user_keywords)
    team_set = set(team_keywords)
    overlap_size = len(user_set & team_set)
    return overlap_size / float(len(team_set))


def get_matched_freedom_keywords(user_keywords: List[str], team_keywords: List[str]) -> List[str]:
    """Return the list of keywords that match between user and team profiles."""
    user_set = set(user_keywords)
    team_set = set(team_keywords)
    return sorted(list(user_set & team_set))

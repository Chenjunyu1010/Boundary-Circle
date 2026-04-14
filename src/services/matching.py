from __future__ import annotations

from typing import List, Set

from sqlmodel import Session, select

from src.models.tags import CircleMember, TagDefinition, UserTag
from src.models.teams import Team, TeamMember, decode_required_tags


def get_user_tag_names_for_circle(session: Session, user_id: int, circle_id: int) -> Set[str]:
    """Return the set of tag *names* this user has submitted in a given circle.

    The result is based on TagDefinition.name joined through UserTag for the
    specified user and circle.
    """
    statement = (
        select(TagDefinition.name)
        .join(UserTag, TagDefinition.id == UserTag.tag_definition_id)
        .where(UserTag.user_id == user_id, UserTag.circle_id == circle_id)
    )
    names: List[str] = session.exec(statement).all()
    return set(names)


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
    required_tags = set(decode_required_tags(team.required_tags_json))

    member_ids = get_team_member_ids(session, team.id or 0)
    member_tag_names: Set[str] = set()
    for member_id in member_ids:
        member_tag_names |= get_user_tag_names_for_circle(
            session=session,
            user_id=member_id,
            circle_id=team.circle_id,
        )

    return required_tags | member_tag_names


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

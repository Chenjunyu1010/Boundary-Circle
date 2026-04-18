from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, SQLModel, select

from src.auth.dependencies import get_current_user
from src.db.database import get_session
from src.models.core import Circle, User
from src.models.tags import CircleMember
from src.models.teams import (
    Team,
    TeamMember,
    TeamRead,
    TeamStatus,
    decode_required_tag_rules,
)
from src.services.matching import (
    build_team_profile,
    compute_freedom_score,
    coverage_score,
    coverage_score_for_rules,
    decode_freedom_keywords,
    describe_matched_rules,
    describe_missing_rules,
    get_matched_freedom_keywords,
    get_team_member_ids,
    get_team_required_tag_names,
    get_user_tag_values_for_circle,
    jaccard_score,
)


router = APIRouter(prefix="/matching", tags=["Matching"])


class UserMatch(SQLModel):
    """Match result for recommending users to join a team."""

    user_id: int
    username: str
    email: str
    coverage_score: float
    jaccard_score: float
    freedom_score: float = 0.0
    matched_tags: List[str]
    matched_freedom_keywords: List[str] = []
    missing_required_tags: List[str]


class TeamMatch(SQLModel):
    """Match result for recommending teams to a user."""

    team: TeamRead
    coverage_score: float
    jaccard_score: float
    freedom_score: float = 0.0
    matched_freedom_keywords: List[str] = []
    missing_required_tags: List[str]


def _ensure_circle_member_or_creator(
    *,
    session: Session,
    circle: Circle,
    user: User,
    detail: str = "User must join the circle first",
) -> None:
    """Ensure the user is either the circle creator or a member of the circle."""
    if user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Current user ID missing",
        )

    if circle.creator_id == user.id:
        return

    membership = session.exec(
        select(CircleMember).where(
            CircleMember.circle_id == circle.id,
            CircleMember.user_id == user.id,
        )
    ).first()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


@router.get("/users", response_model=List[UserMatch])
def match_users_for_team(
    team_id: int,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> List[UserMatch]:
    """Recommend candidate users for a given team based on tag coverage."""
    team = session.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    circle = session.get(Circle, team.circle_id)
    if circle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circle not found")

    _ensure_circle_member_or_creator(session=session, circle=circle, user=current_user)

    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Current user ID missing",
        )

    is_team_member = session.exec(
        select(TeamMember).where(
            TeamMember.team_id == team.id,
            TeamMember.user_id == current_user.id,
        )
    ).first()
    if team.creator_id != current_user.id and is_team_member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team creator or members can view recommendations",
        )

    required_rules = decode_required_tag_rules(team.required_tag_rules_json)
    required_tags = get_team_required_tag_names(team)
    team_profile = build_team_profile(session=session, team=team)
    team_member_ids = set(get_team_member_ids(session=session, team_id=team.id or 0))

    # Decode team's freedom requirement profile
    team_freedom_keywords = decode_freedom_keywords(team.freedom_requirement_profile_json)

    memberships = session.exec(
        select(CircleMember).where(CircleMember.circle_id == circle.id)
    ).all()

    candidates: List[UserMatch] = []
    for membership in memberships:
        user_id = membership.user_id
        if user_id in team_member_ids or user_id == current_user.id:
            continue

        user = session.get(User, user_id)
        if user is None or user.id is None:
            continue

        user_tag_values = get_user_tag_values_for_circle(
            session=session,
            user_id=user_id,
            circle_id=team.circle_id,
        )
        user_tags = set(user_tag_values.keys())

        if required_rules:
            cov = coverage_score_for_rules(required_rules, user_tag_values)
            matched_tags = describe_matched_rules(required_rules, user_tag_values)
            missing_required = describe_missing_rules(required_rules, user_tag_values)
        else:
            cov = coverage_score(required=required_tags, user_tags=user_tags)
            matched_tags = sorted(required_tags & user_tags)
            missing_required = sorted(required_tags - user_tags)

        if cov == 0.0:
            continue

        jac = jaccard_score(team_profile, user_tags)
        
        # Compute freedom score
        user_freedom_keywords = decode_freedom_keywords(membership.freedom_tag_profile_json)
        freedom_score = compute_freedom_score(user_freedom_keywords, team_freedom_keywords)
        matched_freedom = get_matched_freedom_keywords(user_freedom_keywords, team_freedom_keywords)
        
        candidates.append(
            UserMatch(
                user_id=user.id,
                username=user.username,
                email=user.email,
                coverage_score=cov,
                jaccard_score=jac,
                freedom_score=freedom_score,
                matched_tags=matched_tags,
                matched_freedom_keywords=matched_freedom,
                missing_required_tags=missing_required,
            )
        )

    if limit <= 0:
        limit = 10
    limit = min(limit, 50)

    # Sort by (coverage_score, jaccard_score, freedom_score) descending
    candidates.sort(key=lambda m: (m.coverage_score, m.jaccard_score, m.freedom_score), reverse=True)
    return candidates[:limit]


@router.get("/teams", response_model=List[TeamMatch])
def match_teams_for_user(
    circle_id: int,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> List[TeamMatch]:
    """Recommend teams in a circle for the current user based on tags."""
    circle = session.get(Circle, circle_id)
    if circle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circle not found")

    _ensure_circle_member_or_creator(session=session, circle=circle, user=current_user)

    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Current user ID missing",
        )

    user_tag_values = get_user_tag_values_for_circle(
        session=session,
        user_id=current_user.id,
        circle_id=circle_id,
    )
    user_tags = set(user_tag_values.keys())

    # Get user's freedom keywords from CircleMember
    user_freedom_keywords = []
    user_membership = session.exec(
        select(CircleMember).where(
            CircleMember.circle_id == circle_id,
            CircleMember.user_id == current_user.id,
        )
    ).first()
    if user_membership:
        user_freedom_keywords = decode_freedom_keywords(user_membership.freedom_tag_profile_json)

    from src.api.teams import build_team_read  # local import to avoid circular import at module level

    teams = session.exec(select(Team).where(Team.circle_id == circle_id)).all()

    results: List[TeamMatch] = []
    for team in teams:
        team_read = build_team_read(team, session)
        if current_user.id in team_read.member_ids:
            continue
        if team_read.status == TeamStatus.LOCKED:
            continue

        # Decode team's freedom requirement profile
        team_freedom_keywords = decode_freedom_keywords(team.freedom_requirement_profile_json)

        required_rules = decode_required_tag_rules(team.required_tag_rules_json)
        required_tags = get_team_required_tag_names(team)

        if required_rules:
            cov = coverage_score_for_rules(required_rules, user_tag_values)
            missing_required = describe_missing_rules(required_rules, user_tag_values)
        else:
            cov = coverage_score(required=required_tags, user_tags=user_tags)
            missing_required = sorted(required_tags - user_tags)

        if cov == 0.0:
            continue

        team_profile = build_team_profile(session=session, team=team)
        jac = jaccard_score(team_profile, user_tags)
        
        # Compute freedom score
        freedom_score = compute_freedom_score(user_freedom_keywords, team_freedom_keywords)
        matched_freedom = get_matched_freedom_keywords(user_freedom_keywords, team_freedom_keywords)
        
        results.append(
            TeamMatch(
                team=team_read,
                coverage_score=cov,
                jaccard_score=jac,
                freedom_score=freedom_score,
                matched_freedom_keywords=matched_freedom,
                missing_required_tags=missing_required,
            )
        )

    if limit <= 0:
        limit = 10
    limit = min(limit, 50)

    # Sort by (coverage_score, jaccard_score, freedom_score) descending
    results.sort(key=lambda m: (m.coverage_score, m.jaccard_score, m.freedom_score), reverse=True)
    return results[:limit]

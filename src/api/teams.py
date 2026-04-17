from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from src.auth.dependencies import get_current_user
from src.db.database import get_session
from src.models.core import Circle, User
from src.models.tags import CircleMember
from src.models.teams import (
    Invitation,
    InvitationCreate,
    InvitationRead,
    InvitationRespond,
    InvitationStatus,
    Team,
    TeamCreate,
    TeamMember,
    TeamRead,
    TeamStatus,
    decode_required_tag_rules,
    decode_required_tags,
    encode_required_tag_rules,
    encode_required_tags,
)


router = APIRouter(tags=["Teams"])


def build_team_read(team: Team, session: Session) -> TeamRead:
    if team.id is None:
        raise HTTPException(status_code=500, detail="Team ID missing")
    members = session.exec(select(TeamMember).where(TeamMember.team_id == team.id)).all()
    member_ids = [member.user_id for member in members]
    current_members = len(member_ids)
    status = TeamStatus.LOCKED if current_members >= team.max_members else TeamStatus.RECRUITING
    if team.status != status:
        team.status = status
        session.add(team)
        session.commit()
        session.refresh(team)

    creator = session.get(User, team.creator_id)

    return TeamRead(
        id=team.id,
        name=team.name,
        description=team.description,
        circle_id=team.circle_id,
        creator_id=team.creator_id,
        creator_username=creator.username if creator is not None else None,
        creator_full_name=creator.full_name if creator is not None else None,
        max_members=team.max_members,
        current_members=current_members,
        status=status,
        required_tags=decode_required_tags(team.required_tags_json),
        required_tag_rules=decode_required_tag_rules(team.required_tag_rules_json),
        member_ids=member_ids,
    )


def require_circle_member(
    circle_id: int,
    user_id: int,
    session: Session,
    allow_creator: bool = False,
    detail: str = "User must join the circle first",
) -> None:
    circle = session.get(Circle, circle_id)
    if circle is None:
        raise HTTPException(status_code=404, detail="Circle not found")
    if allow_creator and circle.creator_id == user_id:
        return

    membership = session.exec(
        select(CircleMember).where(
            CircleMember.circle_id == circle_id,
            CircleMember.user_id == user_id,
        )
    ).first()
    if membership is None:
        raise HTTPException(status_code=403, detail=detail)


@router.post("/teams", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if current_user.id is None:
        raise HTTPException(status_code=500, detail="Current user ID missing")
    require_circle_member(payload.circle_id, current_user.id, session, allow_creator=True)

    team = Team(
        name=payload.name,
        description=payload.description,
        circle_id=payload.circle_id,
        creator_id=current_user.id,
        max_members=payload.max_members,
        required_tags_json=encode_required_tags(payload.required_tags),
        required_tag_rules_json=encode_required_tag_rules(payload.required_tag_rules),
    )
    session.add(team)
    session.commit()
    session.refresh(team)

    if team.id is None:
        raise HTTPException(status_code=500, detail="Team ID missing")

    session.add(TeamMember(team_id=team.id, user_id=current_user.id))
    session.commit()

    return build_team_read(team, session)


@router.get("/circles/{circle_id}/teams", response_model=list[TeamRead])
def list_teams(
    circle_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if current_user.id is None:
        raise HTTPException(status_code=500, detail="Current user ID missing")
    require_circle_member(circle_id, current_user.id, session, allow_creator=True)
    teams = session.exec(select(Team).where(Team.circle_id == circle_id)).all()
    return [build_team_read(team, session) for team in teams]


@router.get("/circles/{circle_id}/members")
def list_circle_members(
    circle_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if current_user.id is None:
        raise HTTPException(status_code=500, detail="Current user ID missing")
    require_circle_member(circle_id, current_user.id, session, allow_creator=True)
    memberships = session.exec(select(CircleMember).where(CircleMember.circle_id == circle_id)).all()
    users = []
    for membership in memberships:
        user = session.get(User, membership.user_id)
        if user is not None:
            users.append({"id": user.id, "username": user.username, "email": user.email, "circle_id": circle_id})
    return users


@router.post("/teams/{team_id}/invite", response_model=InvitationRead, status_code=status.HTTP_201_CREATED)
def send_invitation(
    team_id: int,
    payload: InvitationCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if current_user.id is None:
        raise HTTPException(status_code=500, detail="Current user ID missing")
    team = session.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    inviter_is_member = session.exec(
        select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
    ).first()
    if team.creator_id != current_user.id and inviter_is_member is None:
        raise HTTPException(status_code=403, detail="Only team creator or members can send invitations")

    require_circle_member(
        team.circle_id,
        payload.user_id,
        session,
        detail="Invitee must be a member of the same circle",
    )

    team_read = build_team_read(team, session)
    if team_read.status == TeamStatus.LOCKED:
        raise HTTPException(status_code=409, detail="Team is already full")

    existing_member = session.exec(
        select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == payload.user_id)
    ).first()
    if existing_member is not None:
        raise HTTPException(status_code=400, detail="User is already a team member")

    existing_pending = session.exec(
        select(Invitation).where(
            Invitation.team_id == team_id,
            Invitation.invitee_id == payload.user_id,
            Invitation.status == InvitationStatus.PENDING,
        )
    ).first()
    if existing_pending is not None:
        raise HTTPException(status_code=409, detail="Invitation already pending")

    invitation = Invitation(team_id=team_id, inviter_id=current_user.id, invitee_id=payload.user_id)
    session.add(invitation)
    session.commit()
    session.refresh(invitation)
    return invitation


@router.get("/teams/{team_id}/invitations", response_model=list[InvitationRead])
def list_team_invitations(
    team_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if current_user.id is None:
        raise HTTPException(status_code=500, detail="Current user ID missing")

    team = session.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    team_membership = session.exec(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id,
        )
    ).first()
    if team.creator_id != current_user.id and team_membership is None:
        raise HTTPException(
            status_code=403,
            detail="Only team creator or members can view team invitations",
        )

    return session.exec(select(Invitation).where(Invitation.team_id == team_id)).all()


@router.get("/invitations", response_model=list[InvitationRead])
def list_invitations(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if current_user.id is None:
        raise HTTPException(status_code=500, detail="Current user ID missing")
    return session.exec(select(Invitation).where(Invitation.invitee_id == current_user.id)).all()


@router.post("/invitations/{invite_id}/respond")
def respond_to_invitation(
    invite_id: int,
    payload: InvitationRespond,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if current_user.id is None:
        raise HTTPException(status_code=500, detail="Current user ID missing")
    invitation = session.get(Invitation, invite_id)
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invitation.invitee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the invitee can respond")
    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Invitation already processed")

    team = session.get(Team, invitation.team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    team_read = build_team_read(team, session)
    if payload.accept and team_read.current_members >= team.max_members:
        raise HTTPException(status_code=409, detail="Team is already full")

    invitation.status = InvitationStatus.ACCEPTED if payload.accept else InvitationStatus.REJECTED
    session.add(invitation)

    if payload.accept:
        session.add(TeamMember(team_id=invitation.team_id, user_id=current_user.id))

    session.commit()

    refreshed_team = session.get(Team, invitation.team_id)
    if refreshed_team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    assert refreshed_team is not None
    refreshed_team_read = build_team_read(refreshed_team, session)
    message = "Invitation accepted" if payload.accept else "Invitation rejected"
    return {"success": True, "message": message, "team_status": refreshed_team_read.status}


@router.delete("/teams/{team_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if current_user.id is None:
        raise HTTPException(status_code=500, detail="Current user ID missing")
    membership = session.exec(
        select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
    ).first()
    if membership is None:
        raise HTTPException(status_code=404, detail="Team membership not found")

    session.delete(membership)
    session.commit()
    return None

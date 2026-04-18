from sqlmodel import select

from scripts.seed_data import seed_dataset
from src.models.core import Circle
from src.models.profile import UserProfile
from src.models.tags import CircleMember
from src.models.teams import Invitation, InvitationKind, InvitationStatus, Team, TeamMember


def _circle_member_pairs(db_session) -> set[tuple[int, int]]:
    return {
        (membership.circle_id, membership.user_id)
        for membership in db_session.exec(select(CircleMember)).all()
    }


def _team_member_pairs(db_session) -> set[tuple[int, int]]:
    return {
        (membership.team_id, membership.user_id)
        for membership in db_session.exec(select(TeamMember)).all()
    }


def _seed_datasets_have_internal_consistency(db_session) -> None:
    circles = {circle.id: circle for circle in db_session.exec(select(Circle)).all()}
    profiles = {profile.user_id: profile for profile in db_session.exec(select(UserProfile)).all()}
    team_members = db_session.exec(select(TeamMember)).all()
    invitations = db_session.exec(select(Invitation)).all()
    teams = db_session.exec(select(Team)).all()

    circle_member_pairs = _circle_member_pairs(db_session)
    team_member_pairs = _team_member_pairs(db_session)

    for team in teams:
        assert team.id is not None
        assert team.circle_id in circles
        assert (team.circle_id, team.creator_id) in circle_member_pairs

        member_ids = [member.user_id for member in team_members if member.team_id == team.id]
        for user_id in member_ids:
            assert (team.circle_id, user_id) in circle_member_pairs

        pending_count = sum(
            1
            for invitation in invitations
            if invitation.team_id == team.id and invitation.status == InvitationStatus.PENDING
        )
        current_members = len(member_ids)
        assert current_members <= team.max_members
        if current_members >= team.max_members:
            assert pending_count == 0

    for invitation in invitations:
        team = next((candidate for candidate in teams if candidate.id == invitation.team_id), None)
        assert team is not None
        assert (team.circle_id, invitation.inviter_id) in circle_member_pairs
        assert (team.circle_id, invitation.invitee_id) in circle_member_pairs

        joined_user_id = (
            invitation.invitee_id
            if invitation.kind == InvitationKind.INVITE
            else invitation.inviter_id
        )
        is_joined_member = (invitation.team_id, joined_user_id) in team_member_pairs
        if invitation.status == InvitationStatus.ACCEPTED:
            assert is_joined_member
        if invitation.status == InvitationStatus.REJECTED:
            assert not is_joined_member

    member_user_ids = {user_id for _, user_id in circle_member_pairs}
    for user_id in member_user_ids:
        assert user_id in profiles


def test_demo_seed_dataset_is_consistent(db_session):
    seed_dataset(db_session, "demo")
    _seed_datasets_have_internal_consistency(db_session)


def test_stress_seed_dataset_is_consistent(db_session):
    seed_dataset(db_session, "stress")
    _seed_datasets_have_internal_consistency(db_session)

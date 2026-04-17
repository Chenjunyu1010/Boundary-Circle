from sqlmodel import select

from scripts.seed_data import (
    dataset_circle_prefix,
    dataset_team_prefix,
    dataset_user_prefix,
    reset_dataset,
    seed_dataset,
)
from src.models.core import Circle, User, UserCreate
from src.models.tags import CircleMember, CircleRole, TagDefinition
from src.models.teams import Invitation, InvitationStatus, Team, TeamMember
from src.services.users import create_user_account


def count_seed_users(db_session, dataset: str) -> int:
    return len(
        [
            user
            for user in db_session.exec(select(User)).all()
            if user.username.startswith(dataset_user_prefix(dataset))
        ]
    )


def count_seed_circles(db_session, dataset: str) -> int:
    return len(
        [
            circle
            for circle in db_session.exec(select(Circle)).all()
            if circle.name.startswith(dataset_circle_prefix(dataset))
        ]
    )


def count_teams_for_dataset(db_session, dataset: str) -> int:
    return len(
        [
            team
            for team in db_session.exec(select(Team)).all()
            if team.name.startswith(dataset_team_prefix(dataset))
        ]
    )


def test_seed_demo_creates_expected_entities_and_markers(db_session):
    summary = seed_dataset(db_session, "demo")

    assert summary.users == 7
    assert summary.circles == 2
    assert summary.teams == 4
    assert summary.invitations == 5
    assert count_seed_users(db_session, "demo") == 7
    assert count_seed_circles(db_session, "demo") == 2

    seeded_user = db_session.exec(
        select(User).where(User.username == "seed_demo_alice")
    ).first()
    assert seeded_user is not None
    assert seeded_user.hashed_password != "SeedData123!"
    assert "$" in seeded_user.hashed_password


def test_seed_demo_is_repeatable_without_duplication(db_session):
    first = seed_dataset(db_session, "demo")
    second = seed_dataset(db_session, "demo")

    assert first.users == second.users == 7
    assert count_seed_users(db_session, "demo") == 7
    assert count_seed_circles(db_session, "demo") == 2
    assert count_teams_for_dataset(db_session, "demo") == 4


def test_seed_stress_creates_varied_dataset(db_session):
    summary = seed_dataset(db_session, "stress")

    assert summary.users == 18
    assert summary.circles == 4
    assert summary.teams == 10
    assert summary.invitations == 12
    assert count_seed_users(db_session, "stress") == 18
    assert count_seed_circles(db_session, "stress") == 4

    tag_names = {tag.name for tag in db_session.exec(select(TagDefinition)).all()}
    assert {"Major", "Preferred Role", "Tech Stack", "Focus Track"} <= tag_names

    statuses = {invitation.status for invitation in db_session.exec(select(Invitation)).all()}
    assert statuses == {
        InvitationStatus.PENDING,
        InvitationStatus.ACCEPTED,
        InvitationStatus.REJECTED,
    }


def test_demo_reset_preserves_non_seed_data(db_session):
    keeper_a = create_user_account(
        db_session,
        UserCreate(username="keeper_a", email="keeper_a@example.com", full_name="Keeper A", password="pw123456"),
    )
    keeper_b = create_user_account(
        db_session,
        UserCreate(username="keeper_b", email="keeper_b@example.com", full_name="Keeper B", password="pw123456"),
    )
    circle = Circle(name="Real Circle", description="Real data", category="Course", creator_id=keeper_a.id)
    db_session.add(circle)
    db_session.commit()
    db_session.refresh(circle)
    db_session.add(CircleMember(user_id=keeper_a.id, circle_id=circle.id, role=CircleRole.ADMIN))
    db_session.add(CircleMember(user_id=keeper_b.id, circle_id=circle.id, role=CircleRole.MEMBER))
    db_session.commit()

    team = Team(name="Real Team", description="Real team", circle_id=circle.id, creator_id=keeper_a.id, max_members=4)
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)
    db_session.add(TeamMember(team_id=team.id, user_id=keeper_a.id))
    db_session.commit()

    invitation = Invitation(
        team_id=team.id,
        inviter_id=keeper_a.id,
        invitee_id=keeper_b.id,
        status=InvitationStatus.PENDING,
    )
    db_session.add(invitation)
    db_session.commit()

    seed_dataset(db_session, "demo")
    reset_dataset(db_session, "demo")

    assert db_session.exec(select(User).where(User.username == "keeper_a")).first() is not None
    assert db_session.exec(select(User).where(User.username == "keeper_b")).first() is not None
    assert db_session.exec(select(Circle).where(Circle.name == "Real Circle")).first() is not None
    assert db_session.exec(select(Team).where(Team.name == "Real Team")).first() is not None
    assert db_session.get(Invitation, invitation.id) is not None
    assert count_seed_users(db_session, "demo") == 0


def test_stress_reset_does_not_delete_demo_data(db_session):
    seed_dataset(db_session, "demo")
    seed_dataset(db_session, "stress")

    reset_dataset(db_session, "stress")

    assert count_seed_users(db_session, "stress") == 0
    assert count_seed_circles(db_session, "stress") == 0
    assert count_seed_users(db_session, "demo") == 7
    assert count_seed_circles(db_session, "demo") == 2

from sqlmodel import select

from scripts.seed_data import (
    dataset_circle_prefix,
    dataset_team_prefix,
    dataset_user_prefix,
    reset_dataset,
    seed_dataset,
)
from src.models.core import Circle, User, UserCreate
from src.models.profile import UserProfile
from src.models.tags import CircleMember, CircleRole, TagDefinition
from src.models.teams import decode_freedom_profile
from src.models.teams import Invitation, InvitationKind, InvitationStatus, Team, TeamMember
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


def count_seed_profiles(db_session, dataset: str) -> int:
    seed_user_ids = {
        user.id
        for user in db_session.exec(select(User)).all()
        if user.username.startswith(dataset_user_prefix(dataset))
    }
    return len(
        [
            profile
            for profile in db_session.exec(select(UserProfile)).all()
            if profile.user_id in seed_user_ids
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


def seeded_circle_members(db_session, dataset: str) -> list[CircleMember]:
    seed_circle_ids = {
        circle.id
        for circle in db_session.exec(select(Circle)).all()
        if circle.name.startswith(dataset_circle_prefix(dataset)) and circle.id is not None
    }
    return [
        membership
        for membership in db_session.exec(select(CircleMember)).all()
        if membership.circle_id in seed_circle_ids
    ]


def seeded_teams(db_session, dataset: str) -> list[Team]:
    return [
        team
        for team in db_session.exec(select(Team)).all()
        if team.name.startswith(dataset_team_prefix(dataset))
    ]


def assert_seeded_freedom_profiles_present(db_session, dataset: str) -> None:
    memberships = seeded_circle_members(db_session, dataset)
    teams = seeded_teams(db_session, dataset)
    assert memberships
    assert teams

    for membership in memberships:
        assert membership.freedom_tag_text.strip()
        assert decode_freedom_profile(membership.freedom_tag_profile_json)["keywords"]

    for team in teams:
        assert team.freedom_requirement_text.strip()
        assert decode_freedom_profile(team.freedom_requirement_profile_json)["keywords"]


def test_seed_demo_creates_expected_entities_and_markers(db_session):
    summary = seed_dataset(db_session, "demo")

    assert summary.users == 7
    assert summary.circles == 2
    assert summary.teams == 4
    assert summary.invitations == 6
    assert count_seed_users(db_session, "demo") == 7
    assert count_seed_profiles(db_session, "demo") == 7
    assert count_seed_circles(db_session, "demo") == 2
    assert_seeded_freedom_profiles_present(db_session, "demo")

    seeded_user = db_session.exec(
        select(User).where(User.username == "seed_demo_alice")
    ).first()
    assert seeded_user is not None
    assert seeded_user.hashed_password != "SeedData123!"
    assert "$" in seeded_user.hashed_password

    seeded_profile = db_session.exec(
        select(UserProfile).where(UserProfile.user_id == seeded_user.id)
    ).first()
    assert seeded_profile is not None
    assert seeded_profile.gender is not None
    assert seeded_profile.birthday is not None
    assert seeded_profile.bio

    join_requests = [
        invitation
        for invitation in db_session.exec(select(Invitation)).all()
        if invitation.kind == InvitationKind.JOIN_REQUEST
    ]
    assert join_requests


def test_seed_demo_is_repeatable_without_duplication(db_session):
    first = seed_dataset(db_session, "demo")
    second = seed_dataset(db_session, "demo")

    assert first.users == second.users == 7
    assert count_seed_users(db_session, "demo") == 7
    assert count_seed_circles(db_session, "demo") == 2
    assert_seeded_freedom_profiles_present(db_session, "demo")
    assert count_teams_for_dataset(db_session, "demo") == 4


def test_seed_stress_creates_varied_dataset(db_session):
    summary = seed_dataset(db_session, "stress")

    assert summary.users == 18
    assert summary.circles == 4
    assert summary.teams == 10
    assert summary.invitations == 16
    assert count_seed_users(db_session, "stress") == 18
    assert count_seed_profiles(db_session, "stress") == 18
    assert count_seed_circles(db_session, "stress") == 4
    assert_seeded_freedom_profiles_present(db_session, "stress")

    tag_names = {tag.name for tag in db_session.exec(select(TagDefinition)).all()}
    assert {"Major", "Preferred Role", "Tech Stack", "Focus Track"} <= tag_names

    statuses = {invitation.status for invitation in db_session.exec(select(Invitation)).all()}
    assert statuses == {
        InvitationStatus.PENDING,
        InvitationStatus.ACCEPTED,
        InvitationStatus.REJECTED,
    }
    kinds = {invitation.kind for invitation in db_session.exec(select(Invitation)).all()}
    assert kinds == {
        InvitationKind.INVITE,
        InvitationKind.JOIN_REQUEST,
    }


def test_seed_stress2_creates_large_diverse_dataset(db_session):
    summary = seed_dataset(db_session, "stress2")

    assert summary.users >= 30
    assert summary.circles >= 6
    assert summary.teams >= 16
    assert summary.invitations >= 24
    assert count_seed_users(db_session, "stress2") == summary.users
    assert count_seed_profiles(db_session, "stress2") == summary.users
    assert count_seed_circles(db_session, "stress2") == summary.circles
    assert_seeded_freedom_profiles_present(db_session, "stress2")

    teams = seeded_teams(db_session, "stress2")
    assert any(team.required_tags_json not in (None, "[]") for team in teams)
    assert any(team.required_tag_rules_json not in (None, "[]") for team in teams)
    assert any("AI" in team.freedom_requirement_text for team in teams)
    assert any("Figma" in team.freedom_requirement_text for team in teams)

    memberships = seeded_circle_members(db_session, "stress2")
    freedom_texts = [membership.freedom_tag_text for membership in memberships]
    assert any("AI" in text for text in freedom_texts)
    assert any("数据" in text for text in freedom_texts)
    assert any("Figma" in text for text in freedom_texts)

    statuses = {
        invitation.status
        for invitation in db_session.exec(select(Invitation)).all()
        if invitation.team_id in {team.id for team in teams}
    }
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
    assert keeper_a.id is not None
    assert keeper_b.id is not None
    circle = Circle(name="Real Circle", description="Real data", category="Course", creator_id=keeper_a.id)
    db_session.add(circle)
    db_session.commit()
    db_session.refresh(circle)
    assert circle.id is not None
    db_session.add(CircleMember(user_id=keeper_a.id, circle_id=circle.id, role=CircleRole.ADMIN))
    db_session.add(CircleMember(user_id=keeper_b.id, circle_id=circle.id, role=CircleRole.MEMBER))
    db_session.commit()

    team = Team(name="Real Team", description="Real team", circle_id=circle.id, creator_id=keeper_a.id, max_members=4)
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)
    assert team.id is not None
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
    assert_seeded_freedom_profiles_present(db_session, "demo")


def test_stress2_reset_does_not_delete_existing_seed_datasets(db_session):
    seed_dataset(db_session, "demo")
    seed_dataset(db_session, "stress")
    seed_dataset(db_session, "stress2")

    reset_dataset(db_session, "stress2")

    assert count_seed_users(db_session, "stress2") == 0
    assert count_seed_circles(db_session, "stress2") == 0
    assert count_seed_users(db_session, "demo") == 7
    assert count_seed_circles(db_session, "demo") == 2
    assert count_seed_users(db_session, "stress") == 18
    assert count_seed_circles(db_session, "stress") == 4

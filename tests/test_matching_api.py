from __future__ import annotations

from typing import Tuple

from fastapi.testclient import TestClient

from src.main import app
from src.models.tags import CircleMember, CircleRole, TagDataType, TagDefinition, UserTag
from src.models.teams import TeamMember


client = TestClient(app)


def register_and_login(username: str, email: str) -> Tuple[dict, dict]:
    """Helper to register a user and return (user_payload, auth_headers)."""
    register_response = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": "secret123"},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": "secret123"},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return register_response.json(), headers


def test_match_users_for_team_orders_by_coverage_and_jaccard(db_session) -> None:
    creator, creator_headers = register_and_login(
        "matcher_creator", "matcher_creator@example.com"
    )

    # Create circle via API
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Matching Circle", "description": "Circle for matching tests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    # Register three candidate users and make them circle members
    alice, _ = register_and_login("alice", "alice@example.com")
    bob, _ = register_and_login("bob", "bob@example.com")
    carol, _ = register_and_login("carol", "carol@example.com")

    db_session.add(
        CircleMember(
            user_id=alice["id"],
            circle_id=circle["id"],
            role=CircleRole.MEMBER,
        )
    )
    db_session.add(
        CircleMember(
            user_id=bob["id"],
            circle_id=circle["id"],
            role=CircleRole.MEMBER,
        )
    )
    db_session.add(
        CircleMember(
            user_id=carol["id"],
            circle_id=circle["id"],
            role=CircleRole.MEMBER,
        )
    )
    db_session.commit()

    # Create tag definitions: role, stack, extra
    role_tag = TagDefinition(
        circle_id=circle["id"],
        name="role",
        data_type=TagDataType.STRING,
        required=False,
    )
    stack_tag = TagDefinition(
        circle_id=circle["id"],
        name="stack",
        data_type=TagDataType.STRING,
        required=False,
    )
    extra_tag = TagDefinition(
        circle_id=circle["id"],
        name="extra",
        data_type=TagDataType.STRING,
        required=False,
    )
    db_session.add(role_tag)
    db_session.add(stack_tag)
    db_session.add(extra_tag)
    db_session.commit()
    db_session.refresh(role_tag)
    db_session.refresh(stack_tag)
    db_session.refresh(extra_tag)

    # Alice: role + stack + extra  -> best coverage and richer profile
    db_session.add(
        UserTag(
            user_id=alice["id"],
            circle_id=circle["id"],
            tag_definition_id=role_tag.id,
            value="backend",
        )
    )
    db_session.add(
        UserTag(
            user_id=alice["id"],
            circle_id=circle["id"],
            tag_definition_id=stack_tag.id,
            value="fastapi",
        )
    )
    db_session.add(
        UserTag(
            user_id=alice["id"],
            circle_id=circle["id"],
            tag_definition_id=extra_tag.id,
            value="extra1",
        )
    )

    # Bob: only role -> partial coverage
    db_session.add(
        UserTag(
            user_id=bob["id"],
            circle_id=circle["id"],
            tag_definition_id=role_tag.id,
            value="backend",
        )
    )

    # Carol: unrelated tag only -> zero coverage, should not appear
    db_session.add(
        UserTag(
            user_id=carol["id"],
            circle_id=circle["id"],
            tag_definition_id=extra_tag.id,
            value="extra2",
        )
    )
    db_session.commit()

    # Create team requiring role and stack
    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Match Team",
            "description": "Team for matching",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": ["role", "stack"],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    # Ask for candidate users
    match_response = client.get(
        f"/matching/users?team_id={team['id']}",
        headers=creator_headers,
    )
    assert match_response.status_code == 200
    data = match_response.json()

    # Carol should not be present (zero coverage), Alice should appear before Bob
    usernames = [item["username"] for item in data]
    assert "carol" not in usernames
    assert "alice" in usernames
    assert "bob" in usernames
    assert usernames.index("alice") < usernames.index("bob")


def test_match_teams_for_user_basic(db_session) -> None:
    user, user_headers = register_and_login("match_user", "match_user@example.com")

    # Create circle and make user a member via Circle creator path
    creator, creator_headers = register_and_login(
        "circle_creator2", "circle_creator2@example.com"
    )
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Team Match Circle", "description": "Circle for team matching"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(
        CircleMember(user_id=user["id"], circle_id=circle["id"], role=CircleRole.MEMBER)
    )
    db_session.commit()

    # Tag definitions
    role_tag = TagDefinition(
        circle_id=circle["id"],
        name="role",
        data_type=TagDataType.STRING,
        required=False,
    )
    stack_tag = TagDefinition(
        circle_id=circle["id"],
        name="stack",
        data_type=TagDataType.STRING,
        required=False,
    )
    db_session.add(role_tag)
    db_session.add(stack_tag)
    db_session.commit()
    db_session.refresh(role_tag)
    db_session.refresh(stack_tag)

    # User has only role
    db_session.add(
        UserTag(
            user_id=user["id"],
            circle_id=circle["id"],
            tag_definition_id=role_tag.id,
            value="backend",
        )
    )
    db_session.commit()

    # Two teams: one requiring only role, one requiring role+stack.
    # They are created by the circle creator so the candidate user is not a member yet.
    team1_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Role Only Team",
            "description": "Requires role only",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": ["role"],
        },
    )
    assert team1_response.status_code == 201

    team2_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Role Stack Team",
            "description": "Requires role and stack",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": ["role", "stack"],
        },
    )
    assert team2_response.status_code == 201

    match_response = client.get(
        f"/matching/teams?circle_id={circle['id']}",
        headers=user_headers,
    )
    assert match_response.status_code == 200
    teams = match_response.json()

    # Only teams with non-zero coverage should appear
    assert len(teams) >= 1
    names = [item["team"]["name"] for item in teams]
    assert "Role Only Team" in names


def test_matching_requires_authentication() -> None:
    response = client.get("/matching/teams?circle_id=1")
    assert response.status_code == 401


def test_match_users_requires_team_membership(db_session) -> None:
    """非队伍成员调用 /matching/users 应返回 403。"""
    creator, creator_headers = register_and_login(
        "perm_creator", "perm_creator@example.com"
    )
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Perm Circle", "description": "Circle for permission tests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    outsider, outsider_headers = register_and_login(
        "perm_outsider", "perm_outsider@example.com"
    )
    # Outsider is circle member but not team member
    db_session.add(
        CircleMember(
            user_id=outsider["id"],
            circle_id=circle["id"],
            role=CircleRole.MEMBER,
        )
    )
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Perm Team",
            "description": "Team for permission tests",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    resp = client.get(f"/matching/users?team_id={team['id']}", headers=outsider_headers)
    assert resp.status_code == 403
    assert (
        resp.json()["detail"]
        == "Only team creator or members can view recommendations"
    )


def test_match_teams_requires_circle_membership(db_session) -> None:
    """非圈子成员调用 /matching/teams 应返回 403。"""
    creator, creator_headers = register_and_login(
        "circle_creator3", "circle_creator3@example.com"
    )
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Outer Circle", "description": "Circle for permission tests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    outsider, outsider_headers = register_and_login(
        "outer_user", "outer_user@example.com"
    )
    # outsider is NOT added as CircleMember

    resp = client.get(f"/matching/teams?circle_id={circle['id']}", headers=outsider_headers)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "User must join the circle first"


def test_match_teams_skips_locked_teams(db_session) -> None:
    """已满/锁定的队伍不应出现在 /matching/teams 的推荐列表中。"""
    user, user_headers = register_and_login("lock_user", "lock_user@example.com")
    creator, creator_headers = register_and_login(
        "lock_creator", "lock_creator@example.com"
    )

    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Lock Circle", "description": "Circle for locked team tests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(
        CircleMember(user_id=user["id"], circle_id=circle["id"], role=CircleRole.MEMBER)
    )
    db_session.commit()

    # Tag definition and user tag so coverage > 0
    role_tag = TagDefinition(
        circle_id=circle["id"],
        name="role",
        data_type=TagDataType.STRING,
        required=False,
    )
    db_session.add(role_tag)
    db_session.commit()
    db_session.refresh(role_tag)

    db_session.add(
        UserTag(
            user_id=user["id"],
            circle_id=circle["id"],
            tag_definition_id=role_tag.id,
            value="backend",
        )
    )
    db_session.commit()

    # Locked team: max_members=2, creator auto-joins; add a second member to fill the team
    locked_team_resp = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Locked Role Team",
            "description": "Full team",
            "circle_id": circle["id"],
            "max_members": 2,
            "required_tags": ["role"],
        },
    )
    assert locked_team_resp.status_code == 201
    locked_team = locked_team_resp.json()

    filler, _ = register_and_login("lock_filler", "lock_filler@example.com")
    db_session.add(
        CircleMember(user_id=filler["id"], circle_id=circle["id"], role=CircleRole.MEMBER)
    )
    db_session.add(
        TeamMember(team_id=locked_team["id"], user_id=filler["id"])
    )
    db_session.commit()

    # Open team: same required tags but capacity for more members
    open_team_resp = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Open Role Team",
            "description": "Has space",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": ["role"],
        },
    )
    assert open_team_resp.status_code == 201

    resp = client.get(
        f"/matching/teams?circle_id={circle['id']}",
        headers=user_headers,
    )
    assert resp.status_code == 200
    teams = resp.json()
    names = [item["team"]["name"] for item in teams]
    assert "Open Role Team" in names
    assert "Locked Role Team" not in names


def test_match_users_with_no_required_tags_returns_candidates(db_session) -> None:
    """队伍没有 required_tags 时仍应返回候选用户，覆盖率视为 1。"""
    creator, creator_headers = register_and_login(
        "noreq_creator", "noreq_creator@example.com"
    )
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "NoReq Circle", "description": "Circle for no-required tags"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    u1, _ = register_and_login("noreq_u1", "noreq_u1@example.com")
    u2, _ = register_and_login("noreq_u2", "noreq_u2@example.com")

    for u in (u1, u2):
        db_session.add(
            CircleMember(user_id=u["id"], circle_id=circle["id"], role=CircleRole.MEMBER)
        )
    db_session.commit()

    team_resp = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "NoReq Team",
            "description": "Team with no required tags",
            "circle_id": circle["id"],
            "max_members": 5,
            "required_tags": [],
        },
    )
    assert team_resp.status_code == 201
    team = team_resp.json()

    resp = client.get(
        f"/matching/users?team_id={team['id']}",
        headers=creator_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # Both users should be considered candidates with coverage_score == 1.0
    usernames = {item["username"] for item in data}
    assert "noreq_u1" in usernames
    assert "noreq_u2" in usernames
    for item in data:
        assert item["coverage_score"] == 1.0


def test_match_users_for_team_uses_single_select_value_rules(db_session) -> None:
    creator, creator_headers = register_and_login(
        "value_creator", "value_creator@example.com"
    )
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Value Circle", "description": "Single select matching"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    matching_user, _ = register_and_login("value_match", "value_match@example.com")
    mismatching_user, _ = register_and_login("value_miss", "value_miss@example.com")

    for user in (matching_user, mismatching_user):
        db_session.add(
            CircleMember(user_id=user["id"], circle_id=circle["id"], role=CircleRole.MEMBER)
        )
    db_session.commit()

    major_tag = TagDefinition(
        circle_id=circle["id"],
        name="Major",
        data_type=TagDataType.SINGLE_SELECT,
        required=False,
        options='["Artificial Intelligence", "Software Engineering"]',
    )
    db_session.add(major_tag)
    db_session.commit()
    db_session.refresh(major_tag)

    db_session.add(
        UserTag(
            user_id=matching_user["id"],
            circle_id=circle["id"],
            tag_definition_id=major_tag.id,
            value="Artificial Intelligence",
        )
    )
    db_session.add(
        UserTag(
            user_id=mismatching_user["id"],
            circle_id=circle["id"],
            tag_definition_id=major_tag.id,
            value="Software Engineering",
        )
    )
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "AI Team",
            "description": "Needs AI major",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": ["Major"],
            "required_tag_rules": [
                {"tag_name": "Major", "expected_value": "Artificial Intelligence"}
            ],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    match_response = client.get(
        f"/matching/users?team_id={team['id']}",
        headers=creator_headers,
    )
    assert match_response.status_code == 200
    usernames = [item["username"] for item in match_response.json()]
    assert "value_match" in usernames
    assert "value_miss" not in usernames


def test_match_users_for_team_uses_multi_select_overlap_rules(db_session) -> None:
    creator, creator_headers = register_and_login(
        "stack_creator", "stack_creator@example.com"
    )
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Stack Circle", "description": "Multi select matching"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    overlap_user, _ = register_and_login("stack_overlap", "stack_overlap@example.com")
    miss_user, _ = register_and_login("stack_miss", "stack_miss@example.com")

    for user in (overlap_user, miss_user):
        db_session.add(
            CircleMember(user_id=user["id"], circle_id=circle["id"], role=CircleRole.MEMBER)
        )
    db_session.commit()

    stack_tag = TagDefinition(
        circle_id=circle["id"],
        name="Tech Stack",
        data_type=TagDataType.MULTI_SELECT,
        required=False,
        options='["Python", "React", "SQL"]',
    )
    db_session.add(stack_tag)
    db_session.commit()
    db_session.refresh(stack_tag)

    db_session.add(
        UserTag(
            user_id=overlap_user["id"],
            circle_id=circle["id"],
            tag_definition_id=stack_tag.id,
            value='["Python", "FastAPI"]',
        )
    )
    db_session.add(
        UserTag(
            user_id=miss_user["id"],
            circle_id=circle["id"],
            tag_definition_id=stack_tag.id,
            value='["Java"]',
        )
    )
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Python Team",
            "description": "Needs overlapping stack",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": ["Tech Stack"],
            "required_tag_rules": [
                {"tag_name": "Tech Stack", "expected_value": ["Python", "SQL"]}
            ],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    match_response = client.get(
        f"/matching/users?team_id={team['id']}",
        headers=creator_headers,
    )
    assert match_response.status_code == 200
    usernames = [item["username"] for item in match_response.json()]
    assert "stack_overlap" in usernames
    assert "stack_miss" not in usernames


def test_match_teams_for_user_uses_structured_value_rules(db_session) -> None:
    user, user_headers = register_and_login("team_value_user", "team_value_user@example.com")
    creator, creator_headers = register_and_login(
        "team_value_creator", "team_value_creator@example.com"
    )

    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Team Value Circle", "description": "Structured team matching"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(
        CircleMember(user_id=user["id"], circle_id=circle["id"], role=CircleRole.MEMBER)
    )
    db_session.commit()

    major_tag = TagDefinition(
        circle_id=circle["id"],
        name="Major",
        data_type=TagDataType.SINGLE_SELECT,
        required=False,
        options='["Artificial Intelligence", "Software Engineering"]',
    )
    db_session.add(major_tag)
    db_session.commit()
    db_session.refresh(major_tag)

    db_session.add(
        UserTag(
            user_id=user["id"],
            circle_id=circle["id"],
            tag_definition_id=major_tag.id,
            value="Artificial Intelligence",
        )
    )
    db_session.commit()

    matching_team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "AI Only Team",
            "description": "Matches user major",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": ["Major"],
            "required_tag_rules": [
                {"tag_name": "Major", "expected_value": "Artificial Intelligence"}
            ],
        },
    )
    assert matching_team_response.status_code == 201

    mismatching_team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "SE Only Team",
            "description": "Does not match user major",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": ["Major"],
            "required_tag_rules": [
                {"tag_name": "Major", "expected_value": "Software Engineering"}
            ],
        },
    )
    assert mismatching_team_response.status_code == 201

    match_response = client.get(
        f"/matching/teams?circle_id={circle['id']}",
        headers=user_headers,
    )
    assert match_response.status_code == 200
    team_names = [item["team"]["name"] for item in match_response.json()]
    assert "AI Only Team" in team_names
    assert "SE Only Team" not in team_names

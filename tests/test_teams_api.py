from fastapi.testclient import TestClient

from src.main import app
from src.models.tags import CircleMember, CircleRole
from src.models.teams import (
    TeamCreate,
    TeamRequirementRule,
    decode_required_tag_rules,
    encode_required_tag_rules,
)


client = TestClient(app)


def register_and_login(username: str, email: str) -> tuple[dict, dict]:
    register_response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "secret123",
        },
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


def test_create_team_requires_authenticated_circle_member():
    creator, creator_headers = register_and_login("teamcreator", "teamcreator@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Issue37 Team Circle", "description": "Circle for team tests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    create_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Alpha Team",
            "description": "First team",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": ["role", "skill"],
        },
    )

    assert create_response.status_code == 201
    payload = create_response.json()
    assert payload["name"] == "Alpha Team"
    assert payload["creator_id"] == creator["id"]
    assert payload["creator_username"] == creator["username"]
    assert payload["current_members"] == 1
    assert payload["status"] == "Recruiting"
    assert payload["member_ids"] == [creator["id"]]


def test_create_team_rejects_invalid_max_members():
    creator, creator_headers = register_and_login("invalidteam", "invalidteam@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Invalid Team Circle", "description": "Circle for invalid create"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    create_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Tiny Team",
            "description": "Too small",
            "circle_id": circle["id"],
            "max_members": 1,
            "required_tags": [],
        },
    )

    assert create_response.status_code == 422


def test_non_circle_member_cannot_create_team():
    creator, creator_headers = register_and_login("outercreator", "outercreator@example.com")
    outsider, outsider_headers = register_and_login("outsider", "outsider@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Member Guard Circle", "description": "Only members can create teams"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    create_response = client.post(
        "/teams",
        headers=outsider_headers,
        json={
            "name": "Unauthorized Team",
            "description": "Should fail",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
        },
    )

    assert create_response.status_code == 403
    assert create_response.json()["detail"] == "User must join the circle first"


def test_member_can_leave_team(db_session):
    creator, creator_headers = register_and_login("leavecaptain", "leavecaptain@example.com")
    invitee, invitee_headers = register_and_login("leavemember", "leavemember@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Leave Circle", "description": "Circle for leave flow"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(CircleMember(user_id=invitee["id"], circle_id=circle["id"], role=CircleRole.MEMBER))
    db_session.commit()

    team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Leave Team",
            "description": "Team to leave",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
        },
    )
    assert team_response.status_code == 201
    team = team_response.json()

    invitation_response = client.post(
        f"/teams/{team['id']}/invite",
        headers=creator_headers,
        json={"user_id": invitee["id"], "team_name": team["name"]},
    )
    assert invitation_response.status_code == 201
    invitation = invitation_response.json()

    accept_response = client.post(
        f"/invitations/{invitation['id']}/respond",
        headers=invitee_headers,
        json={"accept": True},
    )
    assert accept_response.status_code == 200

    leave_response = client.delete(f"/teams/{team['id']}/leave", headers=invitee_headers)
    assert leave_response.status_code == 204

    teams_response = client.get(f"/circles/{circle['id']}/teams", headers=creator_headers)
    assert teams_response.status_code == 200
    stored_team = teams_response.json()[0]
    assert stored_team["current_members"] == 1
    assert stored_team["member_ids"] == [creator["id"]]


def test_non_circle_member_cannot_list_teams_or_members():
    creator, creator_headers = register_and_login("teamguard", "teamguard@example.com")
    outsider, outsider_headers = register_and_login("teamoutsider", "teamoutsider@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Team Guard Circle", "description": "Circle for access checks"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    teams_response = client.get(f"/circles/{circle['id']}/teams", headers=outsider_headers)
    assert teams_response.status_code == 403
    assert teams_response.json()["detail"] == "User must join the circle first"

    members_response = client.get(f"/circles/{circle['id']}/members", headers=outsider_headers)
    assert members_response.status_code == 403
    assert members_response.json()["detail"] == "User must join the circle first"


def test_team_create_accepts_required_tag_rules_schema():
    payload = TeamCreate(
        name="Structured Team",
        description="Has structured rules",
        circle_id=1,
        max_members=4,
        required_tags=["Major", "Tech Stack"],
        required_tag_rules=[
            TeamRequirementRule(tag_name="Major", expected_value="Artificial Intelligence"),
            TeamRequirementRule(tag_name="Tech Stack", expected_value=["Python", "SQL"]),
        ],
    )

    assert payload.required_tag_rules[0].tag_name == "Major"
    assert payload.required_tag_rules[0].expected_value == "Artificial Intelligence"
    assert payload.required_tag_rules[1].expected_value == ["Python", "SQL"]


def test_required_tag_rules_round_trip_through_json_helpers():
    rules = [
        TeamRequirementRule(tag_name="Major", expected_value="Artificial Intelligence"),
        TeamRequirementRule(tag_name="Tech Stack", expected_value=["Python", "SQL"]),
    ]

    encoded = encode_required_tag_rules(rules)
    decoded = decode_required_tag_rules(encoded)

    assert len(decoded) == 2
    assert decoded[0].tag_name == "Major"
    assert decoded[0].expected_value == "Artificial Intelligence"
    assert decoded[1].tag_name == "Tech Stack"
    assert decoded[1].expected_value == ["Python", "SQL"]


def test_decode_required_tag_rules_returns_empty_list_for_malformed_json():
    assert decode_required_tag_rules("not-json") == []
    assert decode_required_tag_rules('{"tag_name":"Major"}') == []


def test_create_team_persists_required_tag_rules():
    creator, creator_headers = register_and_login("rulectx", "rulectx@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Rule Circle", "description": "Circle for structured team rules"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    create_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Rule Team",
            "description": "Structured matching team",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": ["Major", "Tech Stack"],
            "required_tag_rules": [
                {"tag_name": "Major", "expected_value": "Artificial Intelligence"},
                {"tag_name": "Tech Stack", "expected_value": ["Python", "SQL"]},
            ],
        },
    )

    assert create_response.status_code == 201
    payload = create_response.json()
    assert payload["required_tags"] == ["Major", "Tech Stack"]
    assert payload["required_tag_rules"] == [
        {"tag_name": "Major", "expected_value": "Artificial Intelligence"},
        {"tag_name": "Tech Stack", "expected_value": ["Python", "SQL"]},
    ]


def test_create_team_without_required_tag_rules_stays_compatible():
    creator, creator_headers = register_and_login("legacyteam", "legacyteam@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Legacy Team Circle", "description": "Compatibility test"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    create_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Legacy Team",
            "description": "No structured rules",
            "circle_id": circle["id"],
            "max_members": 4,
            "required_tags": ["Role"],
        },
    )

    assert create_response.status_code == 201
    payload = create_response.json()
    assert payload["required_tags"] == ["Role"]
    assert payload["required_tag_rules"] == []

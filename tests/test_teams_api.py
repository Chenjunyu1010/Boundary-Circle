from fastapi.testclient import TestClient

from src.main import app
from src.models.tags import CircleMember, CircleRole


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
        f"/circles/?creator_id={creator['id']}",
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
    assert payload["current_members"] == 1
    assert payload["status"] == "Recruiting"
    assert payload["member_ids"] == [creator["id"]]


def test_create_team_rejects_invalid_max_members():
    creator, creator_headers = register_and_login("invalidteam", "invalidteam@example.com")
    circle_response = client.post(
        f"/circles/?creator_id={creator['id']}",
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
    creator, _ = register_and_login("outercreator", "outercreator@example.com")
    outsider, outsider_headers = register_and_login("outsider", "outsider@example.com")
    circle_response = client.post(
        f"/circles/?creator_id={creator['id']}",
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
        f"/circles/?creator_id={creator['id']}",
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

    teams_response = client.get(f"/circles/{circle['id']}/teams")
    assert teams_response.status_code == 200
    stored_team = teams_response.json()[0]
    assert stored_team["current_members"] == 1
    assert stored_team["member_ids"] == [creator["id"]]

from fastapi.testclient import TestClient

from src.main import app


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
    return register_response.json(), {"Authorization": f"Bearer {token}"}


def test_join_submit_tags_create_team_invite_and_accept_flow():
    creator, creator_headers = register_and_login("issue37creator", "issue37creator@example.com")
    invitee, invitee_headers = register_and_login("issue37invitee", "issue37invitee@example.com")

    circle_response = client.post(
        f"/circles/?creator_id={creator['id']}",
        json={
            "name": "Issue 37 Integration Circle",
            "description": "End-to-end team formation flow",
            "category": "Course",
        },
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    join_response = client.post(f"/circles/{circle['id']}/join", headers=invitee_headers)
    assert join_response.status_code == 200

    members_response = client.get(f"/circles/{circle['id']}/members", headers=creator_headers)
    assert members_response.status_code == 200
    member_ids = {member["id"] for member in members_response.json()}
    assert creator["id"] in member_ids
    assert invitee["id"] in member_ids

    role_tag_response = client.post(
        f"/circles/{circle['id']}/tags?current_user_id={creator['id']}",
        json={
            "name": "Role",
            "data_type": "enum",
            "required": True,
            "options": '["Backend", "Frontend"]',
        },
    )
    assert role_tag_response.status_code == 201
    role_tag = role_tag_response.json()

    skill_tag_response = client.post(
        f"/circles/{circle['id']}/tags?current_user_id={creator['id']}",
        json={"name": "Skill", "data_type": "string", "required": True},
    )
    assert skill_tag_response.status_code == 201
    skill_tag = skill_tag_response.json()

    submit_role_response = client.post(
        f"/circles/{circle['id']}/tags/submit?current_user_id={invitee['id']}",
        json={"tag_definition_id": role_tag["id"], "value": "Backend"},
    )
    submit_skill_response = client.post(
        f"/circles/{circle['id']}/tags/submit?current_user_id={invitee['id']}",
        json={"tag_definition_id": skill_tag["id"], "value": "FastAPI"},
    )
    assert submit_role_response.status_code == 200
    assert submit_skill_response.status_code == 200

    my_tags_response = client.get(
        f"/circles/{circle['id']}/tags/my?current_user_id={invitee['id']}"
    )
    assert my_tags_response.status_code == 200
    my_tags = my_tags_response.json()
    assert {item["value"] for item in my_tags} == {"Backend", "FastAPI"}

    create_team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Issue 37 Team",
            "description": "Integration team flow",
            "circle_id": circle["id"],
            "max_members": 2,
            "required_tags": ["Role", "Skill"],
        },
    )
    assert create_team_response.status_code == 201
    team = create_team_response.json()
    assert team["current_members"] == 1
    assert team["member_ids"] == [creator["id"]]

    invite_response = client.post(
        f"/teams/{team['id']}/invite",
        headers=creator_headers,
        json={"user_id": invitee["id"], "team_name": team["name"]},
    )
    assert invite_response.status_code == 201
    invitation = invite_response.json()

    respond_response = client.post(
        f"/invitations/{invitation['id']}/respond",
        headers=invitee_headers,
        json={"accept": True},
    )
    assert respond_response.status_code == 200
    assert respond_response.json()["team_status"] == "Locked"

    teams_response = client.get(f"/circles/{circle['id']}/teams")
    assert teams_response.status_code == 200
    stored_team = teams_response.json()[0]
    assert stored_team["status"] == "Locked"
    assert stored_team["current_members"] == 2
    assert stored_team["member_ids"] == [creator["id"], invitee["id"]]

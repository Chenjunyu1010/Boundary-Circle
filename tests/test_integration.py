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


def test_full_join_circle_flow():
    creator, _ = register_and_login("flowcreator", "flowcreator@example.com")
    joiner, _ = register_and_login("flowjoiner", "flowjoiner@example.com")

    circle_response = client.post(
        f"/circles/?creator_id={creator['id']}",
        json={
            "name": "Integration Circle",
            "description": "Circle integration flow",
            "category": "Course",
        },
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    major_tag_response = client.post(
        f"/circles/{circle['id']}/tags?current_user_id={creator['id']}",
        json={"name": "Major", "data_type": "string", "required": True},
    )
    assert major_tag_response.status_code == 201
    major_tag = major_tag_response.json()

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

    submit_major_response = client.post(
        f"/circles/{circle['id']}/tags/submit?current_user_id={joiner['id']}",
        json={"tag_definition_id": major_tag['id'], "value": "CS"},
    )
    submit_role_response = client.post(
        f"/circles/{circle['id']}/tags/submit?current_user_id={joiner['id']}",
        json={"tag_definition_id": role_tag['id'], "value": "Backend"},
    )

    assert submit_major_response.status_code == 200
    assert submit_role_response.status_code == 200

    my_tags_response = client.get(
        f"/circles/{circle['id']}/tags/my?current_user_id={joiner['id']}"
    )
    assert my_tags_response.status_code == 200
    payload = my_tags_response.json()
    assert len(payload) == 2
    assert {item['value'] for item in payload} == {"CS", "Backend"}


def test_full_team_formation_flow(db_session):
    from src.models.tags import CircleMember, CircleRole

    creator, creator_headers = register_and_login("teamflowcreator", "teamflowcreator@example.com")
    invitee, invitee_headers = register_and_login("teamflowinvitee", "teamflowinvitee@example.com")

    circle_response = client.post(
        f"/circles/?creator_id={creator['id']}",
        json={
            "name": "Integration Team Circle",
            "description": "Team integration flow",
            "category": "Course",
        },
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    db_session.add(CircleMember(user_id=invitee["id"], circle_id=circle["id"], role=CircleRole.MEMBER))
    db_session.commit()

    create_team_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Integration Team",
            "description": "End-to-end team flow",
            "circle_id": circle["id"],
            "max_members": 2,
            "required_tags": ["role"],
        },
    )
    assert create_team_response.status_code == 201
    team = create_team_response.json()

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

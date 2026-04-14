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

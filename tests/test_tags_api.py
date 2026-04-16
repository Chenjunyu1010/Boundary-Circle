import pytest
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def register_and_login(
    username: str,
    email: str,
    password: str = "secret123",
) -> tuple[dict, dict]:
    register_response = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    return register_response.json(), {"Authorization": f"Bearer {token}"}


@pytest.fixture
def creator():
    return register_and_login("creator", "creator@test.com")


@pytest.fixture
def normal_user():
    return register_and_login("normal", "normal@test.com")


@pytest.fixture
def circle(creator):
    creator_user, creator_headers = creator
    response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "AI Circle", "description": "Test"},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["creator_id"] == creator_user["id"]
    return payload


def create_tag_definition(circle_id: int, headers: dict, payload: dict) -> dict:
    response = client.post(f"/circles/{circle_id}/tags", headers=headers, json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_tag_definition_requires_authentication(circle):
    response = client.post(
        f"/circles/{circle['id']}/tags",
        json={"name": "Tech Stack", "data_type": "string"},
    )
    assert response.status_code == 401


def test_create_tag_definition_rejects_spoofed_query_param_without_auth(circle, creator):
    creator_user, _ = creator
    response = client.post(
        f"/circles/{circle['id']}/tags?current_user_id={creator_user['id']}",
        json={"name": "Tech Stack", "data_type": "string"},
    )
    assert response.status_code == 401


def test_create_tag_definition_as_creator(creator, circle):
    _, creator_headers = creator
    response = client.post(
        f"/circles/{circle['id']}/tags",
        headers=creator_headers,
        json={"name": "Tech Stack", "data_type": "string"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Tech Stack"


def test_create_tag_definition_as_normal_user(normal_user, circle):
    _, normal_headers = normal_user
    response = client.post(
        f"/circles/{circle['id']}/tags",
        headers=normal_headers,
        json={"name": "Role", "data_type": "enum", "options": '["Backend"]'},
    )
    assert response.status_code == 403
    assert "Only circle creator can define tags" in response.json()["detail"]


def test_submit_user_tag_requires_authentication(circle, creator):
    _, creator_headers = creator
    tag_definition = create_tag_definition(
        circle["id"],
        creator_headers,
        {"name": "GPA", "data_type": "float"},
    )

    response = client.post(
        f"/circles/{circle['id']}/tags/submit",
        json={"tag_definition_id": tag_definition["id"], "value": "3.8"},
    )
    assert response.status_code == 401


def test_submit_user_tag_rejects_spoofed_query_param_without_auth(circle, creator, normal_user):
    _, creator_headers = creator
    normal_user_payload, _ = normal_user
    tag_definition = create_tag_definition(
        circle["id"],
        creator_headers,
        {"name": "Role", "data_type": "string"},
    )

    response = client.post(
        f"/circles/{circle['id']}/tags/submit?current_user_id={normal_user_payload['id']}",
        json={"tag_definition_id": tag_definition["id"], "value": "backend"},
    )
    assert response.status_code == 401


def test_submit_user_tag_valid(creator, normal_user, circle):
    _, creator_headers = creator
    _, normal_headers = normal_user
    tag_definition = create_tag_definition(
        circle["id"],
        creator_headers,
        {"name": "GPA", "data_type": "float"},
    )

    response = client.post(
        f"/circles/{circle['id']}/tags/submit",
        headers=normal_headers,
        json={"tag_definition_id": tag_definition["id"], "value": "3.8"},
    )
    assert response.status_code == 200
    assert response.json()["value"] == "3.8"


def test_submit_user_tag_invalid_type(creator, normal_user, circle):
    _, creator_headers = creator
    _, normal_headers = normal_user
    tag_definition = create_tag_definition(
        circle["id"],
        creator_headers,
        {"name": "Years of Exp", "data_type": "integer"},
    )

    response = client.post(
        f"/circles/{circle['id']}/tags/submit",
        headers=normal_headers,
        json={"tag_definition_id": tag_definition["id"], "value": "Two Years"},
    )
    assert response.status_code == 400
    assert "Invalid value" in response.json()["detail"]


def test_submit_user_tag_enum(creator, normal_user, circle):
    _, creator_headers = creator
    _, normal_headers = normal_user
    tag_definition = create_tag_definition(
        circle["id"],
        creator_headers,
        {"name": "Role", "data_type": "enum", "options": '["Frontend", "Backend"]'},
    )

    invalid_response = client.post(
        f"/circles/{circle['id']}/tags/submit",
        headers=normal_headers,
        json={"tag_definition_id": tag_definition["id"], "value": "Designer"},
    )
    assert invalid_response.status_code == 400

    valid_response = client.post(
        f"/circles/{circle['id']}/tags/submit",
        headers=normal_headers,
        json={"tag_definition_id": tag_definition["id"], "value": "Backend"},
    )
    assert valid_response.status_code == 200


def test_create_tag_definition_enum_invalid(creator, circle):
    _, creator_headers = creator

    missing_options = client.post(
        f"/circles/{circle['id']}/tags",
        headers=creator_headers,
        json={"name": "Role1", "data_type": "enum"},
    )
    assert missing_options.status_code == 400

    invalid_json = client.post(
        f"/circles/{circle['id']}/tags",
        headers=creator_headers,
        json={"name": "Role2", "data_type": "enum", "options": "not-a-list"},
    )
    assert invalid_json.status_code == 400


def test_create_tag_definition_single_select_valid(creator, circle):
    _, creator_headers = creator

    response = client.post(
        f"/circles/{circle['id']}/tags",
        headers=creator_headers,
        json={
            "name": "Major",
            "data_type": "single_select",
            "options": '["Artificial Intelligence", "Software Engineering"]',
        },
    )

    assert response.status_code == 201
    assert response.json()["data_type"] == "single_select"
    assert response.json()["options"] == '["Artificial Intelligence", "Software Engineering"]'


def test_create_tag_definition_multi_select_valid(creator, circle):
    _, creator_headers = creator

    response = client.post(
        f"/circles/{circle['id']}/tags",
        headers=creator_headers,
        json={
            "name": "Tech Stack",
            "data_type": "multi_select",
            "options": '["Python", "React", "SQL"]',
            "max_selections": 2,
        },
    )

    assert response.status_code == 201
    assert response.json()["data_type"] == "multi_select"
    assert response.json()["max_selections"] == 2


def test_create_tag_definition_selection_type_requires_options(creator, circle):
    _, creator_headers = creator

    single_select_response = client.post(
        f"/circles/{circle['id']}/tags",
        headers=creator_headers,
        json={"name": "Major", "data_type": "single_select"},
    )
    assert single_select_response.status_code == 400

    multi_select_response = client.post(
        f"/circles/{circle['id']}/tags",
        headers=creator_headers,
        json={"name": "Tech Stack", "data_type": "multi_select", "max_selections": 2},
    )
    assert multi_select_response.status_code == 400


def test_submit_user_tag_single_select_valid(creator, normal_user, circle):
    _, creator_headers = creator
    _, normal_headers = normal_user
    tag_definition = create_tag_definition(
        circle["id"],
        creator_headers,
        {
            "name": "Major",
            "data_type": "single_select",
            "options": '["Artificial Intelligence", "Software Engineering"]',
        },
    )

    response = client.post(
        f"/circles/{circle['id']}/tags/submit",
        headers=normal_headers,
        json={"tag_definition_id": tag_definition["id"], "value": "Artificial Intelligence"},
    )

    assert response.status_code == 200
    assert response.json()["value"] == "Artificial Intelligence"


def test_submit_user_tag_single_select_rejects_unknown_option(creator, normal_user, circle):
    _, creator_headers = creator
    _, normal_headers = normal_user
    tag_definition = create_tag_definition(
        circle["id"],
        creator_headers,
        {
            "name": "Major",
            "data_type": "single_select",
            "options": '["Artificial Intelligence", "Software Engineering"]',
        },
    )

    response = client.post(
        f"/circles/{circle['id']}/tags/submit",
        headers=normal_headers,
        json={"tag_definition_id": tag_definition["id"], "value": "Mathematics"},
    )

    assert response.status_code == 400


def test_submit_user_tag_multi_select_valid(creator, normal_user, circle):
    _, creator_headers = creator
    _, normal_headers = normal_user
    tag_definition = create_tag_definition(
        circle["id"],
        creator_headers,
        {
            "name": "Tech Stack",
            "data_type": "multi_select",
            "options": '["Python", "React", "SQL"]',
            "max_selections": 2,
        },
    )

    response = client.post(
        f"/circles/{circle['id']}/tags/submit",
        headers=normal_headers,
        json={"tag_definition_id": tag_definition["id"], "value": '["Python", "SQL"]'},
    )

    assert response.status_code == 200
    assert response.json()["value"] == '["Python", "SQL"]'


def test_submit_user_tag_multi_select_rejects_too_many_values(creator, normal_user, circle):
    _, creator_headers = creator
    _, normal_headers = normal_user
    tag_definition = create_tag_definition(
        circle["id"],
        creator_headers,
        {
            "name": "Tech Stack",
            "data_type": "multi_select",
            "options": '["Python", "React", "SQL"]',
            "max_selections": 2,
        },
    )

    response = client.post(
        f"/circles/{circle['id']}/tags/submit",
        headers=normal_headers,
        json={"tag_definition_id": tag_definition["id"], "value": '["Python", "React", "SQL"]'},
    )

    assert response.status_code == 400


def test_get_my_tags_and_delete(creator, normal_user, circle):
    _, creator_headers = creator
    _, normal_headers = normal_user
    tag_definition = create_tag_definition(
        circle["id"],
        creator_headers,
        {"name": "Test", "data_type": "string"},
    )

    submit_response = client.post(
        f"/circles/{circle['id']}/tags/submit",
        headers=normal_headers,
        json={"tag_definition_id": tag_definition["id"], "value": "my_value"},
    )
    assert submit_response.status_code == 200

    get_response = client.get(
        f"/circles/{circle['id']}/tags/my",
        headers=normal_headers,
    )
    assert get_response.status_code == 200
    assert len(get_response.json()) == 1
    user_tag_id = get_response.json()[0]["id"]

    delete_response = client.delete(f"/tags/{user_tag_id}", headers=normal_headers)
    assert delete_response.status_code == 204

    get_after_delete = client.get(
        f"/circles/{circle['id']}/tags/my",
        headers=normal_headers,
    )
    assert len(get_after_delete.json()) == 0

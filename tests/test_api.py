import pytest
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def register_and_login(
    username: str = "testuser",
    email: str = "test@example.com",
    password: str = "password123",
) -> tuple[dict, dict]:
    register_response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "full_name": "Test User",
            "password": password,
        },
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
def test_user():
    """Create a basic user via the legacy /users endpoint for list/read tests."""
    user_data = {
        "username": "plainuser",
        "email": "plain@example.com",
        "full_name": "Plain User",
        "password": "password123",
    }
    response = client.post("/users/", json=user_data)
    return response.json()


@pytest.fixture
def authenticated_user():
    """Create an authenticated user for protected route tests."""
    return register_and_login("circleowner", "circleowner@example.com")


@pytest.fixture
def test_circle(authenticated_user):
    """Create a test circle as the authenticated user."""
    user, headers = authenticated_user
    circle_data = {
        "name": "Test Circle",
        "description": "This is a test circle",
        "category": "Test",
    }
    response = client.post("/circles/", headers=headers, json=circle_data)
    assert response.status_code == 201
    payload = response.json()
    assert payload["creator_id"] == user["id"]
    return payload


def test_create_user():
    user_data = {
        "username": "newuser",
        "email": "new@example.com",
        "full_name": "New User",
        "password": "password123",
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "id" in data


def test_create_user_can_login_through_auth_flow():
    password = "password123"
    user_data = {
        "username": "legacycreate",
        "email": "legacycreate@example.com",
        "full_name": "Legacy Create",
        "password": password,
    }
    create_response = client.post("/users/", json=user_data)
    assert create_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"email": user_data["email"], "password": password},
    )

    assert login_response.status_code == 200
    token_payload = login_response.json()
    assert token_payload["token_type"] == "bearer"
    assert token_payload["access_token"]


def test_create_user_duplicate_email(test_user):
    user_data = {
        "username": "anotheruser",
        "email": test_user["email"],
        "password": "password123",
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_create_user_duplicate_username_matches_auth_register_behavior():
    first_user = {
        "username": "sharedname",
        "email": "sharedname@example.com",
        "password": "password123",
    }
    second_user = {
        "username": "sharedname",
        "email": "sharedname-2@example.com",
        "password": "password123",
    }

    first_response = client.post("/users/", json=first_user)
    assert first_response.status_code == 201

    duplicate_response = client.post("/users/", json=second_user)
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Username already taken"


def test_get_users(test_user):
    response = client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(user["username"] == "plainuser" for user in data)


def test_get_user(test_user):
    response = client.get(f"/users/{test_user['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "plainuser"


def test_get_user_not_found():
    response = client.get("/users/999")
    assert response.status_code == 404


def test_create_circle_requires_authentication():
    circle_data = {
        "name": "Secure Circle",
        "description": "Protected create",
        "category": "Course",
    }
    response = client.post("/circles/", json=circle_data)
    assert response.status_code == 401


def test_create_circle_rejects_spoofed_creator_id_without_auth():
    circle_data = {
        "name": "Spoofed Circle",
        "description": "Should not allow query-param identity",
        "category": "Course",
    }
    response = client.post("/circles/?creator_id=999", json=circle_data)
    assert response.status_code == 401


def test_create_circle_uses_authenticated_user(authenticated_user):
    user, headers = authenticated_user
    circle_data = {
        "name": "Authenticated Circle",
        "description": "Created with bearer token",
        "category": "Course",
    }
    response = client.post("/circles/", headers=headers, json=circle_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Authenticated Circle"
    assert data["creator_id"] == user["id"]
    assert data["creator_username"] == user["username"]


def test_get_circles(test_circle):
    response = client.get("/circles/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_get_circle(test_circle):
    response = client.get(f"/circles/{test_circle['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Circle"
    assert data["creator_username"] == "circleowner"


def test_get_circles_marks_creator_and_membership_state(authenticated_user):
    user, headers = authenticated_user
    circle_response = client.post(
        "/circles/",
        headers=headers,
        json={
            "name": "Membership State Circle",
            "description": "Circle for membership flags",
            "category": "Course",
        },
    )
    assert circle_response.status_code == 201

    circles_response = client.get("/circles/", headers=headers)
    assert circles_response.status_code == 200
    circle = next(
        item for item in circles_response.json() if item["name"] == "Membership State Circle"
    )
    assert circle["creator_id"] == user["id"]
    assert circle["is_creator"] is True
    assert circle["is_member"] is True


def test_get_circle_not_found():
    response = client.get("/circles/999")
    assert response.status_code == 404

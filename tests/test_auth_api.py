from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_register_login_and_get_current_user():
    register_payload = {
        "username": "authuser",
        "email": "auth@example.com",
        "full_name": "Auth User",
        "password": "secret123",
    }

    register_response = client.post("/auth/register", json=register_payload)
    assert register_response.status_code == 201
    registered_user = register_response.json()
    assert registered_user["username"] == "authuser"
    assert registered_user["email"] == "auth@example.com"
    assert "id" in registered_user

    login_response = client.post(
        "/auth/login",
        json={"email": "auth@example.com", "password": "secret123"},
    )
    assert login_response.status_code == 200
    token_payload = login_response.json()
    assert token_payload["token_type"] == "bearer"
    assert token_payload["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token_payload['access_token']}"},
    )
    assert me_response.status_code == 200
    current_user = me_response.json()
    assert current_user["username"] == "authuser"
    assert current_user["email"] == "auth@example.com"
    assert current_user["id"] == registered_user["id"]


def test_login_rejects_wrong_password():
    client.post(
        "/auth/register",
        json={
            "username": "wrongpass",
            "email": "wrongpass@example.com",
            "password": "secret123",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "wrongpass@example.com", "password": "not-the-right-password"},
    )

    assert login_response.status_code == 401
    assert login_response.json()["detail"] == "Invalid email or password"


def test_login_accepts_frontend_username_field_for_email_identifier():
    client.post(
        "/auth/register",
        json={
            "username": "frontendauth",
            "email": "frontendauth@example.com",
            "password": "secret123",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={"username": "frontendauth@example.com", "password": "secret123"},
    )

    assert login_response.status_code == 200
    token_payload = login_response.json()
    assert token_payload["token_type"] == "bearer"
    assert token_payload["access_token"]


def test_register_rejects_duplicate_email():
    payload = {
        "username": "duplicate",
        "email": "duplicate@example.com",
        "password": "secret123",
    }

    first_response = client.post("/auth/register", json=payload)
    assert first_response.status_code == 201

    duplicate_response = client.post(
        "/auth/register",
        json={**payload, "username": "duplicate-2"},
    )

    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Email already registered"


def test_protected_route_rejects_invalid_token():
    me_response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer definitely-not-a-valid-token"},
    )

    assert me_response.status_code == 401
    assert me_response.json()["detail"] == "Invalid authentication credentials"

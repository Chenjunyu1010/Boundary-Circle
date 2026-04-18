from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def register_and_login(username: str, email: str) -> tuple[dict, dict[str, str]]:
    register_response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "secret123",
            "full_name": f"{username} full name",
        },
    )
    assert register_response.status_code == 201
    user = register_response.json()

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": "secret123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return user, {"Authorization": f"Bearer {token}"}


def test_get_my_profile_returns_defaults_without_profile_row():
    user, headers = register_and_login("profile_default", "profile_default@example.com")

    response = client.get("/profile/me", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "id": user["id"],
        "username": "profile_default",
        "email": "profile_default@example.com",
        "full_name": "profile_default full name",
        "gender": None,
        "birthday": None,
        "bio": None,
        "profile_prompt_dismissed": False,
        "show_full_name": True,
        "show_gender": True,
        "show_birthday": True,
        "show_email": True,
        "show_bio": True,
    }


def test_put_my_profile_creates_and_updates_profile():
    _, headers = register_and_login("profile_update", "profile_update@example.com")

    update_response = client.put(
        "/profile/me",
        headers=headers,
        json={
            "full_name": "Updated Name",
            "gender": "Female",
            "birthday": "2003-09-15",
            "bio": "Enjoys badminton and backend work.",
            "show_full_name": False,
            "show_gender": True,
            "show_birthday": False,
            "show_email": False,
            "show_bio": True,
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["full_name"] == "Updated Name"
    assert updated["gender"] == "Female"
    assert updated["birthday"] == "2003-09-15"
    assert updated["bio"] == "Enjoys badminton and backend work."
    assert updated["show_full_name"] is False
    assert updated["show_birthday"] is False
    assert updated["show_email"] is False

    me_response = client.get("/profile/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json() == updated


def test_public_profile_hides_fields_marked_private():
    user, owner_headers = register_and_login("profile_public", "profile_public@example.com")
    _, viewer_headers = register_and_login("profile_viewer", "profile_viewer@example.com")

    update_response = client.put(
        "/profile/me",
        headers=owner_headers,
        json={
            "full_name": "Visible Name",
            "gender": "Male",
            "birthday": "2002-01-02",
            "bio": "Public bio",
            "show_full_name": True,
            "show_gender": False,
            "show_birthday": False,
            "show_email": False,
            "show_bio": True,
        },
    )
    assert update_response.status_code == 200

    public_response = client.get(f"/users/{user['id']}/profile", headers=viewer_headers)

    assert public_response.status_code == 200
    assert public_response.json() == {
        "id": user["id"],
        "username": "profile_public",
        "full_name": "Visible Name",
        "gender": None,
        "birthday": None,
        "email": None,
        "bio": "Public bio",
    }


def test_profile_update_rejects_invalid_values():
    _, headers = register_and_login("profile_invalid", "profile_invalid@example.com")

    invalid_gender = client.put(
        "/profile/me",
        headers=headers,
        json={"gender": "Apache Helicopter"},
    )
    assert invalid_gender.status_code == 400
    assert invalid_gender.json()["detail"] == "Invalid gender value"

    invalid_birthday = client.put(
        "/profile/me",
        headers=headers,
        json={"birthday": "not-a-date"},
    )
    assert invalid_birthday.status_code == 400
    assert invalid_birthday.json()["detail"] == "Invalid birthday format"

    invalid_bio = client.put(
        "/profile/me",
        headers=headers,
        json={"bio": "x" * 301},
    )
    assert invalid_bio.status_code == 400
    assert invalid_bio.json()["detail"] == "Bio must be at most 300 characters"


def test_profile_prompt_can_be_dismissed():
    _, headers = register_and_login("profile_skip", "profile_skip@example.com")

    dismiss_response = client.post("/profile/me/dismiss-prompt", headers=headers)

    assert dismiss_response.status_code == 200
    payload = dismiss_response.json()
    assert payload["profile_prompt_dismissed"] is True

    me_response = client.get("/profile/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["profile_prompt_dismissed"] is True

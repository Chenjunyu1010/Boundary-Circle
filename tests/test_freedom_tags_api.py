from fastapi.testclient import TestClient

from src.main import app
from src.models.tags import CircleMember, CircleRole
from src.services.extraction import FreedomProfileExtractor


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


def test_circle_member_can_save_freedom_tag_text():
    """A circle member can save freedom_tag_text via PUT /circles/{circle_id}/profile."""
    user, user_headers = register_and_login("freedomuser", "freedomuser@example.com")
    circle_response = client.post(
        "/circles/",
        headers=user_headers,
        json={"name": "Freedom Tag Circle", "description": "Circle for freedom tags"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    # Save freedom_tag_text (creator is already a member)
    profile_response = client.put(
        f"/circles/{circle['id']}/profile",
        headers=user_headers,
        json={
            "freedom_tag_text": "I am a freedom-loving developer interested in AI and open source.",
        },
    )
    assert profile_response.status_code == 200
    payload = profile_response.json()
    assert payload["freedom_tag_text"] == "I am a freedom-loving developer interested in AI and open source."
    assert "freedom_tag_profile" in payload
    assert isinstance(payload["freedom_tag_profile"], dict)
    # Keywords may be empty in current no-provider setup
    assert "keywords" in payload["freedom_tag_profile"]


def test_non_circle_member_gets_403_on_freedom_profile_endpoint():
    """Non-circle members receive 403 Forbidden on PUT /circles/{circle_id}/profile."""
    user, user_headers = register_and_login("outsider", "outsider@example.com")
    creator, creator_headers = register_and_login("circlecreator", "circlecreator@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Private Freedom Circle", "description": "Private circle"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    # outsider is not a member, should get 403
    profile_response = client.put(
        f"/circles/{circle['id']}/profile",
        headers=user_headers,
        json={
            "freedom_tag_text": "This should fail",
        },
    )
    assert profile_response.status_code == 403
    assert "User must join the circle first" in profile_response.json()["detail"]


def test_circle_member_can_read_saved_freedom_tag_text():
    """A circle member can read the current saved freedom tag profile via GET /circles/{circle_id}/profile."""
    user, user_headers = register_and_login("freedomreader", "freedomreader@example.com")
    circle_response = client.post(
        "/circles/",
        headers=user_headers,
        json={"name": "Freedom Read Circle", "description": "Circle for reading freedom tags"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    save_response = client.put(
        f"/circles/{circle['id']}/profile",
        headers=user_headers,
        json={"freedom_tag_text": "Python FastAPI Docker"},
    )
    assert save_response.status_code == 200

    read_response = client.get(
        f"/circles/{circle['id']}/profile",
        headers=user_headers,
    )
    assert read_response.status_code == 200
    payload = read_response.json()
    assert payload["freedom_tag_text"] == "Python FastAPI Docker"
    assert "freedom_tag_profile" in payload
    assert isinstance(payload["freedom_tag_profile"], dict)


def test_non_circle_member_gets_403_on_reading_freedom_profile():
    """Non-circle members receive 403 Forbidden on GET /circles/{circle_id}/profile."""
    user, user_headers = register_and_login("readoutsider", "readoutsider@example.com")
    creator, creator_headers = register_and_login("readcreator", "readcreator@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Read Private Circle", "description": "Private circle for read test"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    read_response = client.get(
        f"/circles/{circle['id']}/profile",
        headers=user_headers,
    )
    assert read_response.status_code == 403
    assert "User must join the circle first" in read_response.json()["detail"]


def test_create_team_with_freedom_requirement_text():
    """POST /teams accepts freedom_requirement_text and includes it in response."""
    creator, creator_headers = register_and_login("teamcreator", "teamcreator@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Freedom Team Circle", "description": "Circle for team freedom tests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    create_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Freedom Team",
            "description": "Team with freedom requirement",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
            "freedom_requirement_text": "Team members should value freedom and privacy.",
        },
    )
    assert create_response.status_code == 201
    payload = create_response.json()
    assert payload["freedom_requirement_text"] == "Team members should value freedom and privacy."
    assert "freedom_requirement_profile_keywords" in payload
    assert isinstance(payload["freedom_requirement_profile_keywords"], list)


def test_create_team_with_blank_freedom_requirement_text_succeeds():
    """Creating a team with blank freedom_requirement_text still succeeds."""
    creator, creator_headers = register_and_login("blankcreator", "blankcreator@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Blank Freedom Circle", "description": "Circle for blank freedom tests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    create_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Blank Freedom Team",
            "description": "Team with empty freedom requirement",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
            "freedom_requirement_text": "",
        },
    )
    assert create_response.status_code == 201
    payload = create_response.json()
    assert payload["freedom_requirement_text"] == ""
    assert "freedom_requirement_profile_keywords" in payload


class _FixedKeywordExtractor(FreedomProfileExtractor):
    """Deterministic extractor used to test configured provider paths."""

    def __init__(self, keywords: list[str]):
        self._keywords = keywords

    def extract_keywords(self, text: str) -> dict[str, list[str]]:
        return {"keywords": self._keywords}


def test_circle_member_save_uses_configured_extractor_keywords(monkeypatch):
    """Configured extractor keywords should be returned from the circle profile save path."""
    from src.api import circles as circles_api

    monkeypatch.setattr(
        circles_api,
        "build_freedom_profile_extractor",
        lambda: _FixedKeywordExtractor(["python", "fastapi"]),
    )

    user, user_headers = register_and_login("provideruser", "provideruser@example.com")
    circle_response = client.post(
        "/circles/",
        headers=user_headers,
        json={"name": "Provider Freedom Circle", "description": "Circle for provider test"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    profile_response = client.put(
        f"/circles/{circle['id']}/profile",
        headers=user_headers,
        json={"freedom_tag_text": "I build Python APIs with FastAPI."},
    )
    assert profile_response.status_code == 200

    payload = profile_response.json()
    assert payload["freedom_tag_profile"] == {"keywords": ["python", "fastapi"]}


def test_create_team_uses_configured_extractor_keywords(monkeypatch):
    """Configured extractor keywords should be included in the team create response."""
    from src.api import teams as teams_api

    monkeypatch.setattr(
        teams_api,
        "build_freedom_profile_extractor",
        lambda: _FixedKeywordExtractor(["privacy", "security"]),
    )

    creator, creator_headers = register_and_login("providerteamcreator", "providerteamcreator@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Provider Team Circle", "description": "Circle for provider team tests"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    create_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Provider Team",
            "description": "Team with provider extraction",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
            "freedom_requirement_text": "Looking for teammates who care about privacy and security.",
        },
    )
    assert create_response.status_code == 201

    payload = create_response.json()
    assert payload["freedom_requirement_profile_keywords"] == ["privacy", "security"]


def test_circle_profile_rejects_overlong_freedom_tag_text():
    """Circle freedom profile input should reject oversized payloads before LLM extraction."""
    user, user_headers = register_and_login("longprofile", "longprofile@example.com")
    circle_response = client.post(
        "/circles/",
        headers=user_headers,
        json={"name": "Long Freedom Circle", "description": "Circle for length validation"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    profile_response = client.put(
        f"/circles/{circle['id']}/profile",
        headers=user_headers,
        json={"freedom_tag_text": "x" * 2001},
    )

    assert profile_response.status_code == 422


def test_create_team_rejects_overlong_freedom_requirement_text():
    """Team freedom requirement input should reject oversized payloads before LLM extraction."""
    creator, creator_headers = register_and_login("longteamcreator", "longteamcreator@example.com")
    circle_response = client.post(
        "/circles/",
        headers=creator_headers,
        json={"name": "Long Team Circle", "description": "Circle for team length validation"},
    )
    assert circle_response.status_code == 201
    circle = circle_response.json()

    create_response = client.post(
        "/teams",
        headers=creator_headers,
        json={
            "name": "Long Freedom Team",
            "description": "Team with oversized freedom requirement",
            "circle_id": circle["id"],
            "max_members": 3,
            "required_tags": [],
            "freedom_requirement_text": "x" * 2001,
        },
    )

    assert create_response.status_code == 422

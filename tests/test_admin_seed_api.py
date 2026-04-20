from fastapi.testclient import TestClient
from sqlmodel import select

from src.core.settings import get_settings
from src.main import app
from src.models.core import Circle, User
from src.models.teams import Team


client = TestClient(app)


def count_seed_users(dataset: str) -> int:
    from tests.conftest import engine
    from sqlmodel import Session

    with Session(engine) as session:
        return len(
            [
                user
                for user in session.exec(select(User)).all()
                if user.username.startswith(f"seed_{dataset}_")
            ]
        )


def count_seed_circles(dataset: str) -> int:
    from tests.conftest import engine
    from sqlmodel import Session

    with Session(engine) as session:
        return len(
            [
                circle
                for circle in session.exec(select(Circle)).all()
                if circle.name.startswith(f"[SEED {dataset.upper()}] ")
            ]
        )


def count_seed_teams(dataset: str) -> int:
    from tests.conftest import engine
    from sqlmodel import Session

    with Session(engine) as session:
        return len(
            [
                team
                for team in session.exec(select(Team)).all()
                if team.name.startswith(f"[SEED {dataset.upper()}] ")
            ]
        )


def test_admin_seed_requires_valid_admin_key(monkeypatch):
    monkeypatch.setenv("ADMIN_SEED_KEY", "secret-key")
    get_settings.cache_clear()

    response = client.post("/admin/seed?dataset=stress")

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid admin key"


def test_admin_seed_returns_503_when_admin_key_not_configured(monkeypatch):
    monkeypatch.delenv("ADMIN_SEED_KEY", raising=False)
    get_settings.cache_clear()

    response = client.post(
        "/admin/seed?dataset=stress",
        headers={"X-Admin-Key": "secret-key"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Admin seed API is not configured"


def test_admin_seed_stress_import_matches_existing_stress_shape(monkeypatch):
    monkeypatch.setenv("ADMIN_SEED_KEY", "secret-key")
    get_settings.cache_clear()

    response = client.post(
        "/admin/seed?dataset=stress",
        headers={"X-Admin-Key": "secret-key"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "seed"
    assert payload["dataset"] == "stress"
    assert payload["summary"]["users"] == 48
    assert payload["summary"]["circles"] == 8
    assert payload["summary"]["teams"] == 32
    assert payload["summary"]["invitations"] >= 32
    assert count_seed_users("stress") == 48
    assert count_seed_circles("stress") == 8
    assert count_seed_teams("stress") == 32


def test_admin_seed_stress_is_repeatable_without_duplication(monkeypatch):
    monkeypatch.setenv("ADMIN_SEED_KEY", "secret-key")
    get_settings.cache_clear()

    first_response = client.post(
        "/admin/seed?dataset=stress",
        headers={"X-Admin-Key": "secret-key"},
    )
    second_response = client.post(
        "/admin/seed?dataset=stress",
        headers={"X-Admin-Key": "secret-key"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert count_seed_users("stress") == 48
    assert count_seed_circles("stress") == 8
    assert count_seed_teams("stress") == 32


def test_admin_seed_reset_removes_stress_dataset(monkeypatch):
    monkeypatch.setenv("ADMIN_SEED_KEY", "secret-key")
    get_settings.cache_clear()

    seed_response = client.post(
        "/admin/seed?dataset=stress",
        headers={"X-Admin-Key": "secret-key"},
    )
    reset_response = client.post(
        "/admin/seed/reset?dataset=stress",
        headers={"X-Admin-Key": "secret-key"},
    )

    assert seed_response.status_code == 200
    assert reset_response.status_code == 200
    assert reset_response.json()["action"] == "reset"
    assert reset_response.json()["dataset"] == "stress"
    assert count_seed_users("stress") == 0
    assert count_seed_circles("stress") == 0
    assert count_seed_teams("stress") == 0

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class SessionState(dict):
    def __getattr__(self, item: str):
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc

    def __setattr__(self, key: str, value):
        self[key] = value


def load_frontend_modules(monkeypatch, mock_mode: str = "true"):
    for name in [
        "frontend.utils.api",
        "frontend.utils.auth",
        "frontend.utils.validation",
        "streamlit",
    ]:
        sys.modules.pop(name, None)

    fake_streamlit = ModuleType("streamlit")
    fake_streamlit.session_state = SessionState()
    fake_streamlit.warning = lambda *args, **kwargs: None
    fake_streamlit.stop = lambda: None
    fake_streamlit.toast = lambda *args, **kwargs: None
    fake_streamlit.success = lambda *args, **kwargs: None
    fake_streamlit.error = lambda *args, **kwargs: None
    fake_streamlit.info = lambda *args, **kwargs: None
    fake_streamlit.balloons = lambda *args, **kwargs: None
    fake_streamlit.rerun = lambda: None

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setenv("MOCK_MODE", mock_mode)
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:8000")

    api_module = importlib.import_module("frontend.utils.api")
    auth_module = importlib.import_module("frontend.utils.auth")
    validation_module = importlib.import_module("frontend.utils.validation")
    return fake_streamlit, api_module, auth_module, validation_module


def load_circle_detail_module(monkeypatch):
    fake_streamlit, _, _, _ = load_frontend_modules(monkeypatch)
    fake_streamlit.query_params = {}
    frontend_root = ROOT / "frontend"
    if str(frontend_root) not in sys.path:
        sys.path.insert(0, str(frontend_root))

    for name in [
        "frontend.views.circle_detail",
        "utils.api",
        "utils.auth",
    ]:
        sys.modules.pop(name, None)

    return fake_streamlit, importlib.import_module("frontend.views.circle_detail")


def test_api_client_login_mock_mode_response_matches_auth_contract(monkeypatch):
    fake_streamlit, api_module, _, _ = load_frontend_modules(monkeypatch)
    fake_streamlit.session_state.access_token = "token-123"

    client = api_module.APIClient()
    headers = client._get_headers()
    response = client.post(
        "/auth/login",
        data={"username": "alice@example.com", "password": "secret123"},
    )

    assert headers["Authorization"] == "Bearer token-123"
    assert response.status_code == 200
    assert response.json() == {
        "access_token": "mock_token_alice@example.com",
        "token_type": "bearer",
        "user": {
            "id": 1,
            "username": "alice",
            "email": "alice@example.com",
        },
    }


def test_auth_register_and_login_valid_credentials_update_session_state(monkeypatch):
    fake_streamlit, _, auth_module, _ = load_frontend_modules(monkeypatch)

    auth_module.init_session_state()

    registered, register_message = auth_module.register(
        username="alice",
        email="alice@example.com",
        password="secret123",
    )
    logged_in, login_message = auth_module.login(
        email="alice@example.com",
        password="secret123",
    )

    assert registered is True
    assert register_message == "Registration successful! Please login."
    assert logged_in is True
    assert login_message == "Login successful!"
    assert fake_streamlit.session_state.logged_in is True
    assert fake_streamlit.session_state.access_token == "mock_token_alice@example.com"
    assert fake_streamlit.session_state.user_id == 1
    assert fake_streamlit.session_state.username == "alice"
    assert fake_streamlit.session_state.email == "alice@example.com"


def test_auth_logout_when_called_clears_authentication_state(monkeypatch):
    fake_streamlit, _, auth_module, _ = load_frontend_modules(monkeypatch)

    auth_module.init_session_state()
    fake_streamlit.session_state.logged_in = True
    fake_streamlit.session_state.access_token = "token-123"
    fake_streamlit.session_state.user_id = 5
    fake_streamlit.session_state.username = "alice"
    fake_streamlit.session_state.email = "alice@example.com"

    auth_module.logout()

    assert auth_module.is_authenticated() is False
    assert fake_streamlit.session_state.access_token is None
    assert fake_streamlit.session_state.user_id is None
    assert fake_streamlit.session_state.username is None
    assert fake_streamlit.session_state.email is None


def test_validation_helpers_reject_invalid_inputs(monkeypatch):
    _, _, _, validation_module = load_frontend_modules(monkeypatch)

    assert validation_module.validate_email("bad-email") == (
        False,
        "Please enter a valid email address",
    )
    assert validation_module.validate_password("short") == (
        False,
        "Password must be at least 6 characters",
    )
    assert validation_module.validate_username("ab!") == (
        False,
        "Username can only contain letters, numbers and underscores",
    )


def test_login_fails_when_real_mode_cannot_load_user_profile(monkeypatch):
    fake_streamlit, _, auth_module, _ = load_frontend_modules(
        monkeypatch,
        mock_mode="false",
    )

    auth_module.init_session_state()

    class Response:
        def __init__(self, payload: dict, ok: bool = True, reason: str = "OK"):
            self._payload = payload
            self.ok = ok
            self.reason = reason

        def json(self):
            return self._payload

    monkeypatch.setattr(
        auth_module.api_client,
        "post",
        lambda endpoint, data=None: Response({"access_token": "real-token"}),
    )
    monkeypatch.setattr(
        auth_module.api_client,
        "get",
        lambda endpoint, params=None: Response({}, ok=False, reason="Unauthorized"),
    )

    logged_in, message = auth_module.login(
        email="alice@example.com",
        password="secret123",
    )

    assert logged_in is False
    assert message == "Login failed: unable to load user profile."
    assert fake_streamlit.session_state.logged_in is False
    assert fake_streamlit.session_state.access_token is None


def test_circle_detail_normalize_tag_definition_preserves_selection_metadata(monkeypatch):
    _, circle_detail_module = load_circle_detail_module(monkeypatch)

    normalized = circle_detail_module.normalize_tag_definition(
        {
            "id": 7,
            "name": "Tech Stack",
            "data_type": "multi_select",
            "required": True,
            "options": '["Python", "React", "SQL"]',
            "max_selections": 2,
        }
    )

    assert normalized["data_type"] == "multi_select"
    assert normalized["options"] == ["Python", "React", "SQL"]
    assert normalized["max_selections"] == 2


def test_circle_detail_validate_tag_input_rejects_multi_select_over_limit(monkeypatch):
    _, circle_detail_module = load_circle_detail_module(monkeypatch)

    normalized = circle_detail_module.normalize_tag_definition(
        {
            "id": 7,
            "name": "Tech Stack",
            "data_type": "multi_select",
            "required": True,
            "options": '["Python", "React", "SQL"]',
            "max_selections": 2,
        }
    )

    is_valid, error_message = circle_detail_module.validate_tag_input(
        normalized,
        ["Python", "React", "SQL"],
    )

    assert is_valid is False
    assert error_message == "Tech Stack allows at most 2 selections."


def test_circle_detail_clear_admin_tag_form_state_removes_widget_values(monkeypatch):
    fake_streamlit, circle_detail_module = load_circle_detail_module(monkeypatch)

    fake_streamlit.session_state["admin_tag_name_5"] = "Major"
    fake_streamlit.session_state["admin_tag_type_5"] = "single_select"
    fake_streamlit.session_state["admin_tag_required_5"] = True
    fake_streamlit.session_state["admin_tag_options_5"] = '["AI", "SE"]'
    fake_streamlit.session_state["admin_tag_max_selections_5"] = 2

    circle_detail_module.clear_admin_tag_form_state(5)

    assert "admin_tag_name_5" not in fake_streamlit.session_state
    assert "admin_tag_type_5" not in fake_streamlit.session_state
    assert "admin_tag_required_5" not in fake_streamlit.session_state
    assert "admin_tag_options_5" not in fake_streamlit.session_state
    assert "admin_tag_max_selections_5" not in fake_streamlit.session_state


def test_circle_detail_delete_tag_definition_uses_expected_endpoint(monkeypatch):
    _, circle_detail_module = load_circle_detail_module(monkeypatch)

    class Response:
        ok = True
        reason = "OK"

    captured = {}

    def fake_delete(endpoint, params=None):
        captured["endpoint"] = endpoint
        captured["params"] = params
        return Response()

    monkeypatch.setattr(circle_detail_module.api_client, "delete", fake_delete)

    success, message = circle_detail_module.delete_tag_definition(17)

    assert success is True
    assert message == "Tag definition deleted successfully."
    assert captured == {
        "endpoint": "/tags/definitions/17",
        "params": None,
    }

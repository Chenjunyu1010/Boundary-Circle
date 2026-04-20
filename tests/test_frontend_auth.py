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
        "frontend.navigation",
        "navigation",
        "streamlit",
        "streamlit.components",
        "streamlit.components.v1",
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
    fake_streamlit.switch_page = lambda *args, **kwargs: None
    fake_streamlit.context = ModuleType("context")
    fake_streamlit.context.cookies = {}
    fake_streamlit.markdown = lambda *args, **kwargs: None

    components_module = ModuleType("streamlit.components")
    components_v1_module = ModuleType("streamlit.components.v1")
    components_v1_module.html = lambda *args, **kwargs: None
    components_module.v1 = components_v1_module
    fake_streamlit.components = components_module

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "streamlit.components", components_module)
    monkeypatch.setitem(sys.modules, "streamlit.components.v1", components_v1_module)
    monkeypatch.setenv("MOCK_MODE", mock_mode)
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:8000")

    api_module = importlib.import_module("frontend.utils.api")
    auth_module = importlib.import_module("frontend.utils.auth")
    validation_module = importlib.import_module("frontend.utils.validation")
    return fake_streamlit, api_module, auth_module, validation_module


def test_api_client_reads_streamlit_secrets_when_env_missing(monkeypatch):
    for name in [
        "frontend.utils.api",
        "streamlit",
    ]:
        sys.modules.pop(name, None)

    monkeypatch.delenv("API_BASE_URL", raising=False)
    monkeypatch.delenv("MOCK_MODE", raising=False)

    fake_streamlit = ModuleType("streamlit")
    fake_streamlit.session_state = SessionState()
    fake_streamlit.secrets = {
        "API_BASE_URL": "https://backend.example.com",
        "MOCK_MODE": "false",
    }
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    api_module = importlib.import_module("frontend.utils.api")
    client = api_module.APIClient()

    assert client.base_url == "https://backend.example.com"
    assert client.mock_mode is False


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
        "frontend.utils.ui",
        "utils.ui",
    ]:
        sys.modules.pop(name, None)

    return fake_streamlit, importlib.import_module("frontend.views.circle_detail")


def load_auth_page_module(monkeypatch):
    fake_streamlit, _, _, _ = load_frontend_modules(monkeypatch)
    fake_streamlit.set_page_config = lambda *args, **kwargs: None
    fake_streamlit.title = lambda *args, **kwargs: None
    fake_streamlit.markdown = lambda *args, **kwargs: None
    fake_streamlit.caption = lambda *args, **kwargs: None
    fake_streamlit.tabs = lambda labels: [object() for _ in labels]

    class DummyContext:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    fake_streamlit.form = lambda *args, **kwargs: DummyContext()
    fake_streamlit.spinner = lambda *args, **kwargs: DummyContext()
    fake_streamlit.text_input = lambda *args, **kwargs: ""
    fake_streamlit.form_submit_button = lambda *args, **kwargs: False
    fake_streamlit.page_link = lambda *args, **kwargs: None

    frontend_root = ROOT / "frontend"
    if str(frontend_root) not in sys.path:
        sys.path.insert(0, str(frontend_root))

    for name in [
        "frontend.pages.auth",
        "utils.auth",
        "utils.validation",
        "frontend.utils.ui",
        "utils.ui",
    ]:
        sys.modules.pop(name, None)

    return fake_streamlit, importlib.import_module("frontend.pages.auth")


def load_profile_page_module(monkeypatch):
    fake_streamlit, _, _, _ = load_frontend_modules(monkeypatch)
    frontend_root = ROOT / "frontend"
    if str(frontend_root) not in sys.path:
        sys.path.insert(0, str(frontend_root))

    for name in [
        "frontend.pages.profile",
        "utils.api",
        "utils.auth",
        "frontend.utils.ui",
        "utils.ui",
    ]:
        sys.modules.pop(name, None)

    return fake_streamlit, importlib.import_module("frontend.pages.profile")


def load_public_profile_page_module(monkeypatch):
    fake_streamlit, _, _, _ = load_frontend_modules(monkeypatch)
    fake_streamlit.query_params = {}
    fake_streamlit.set_page_config = lambda *args, **kwargs: None
    fake_streamlit.title = lambda *args, **kwargs: None
    fake_streamlit.caption = lambda *args, **kwargs: None
    fake_streamlit.error = lambda *args, **kwargs: None
    fake_streamlit.info = lambda *args, **kwargs: None
    fake_streamlit.write = lambda *args, **kwargs: None
    fake_streamlit.markdown = lambda *args, **kwargs: None
    fake_streamlit.page_link = lambda *args, **kwargs: None

    class DummyContext:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    fake_streamlit.container = lambda *args, **kwargs: DummyContext()

    frontend_root = ROOT / "frontend"
    if str(frontend_root) not in sys.path:
        sys.path.insert(0, str(frontend_root))

    for name in [
        "frontend.pages.public_profile",
        "utils.api",
        "utils.auth",
    ]:
        sys.modules.pop(name, None)

    return fake_streamlit, importlib.import_module("frontend.pages.public_profile")


def load_home_module(monkeypatch):
    fake_streamlit, _, _, _ = load_frontend_modules(monkeypatch)
    fake_streamlit.set_page_config = lambda *args, **kwargs: None
    fake_streamlit.title = lambda *args, **kwargs: None
    fake_streamlit.markdown = lambda *args, **kwargs: None
    fake_streamlit.success = lambda *args, **kwargs: None
    fake_streamlit.warning = lambda *args, **kwargs: None
    fake_streamlit.info = lambda *args, **kwargs: None
    fake_streamlit.write = lambda *args, **kwargs: None
    fake_streamlit.page_link = lambda *args, **kwargs: None
    fake_streamlit.button = lambda *args, **kwargs: False
    fake_streamlit.columns = lambda count: [fake_streamlit for _ in range(count)]

    frontend_root = ROOT / "frontend"
    if str(frontend_root) not in sys.path:
        sys.path.insert(0, str(frontend_root))

    for name in [
        "frontend.Home",
        "utils.api",
        "utils.auth",
        "frontend.utils.ui",
        "utils.ui",
    ]:
        sys.modules.pop(name, None)

    return fake_streamlit, importlib.import_module("frontend.Home")


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


def test_ui_password_css_hides_browser_native_reveal_controls(monkeypatch):
    load_frontend_modules(monkeypatch)
    sys.modules.pop("frontend.utils.ui", None)
    ui_module = importlib.import_module("frontend.utils.ui")

    css = ui_module.build_button_usability_css()
    password_rule = """
        input[type="password"]::-ms-reveal,
        input[type="password"]::-ms-clear {
            display: none;
        }
"""

    assert 'input[type="password"]::-ms-reveal' in css
    assert 'input[type="password"]::-ms-clear' in css
    assert password_rule in css


def test_ui_button_css_uses_streamlit_theme_tokens_for_light_and_dark_modes(monkeypatch):
    load_frontend_modules(monkeypatch)
    sys.modules.pop("frontend.utils.ui", None)
    ui_module = importlib.import_module("frontend.utils.ui")

    css = ui_module.build_button_usability_css()

    assert "min-height: 2.75rem;" in css
    assert "padding: 0.45rem 1rem;" in css
    assert "--bc-button-primary-bg: #2563eb;" in css
    assert "--bc-button-danger-bg: #dc2626;" in css
    assert "--bc-button-neutral-border:" in css
    assert "background: var(--bc-button-neutral-bg);" in css
    assert "border: 1px solid var(--bc-button-neutral-border) !important;" in css
    assert '[data-testid="stPageLink"] a' in css
    assert "background: var(--bc-button-primary-bg) !important;" in css
    assert "color: var(--bc-button-primary-text) !important;" in css
    assert 'button[kind="primary"]' in css
    assert 'button[role="tab"]' in css
    assert 'button[role="tab"][aria-selected="true"]' in css
    assert '[data-testid="stPageLink"] a {' in css
    assert "currentColor 18%" not in css


def test_ui_button_variant_marker_renders_danger_hook(monkeypatch):
    fake_streamlit, _, _, _ = load_frontend_modules(monkeypatch)
    calls: list[tuple[str, bool]] = []

    def fake_markdown(content, unsafe_allow_html=False, **kwargs):
        calls.append((content, unsafe_allow_html))

    fake_streamlit.markdown = fake_markdown
    sys.modules.pop("frontend.utils.ui", None)
    ui_module = importlib.import_module("frontend.utils.ui")

    ui_module.render_button_variant_marker("danger")

    assert calls == [
        ('<div class="bc-button-marker" data-variant="danger"></div>', True)
    ]


def test_profile_page_day_options_follow_month_and_leap_year(monkeypatch):
    load_frontend_modules(monkeypatch)
    sys.modules.pop("frontend.pages.profile", None)
    profile_page_module = importlib.import_module("frontend.pages.profile")

    assert profile_page_module.get_birthday_day_options(2001, 2) == [None, *list(range(1, 29))]
    assert profile_page_module.get_birthday_day_options(2000, 2) == [None, *list(range(1, 30))]
    assert profile_page_module.get_birthday_day_options(2001, 4) == [None, *list(range(1, 31))]
    assert profile_page_module.get_birthday_day_options(None, None) == [None, *list(range(1, 32))]


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


def test_auth_init_session_state_restores_user_from_persisted_token(monkeypatch):
    fake_streamlit, _, auth_module, _ = load_frontend_modules(
        monkeypatch,
        mock_mode="false",
    )
    fake_streamlit.context.cookies["boundary_circle_access_token"] = "persisted-token"

    class Response:
        def __init__(self, payload: dict, ok: bool = True):
            self._payload = payload
            self.ok = ok
            self.reason = "OK" if ok else "Unauthorized"

        def json(self):
            return self._payload

    def fake_get(endpoint, params=None):
        if endpoint == "/auth/me":
            return Response(
                {
                    "id": 11,
                    "username": "alice",
                    "email": "alice@example.com",
                    "full_name": "Alice Chen",
                }
            )
        if endpoint == "/profile/me":
            return Response(
                {
                    "id": 11,
                    "username": "alice",
                    "email": "alice@example.com",
                    "full_name": "Alice Chen",
                    "gender": "Female",
                    "birthday": None,
                    "bio": "SE student",
                    "profile_prompt_dismissed": True,
                }
            )
        raise AssertionError(endpoint)

    monkeypatch.setattr(auth_module.api_client, "get", fake_get)

    auth_module.init_session_state()

    assert fake_streamlit.session_state.logged_in is True
    assert fake_streamlit.session_state.access_token == "persisted-token"
    assert fake_streamlit.session_state.user_id == 11
    assert fake_streamlit.session_state.username == "alice"
    assert fake_streamlit.session_state.email == "alice@example.com"


def test_auth_init_session_state_clears_invalid_persisted_token(monkeypatch):
    fake_streamlit, _, auth_module, _ = load_frontend_modules(
        monkeypatch,
        mock_mode="false",
    )
    cookie_calls = []
    fake_streamlit.context.cookies["boundary_circle_access_token"] = "stale-token"

    class Response:
        def __init__(self, payload: dict, ok: bool = True, reason: str = "OK", status_code: int = 200):
            self._payload = payload
            self.ok = ok
            self.reason = reason
            self.status_code = status_code

        def json(self):
            return self._payload

    def fake_get(endpoint, params=None):
        if endpoint == "/auth/me":
            return Response({}, ok=False, reason="Unauthorized", status_code=401)
        if endpoint == "/profile/me":
            raise AssertionError("/profile/me should not be called after auth rejection")
        raise AssertionError(endpoint)

    monkeypatch.setattr(auth_module.api_client, "get", fake_get)
    monkeypatch.setattr(auth_module, "_sync_auth_cookie", lambda access_token: cookie_calls.append(access_token))

    auth_module.init_session_state()

    assert auth_module.is_authenticated() is False
    assert fake_streamlit.session_state.logged_in is False
    assert fake_streamlit.session_state.access_token is None
    assert fake_streamlit.session_state.user_id is None
    assert fake_streamlit.session_state.username is None
    assert fake_streamlit.session_state.email is None
    assert cookie_calls == [None]


def test_auth_init_session_state_preserves_persisted_token_on_transient_failure(monkeypatch):
    fake_streamlit, _, auth_module, _ = load_frontend_modules(
        monkeypatch,
        mock_mode="false",
    )
    cookie_calls = []
    fake_streamlit.context.cookies["boundary_circle_access_token"] = "persisted-token"

    def fake_get(endpoint, params=None):
        if endpoint == "/auth/me":
            raise RuntimeError("temporary network error")
        raise AssertionError(endpoint)

    monkeypatch.setattr(auth_module.api_client, "get", fake_get)
    monkeypatch.setattr(auth_module, "_sync_auth_cookie", lambda access_token: cookie_calls.append(access_token))

    auth_module.init_session_state()

    assert auth_module.is_authenticated() is False
    assert fake_streamlit.session_state.logged_in is False
    assert fake_streamlit.session_state.access_token == "persisted-token"
    assert fake_streamlit.session_state.user_id is None
    assert fake_streamlit.session_state.username is None
    assert fake_streamlit.session_state.email is None
    assert cookie_calls == []


def test_auth_init_session_state_attempts_browser_storage_rehydration_when_no_cookie(monkeypatch):
    fake_streamlit, _, auth_module, _ = load_frontend_modules(
        monkeypatch,
        mock_mode="false",
    )
    html_calls = []

    monkeypatch.setattr(auth_module, "_restore_session_from_persisted_token", lambda persisted_token: None)
    monkeypatch.setattr(auth_module, "_get_persisted_access_token", lambda: None)
    monkeypatch.setattr(auth_module, "_run_browser_auth_bridge", lambda: html_calls.append("bridge"))

    auth_module.init_session_state()

    assert html_calls == ["bridge"]


def test_sync_auth_cookie_persists_browser_storage_and_secure_flag(monkeypatch):
    _, _, auth_module, _ = load_frontend_modules(monkeypatch)
    html_payloads = []

    def fake_html(markup, **kwargs):
        html_payloads.append(markup)

    components_v1 = sys.modules["streamlit.components.v1"]
    monkeypatch.setattr(components_v1, "html", fake_html)

    auth_module._sync_auth_cookie("persisted-token")

    assert html_payloads
    markup = html_payloads[0]
    assert "localStorage.setItem" in markup
    assert "boundary_circle_access_token" in markup
    assert "Secure" in markup


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


def test_auth_fetch_user_info_persists_full_name(monkeypatch):
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
        "get",
        lambda endpoint, params=None: Response(
            {
                "id": 7,
                "username": "alice",
                "email": "alice@example.com",
                "full_name": "Alice Chen",
            }
        ),
    )

    assert auth_module._fetch_user_info() is True
    assert fake_streamlit.session_state.user_id == 7
    assert fake_streamlit.session_state.username == "alice"
    assert fake_streamlit.session_state.email == "alice@example.com"
    assert fake_streamlit.session_state.full_name == "Alice Chen"


def test_api_client_profile_mock_mode_supports_read_and_update(monkeypatch):
    fake_streamlit, api_module, auth_module, _ = load_frontend_modules(monkeypatch)
    auth_module.init_session_state()
    fake_streamlit.session_state.user_id = 9
    fake_streamlit.session_state.username = "profile_user"
    fake_streamlit.session_state.email = "profile_user@example.com"
    fake_streamlit.session_state.full_name = "Profile User"

    client = api_module.APIClient()

    initial_response = client.get("/profile/me")
    assert initial_response.status_code == 200
    assert initial_response.json() == {
        "id": 9,
        "username": "profile_user",
        "email": "profile_user@example.com",
        "full_name": "Profile User",
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

    updated_response = client.put(
        "/profile/me",
        data={
            "full_name": "Updated User",
            "gender": "Other",
            "birthday": "2001-04-03",
            "bio": "Updated bio",
            "show_email": False,
        },
    )

    assert updated_response.status_code == 200
    assert updated_response.json()["full_name"] == "Updated User"
    assert updated_response.json()["gender"] == "Other"
    assert updated_response.json()["show_email"] is False


def test_api_client_public_profile_mock_mode_supports_read(monkeypatch):
    _, api_module, auth_module, _ = load_frontend_modules(monkeypatch)
    auth_module.init_session_state()

    response = api_module.api_client.get("/users/2/profile")

    assert response.status_code == 200
    assert response.json()["id"] == 2
    assert response.json()["username"] == "bob"
    assert response.json()["email"] == "bob@example.com"


def test_register_success_sets_profile_completion_prompt(monkeypatch):
    fake_streamlit, auth_page_module = load_auth_page_module(monkeypatch)

    monkeypatch.setattr(
        auth_page_module,
        "register",
        lambda username, email, password: (True, "Registration successful! Please login."),
    )

    auth_page_module.handle_register(
        username="alice",
        email="alice@example.com",
        password="secret123",
        confirm_password="secret123",
    )

    assert fake_streamlit.session_state.get("show_profile_completion_prompt") is not True
    assert fake_streamlit.session_state.get("suggested_profile_username") is None


def test_login_success_redirects_to_home(monkeypatch):
    fake_streamlit, auth_page_module = load_auth_page_module(monkeypatch)
    redirected = {}

    monkeypatch.setattr(
        auth_page_module,
        "login",
        lambda email, password: (True, "Login successful!"),
    )
    monkeypatch.setattr(
        fake_streamlit,
        "switch_page",
        lambda target: redirected.setdefault("target", target),
    )

    auth_page_module.handle_login("alice@example.com", "secret123")

    assert redirected["target"] == "Home.py"


def test_profile_page_save_updates_session_full_name(monkeypatch):
    fake_streamlit, api_module, auth_module, _ = load_frontend_modules(monkeypatch)
    auth_module.init_session_state()
    fake_streamlit.session_state.full_name = None

    response = api_module.api_client.put(
        "/profile/me",
        data={
            "full_name": "Chen Junyu",
            "gender": "Male",
            "birthday": "2001-04-03",
            "bio": "Updated bio",
        },
    )

    if response.ok:
        fake_streamlit.session_state.full_name = response.json().get("full_name")

    assert fake_streamlit.session_state.full_name == "Chen Junyu"


def test_public_profile_page_build_rows_skips_hidden_fields(monkeypatch):
    _, public_profile_page_module = load_public_profile_page_module(monkeypatch)

    rows = public_profile_page_module.build_public_profile_rows(
        {
            "username": "cjy",
            "full_name": None,
            "email": "cjy@example.com",
            "gender": None,
            "birthday": "2001-04-03",
            "bio": None,
        }
    )

    assert rows == [
        ("Username", "cjy"),
        ("Email", "cjy@example.com"),
        ("Birthday", "2001-04-03"),
    ]


def test_public_profile_page_parses_query_param_user_id(monkeypatch):
    fake_streamlit, public_profile_page_module = load_public_profile_page_module(monkeypatch)
    fake_streamlit.query_params["user_id"] = "17"

    assert public_profile_page_module.get_target_user_id() == 17


def test_public_profile_page_prefers_session_target_user_id(monkeypatch):
    fake_streamlit, public_profile_page_module = load_public_profile_page_module(monkeypatch)
    fake_streamlit.session_state.public_profile_target_user_id = 29
    fake_streamlit.query_params["user_id"] = "17"

    assert public_profile_page_module.get_target_user_id() == 29


def test_public_profile_page_builds_avatar_text_from_username(monkeypatch):
    _, public_profile_page_module = load_public_profile_page_module(monkeypatch)

    assert public_profile_page_module.build_avatar_text("cjy") == "CJ"
    assert public_profile_page_module.build_avatar_text("陈俊宇") == "陈俊"
    assert public_profile_page_module.build_avatar_text(None) == "U"


def test_public_profile_page_go_back_restores_context_before_switch(monkeypatch):
    fake_streamlit, public_profile_page_module = load_public_profile_page_module(monkeypatch)
    switched = {}

    fake_streamlit.session_state.public_profile_return_page = "pages/team_management.py"
    fake_streamlit.session_state.public_profile_target_user_id = 12
    fake_streamlit.session_state.public_profile_return_context = {
        "current_circle_id": 5,
        "selected_team_id": 12,
        "team_management_focus_detail": True,
    }
    fake_streamlit.query_params["user_id"] = "12"
    fake_streamlit.switch_page = lambda target: switched.setdefault("target", target)

    public_profile_page_module.go_back()

    assert fake_streamlit.session_state.current_circle_id == 5
    assert fake_streamlit.session_state.selected_team_id == 12
    assert fake_streamlit.session_state.team_management_focus_detail is True
    assert "public_profile_target_user_id" not in fake_streamlit.session_state
    assert "user_id" not in fake_streamlit.query_params
    assert switched["target"] == "pages/team_management.py"


def test_home_build_account_summary_includes_profile_fields_and_visibility(monkeypatch):
    _, home_module = load_home_module(monkeypatch)

    rows = home_module.build_account_summary(
        {
            "username": "cjy",
            "email": "cjy@example.com",
            "full_name": "Chen Junyu",
        },
        {
            "gender": "Male",
            "birthday": "2001-04-03",
            "bio": "Backend and badminton.",
            "show_full_name": True,
            "show_gender": False,
            "show_birthday": True,
            "show_email": True,
            "show_bio": False,
        },
    )

    assert rows == [
        ("Username", "cjy", None),
        ("Full name", "Chen Junyu", None),
        ("Email", "cjy@example.com", None),
        ("Gender", "Male", "Hidden"),
        ("Birthday", "2001-04-03", None),
        ("Bio", "Backend and badminton.", "Hidden"),
    ]


def test_home_format_account_summary_row_uses_muted_badges(monkeypatch):
    _, home_module = load_home_module(monkeypatch)

    hidden_row = home_module.format_account_summary_row("Bio", "Backend and badminton.", "Hidden")
    public_row = home_module.format_account_summary_row("Email", "cjy@example.com", None)

    assert "Hidden" in hidden_row
    assert "#6b7280" in hidden_row
    assert "Hidden" not in public_row
    assert "#9ca3af" not in public_row


def test_login_sets_profile_completion_prompt_for_incomplete_profile(monkeypatch):
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

    def fake_get(endpoint, params=None):
        if endpoint == "/auth/me":
            return Response(
                {
                    "id": 7,
                    "username": "alice",
                    "email": "alice@example.com",
                    "full_name": "Alice Chen",
                }
            )
        if endpoint == "/profile/me":
            return Response(
                {
                    "id": 7,
                    "username": "alice",
                    "email": "alice@example.com",
                    "full_name": "Alice Chen",
                    "gender": None,
                    "birthday": None,
                    "bio": None,
                    "show_full_name": True,
                    "show_gender": True,
                    "show_birthday": True,
                    "show_email": True,
                    "show_bio": True,
                    "profile_prompt_dismissed": False,
                }
            )
        raise AssertionError(endpoint)

    monkeypatch.setattr(auth_module.api_client, "get", fake_get)

    logged_in, message = auth_module.login(
        email="alice@example.com",
        password="secret123",
    )

    assert logged_in is True
    assert message == "Login successful!"
    assert fake_streamlit.session_state.show_profile_completion_prompt is True


def test_login_skips_profile_prompt_when_dismissed(monkeypatch):
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

    def fake_get(endpoint, params=None):
        if endpoint == "/auth/me":
            return Response(
                {
                    "id": 7,
                    "username": "alice",
                    "email": "alice@example.com",
                    "full_name": "Alice Chen",
                }
            )
        if endpoint == "/profile/me":
            return Response(
                {
                    "id": 7,
                    "username": "alice",
                    "email": "alice@example.com",
                    "full_name": "Alice Chen",
                    "gender": None,
                    "birthday": None,
                    "bio": None,
                    "show_full_name": True,
                    "show_gender": True,
                    "show_birthday": True,
                    "show_email": True,
                    "show_bio": True,
                    "profile_prompt_dismissed": True,
                }
            )
        raise AssertionError(endpoint)

    monkeypatch.setattr(auth_module.api_client, "get", fake_get)

    logged_in, _ = auth_module.login(
        email="alice@example.com",
        password="secret123",
    )

    assert logged_in is True
    assert fake_streamlit.session_state.get("show_profile_completion_prompt") is not True


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
    fake_streamlit.session_state["admin_tag_option_count_5"] = 3
    fake_streamlit.session_state["admin_tag_option_5_0"] = "AI"
    fake_streamlit.session_state["admin_tag_option_5_1"] = "SE"
    fake_streamlit.session_state["admin_tag_option_5_2"] = "DS"

    circle_detail_module.clear_admin_tag_form_state(5)

    assert "admin_tag_name_5" not in fake_streamlit.session_state
    assert "admin_tag_type_5" not in fake_streamlit.session_state
    assert "admin_tag_required_5" not in fake_streamlit.session_state
    assert "admin_tag_options_5" not in fake_streamlit.session_state
    assert "admin_tag_max_selections_5" not in fake_streamlit.session_state
    assert "admin_tag_option_count_5" not in fake_streamlit.session_state
    assert "admin_tag_option_5_0" not in fake_streamlit.session_state
    assert "admin_tag_option_5_1" not in fake_streamlit.session_state
    assert "admin_tag_option_5_2" not in fake_streamlit.session_state


def test_circle_detail_admin_tag_field_visibility_matches_type(monkeypatch):
    _, circle_detail_module = load_circle_detail_module(monkeypatch)

    assert circle_detail_module.should_show_tag_options_field("integer") is False
    assert circle_detail_module.should_show_tag_options_field("single_select") is True
    assert circle_detail_module.should_show_tag_options_field("multi_select") is True

    assert circle_detail_module.should_show_max_selections_field("integer") is False
    assert circle_detail_module.should_show_max_selections_field("single_select") is False
    assert circle_detail_module.should_show_max_selections_field("multi_select") is True


def test_circle_detail_admin_tag_type_choices_exclude_string(monkeypatch):
    _, circle_detail_module = load_circle_detail_module(monkeypatch)

    assert circle_detail_module.ADMIN_TAG_TYPE_OPTIONS == [
        "integer",
        "float",
        "boolean",
        "single_select",
        "multi_select",
    ]


def test_circle_detail_get_admin_tag_option_values_initializes_two_blank_rows(monkeypatch):
    fake_streamlit, circle_detail_module = load_circle_detail_module(monkeypatch)

    values = circle_detail_module.get_admin_tag_option_values(5)

    assert values == ["", ""]
    assert fake_streamlit.session_state["admin_tag_option_count_5"] == 2


def test_circle_detail_get_admin_tag_option_values_reads_existing_rows(monkeypatch):
    fake_streamlit, circle_detail_module = load_circle_detail_module(monkeypatch)

    fake_streamlit.session_state["admin_tag_option_count_5"] = 3
    fake_streamlit.session_state["admin_tag_option_5_0"] = "AI"
    fake_streamlit.session_state["admin_tag_option_5_1"] = "SE"
    fake_streamlit.session_state["admin_tag_option_5_2"] = "DS"

    values = circle_detail_module.get_admin_tag_option_values(5)

    assert values == ["AI", "SE", "DS"]


def test_circle_detail_build_selection_options_payload_from_option_rows(monkeypatch):
    _, circle_detail_module = load_circle_detail_module(monkeypatch)

    payload, error_message = circle_detail_module.build_selection_options_payload(
        [" AI ", "", "SE", "AI"]
    )

    assert payload == '["AI", "SE"]'
    assert error_message == ""


def test_circle_detail_build_selection_options_payload_rejects_empty_options(monkeypatch):
    _, circle_detail_module = load_circle_detail_module(monkeypatch)

    payload, error_message = circle_detail_module.build_selection_options_payload(["", "   "])

    assert payload is None
    assert error_message == "At least one option is required for selection types."


def test_circle_detail_main_shows_member_tag_summary(monkeypatch):
    fake_streamlit, circle_detail_module = load_circle_detail_module(monkeypatch)

    captions: list[str] = []
    fake_streamlit.caption = lambda message="", *args, **kwargs: captions.append(str(message))
    fake_streamlit.button = lambda *args, **kwargs: False
    fake_streamlit.title = lambda *args, **kwargs: None
    fake_streamlit.markdown = lambda *args, **kwargs: None
    fake_streamlit.success = lambda *args, **kwargs: None
    fake_streamlit.warning = lambda *args, **kwargs: None
    fake_streamlit.info = lambda *args, **kwargs: None
    fake_streamlit.error = lambda *args, **kwargs: None
    fake_streamlit.columns = lambda spec: tuple(type("DummyContext", (), {"__enter__": lambda self: self, "__exit__": lambda self, exc_type, exc, tb: False})() for _ in range(len(spec) if isinstance(spec, list) else spec))
    fake_streamlit.container = lambda *args, **kwargs: type("DummyContext", (), {"__enter__": lambda self: self, "__exit__": lambda self, exc_type, exc, tb: False})()
    fake_streamlit.expander = lambda *args, **kwargs: type("DummyContext", (), {"__enter__": lambda self: self, "__exit__": lambda self, exc_type, exc, tb: False})()
    fake_streamlit.form = lambda *args, **kwargs: type("DummyContext", (), {"__enter__": lambda self: self, "__exit__": lambda self, exc_type, exc, tb: False})()
    fake_streamlit.page_link = lambda *args, **kwargs: None

    fake_streamlit.session_state.circle_hall_focus_detail = True

    monkeypatch.setattr(circle_detail_module, "apply_button_usability_style", lambda: None)
    monkeypatch.setattr(circle_detail_module, "require_auth", lambda: None)
    monkeypatch.setattr(circle_detail_module, "resolve_circle_id", lambda query_params=None: 5)
    monkeypatch.setattr(circle_detail_module, "get_current_user", lambda: {"id": 7, "username": "viewer"})
    monkeypatch.setattr(
        circle_detail_module,
        "fetch_circle_detail",
        lambda circle_id: {"id": 5, "name": "AI Circle", "creator_id": 1, "creator_username": "creator"},
    )
    monkeypatch.setattr(
        circle_detail_module,
        "fetch_circle_members",
        lambda circle_id: [{"id": 9, "username": "alice", "email": "alice@example.com"}],
    )
    monkeypatch.setattr(circle_detail_module, "fetch_circle_tags", lambda circle_id: [])
    monkeypatch.setattr(
        circle_detail_module,
        "fetch_freedom_tag_profile",
        lambda circle_id: {"freedom_tag_text": "", "freedom_tag_profile": {"keywords": []}},
    )
    monkeypatch.setattr(
        circle_detail_module,
        "fetch_member_tags",
        lambda circle_id, user_id: [{"tag_name": "Major", "data_type": "single_select", "value": "AI"}],
    )

    circle_detail_module.main()

    assert any("Tags: Major: AI" in caption for caption in captions)


def test_circle_detail_main_labels_creator_member_as_creator(monkeypatch):
    fake_streamlit, circle_detail_module = load_circle_detail_module(monkeypatch)

    markdown_calls: list[str] = []
    fake_streamlit.markdown = lambda message="", *args, **kwargs: markdown_calls.append(str(message))
    fake_streamlit.caption = lambda *args, **kwargs: None
    fake_streamlit.button = lambda *args, **kwargs: False
    fake_streamlit.title = lambda *args, **kwargs: None
    fake_streamlit.success = lambda *args, **kwargs: None
    fake_streamlit.warning = lambda *args, **kwargs: None
    fake_streamlit.info = lambda *args, **kwargs: None
    fake_streamlit.error = lambda *args, **kwargs: None
    fake_streamlit.columns = lambda spec: tuple(type("DummyContext", (), {"__enter__": lambda self: self, "__exit__": lambda self, exc_type, exc, tb: False})() for _ in range(len(spec) if isinstance(spec, list) else spec))
    fake_streamlit.container = lambda *args, **kwargs: type("DummyContext", (), {"__enter__": lambda self: self, "__exit__": lambda self, exc_type, exc, tb: False})()
    fake_streamlit.expander = lambda *args, **kwargs: type("DummyContext", (), {"__enter__": lambda self: self, "__exit__": lambda self, exc_type, exc, tb: False})()
    fake_streamlit.form = lambda *args, **kwargs: type("DummyContext", (), {"__enter__": lambda self: self, "__exit__": lambda self, exc_type, exc, tb: False})()
    fake_streamlit.page_link = lambda *args, **kwargs: None

    fake_streamlit.session_state.circle_hall_focus_detail = True

    monkeypatch.setattr(circle_detail_module, "apply_button_usability_style", lambda: None)
    monkeypatch.setattr(circle_detail_module, "require_auth", lambda: None)
    monkeypatch.setattr(circle_detail_module, "resolve_circle_id", lambda query_params=None: 5)
    monkeypatch.setattr(circle_detail_module, "get_current_user", lambda: {"id": 7, "username": "viewer"})
    monkeypatch.setattr(
        circle_detail_module,
        "fetch_circle_detail",
        lambda circle_id: {"id": 5, "name": "AI Circle", "creator_id": 9, "creator_username": "alice"},
    )
    monkeypatch.setattr(
        circle_detail_module,
        "fetch_circle_members",
        lambda circle_id: [{"id": 9, "username": "alice", "email": "alice@example.com"}],
    )
    monkeypatch.setattr(circle_detail_module, "fetch_circle_tags", lambda circle_id: [])
    monkeypatch.setattr(
        circle_detail_module,
        "fetch_freedom_tag_profile",
        lambda circle_id: {"freedom_tag_text": "", "freedom_tag_profile": {"keywords": []}},
    )
    monkeypatch.setattr(circle_detail_module, "fetch_member_tags", lambda circle_id, user_id: [])

    circle_detail_module.main()

    assert any(">Creator<" in value for value in markdown_calls)


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

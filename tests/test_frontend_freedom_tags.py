"""Frontend tests for freedom tags and matching explanations."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))


class SessionState(dict):
    def __getattr__(self, item: str):
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc

    def __setattr__(self, key: str, value):
        self[key] = value


class DummyContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def load_circle_detail_module(monkeypatch):
    """Load circle_detail module with mocked dependencies."""
    for name in [
        "frontend.views.circle_detail",
        "frontend.utils.api",
        "frontend.utils.auth",
        "streamlit",
        "utils.api",
        "utils.auth",
    ]:
        sys.modules.pop(name, None)

    fake_streamlit = ModuleType("streamlit")
    fake_streamlit_attrs = {
        "session_state": SessionState(),
        "query_params": {},
        "set_page_config": lambda *args, **kwargs: None,
        "switch_page": lambda *args, **kwargs: None,
        "warning": lambda *args, **kwargs: None,
        "stop": lambda: None,
        "success": lambda *args, **kwargs: None,
        "error": lambda *args, **kwargs: None,
        "info": lambda *args, **kwargs: None,
        "markdown": lambda *args, **kwargs: None,
        "title": lambda *args, **kwargs: None,
        "page_link": lambda *args, **kwargs: None,
        "columns": lambda *args, **kwargs: (None, None),
        "container": lambda *args, **kwargs: None,
        "button": lambda *args, **kwargs: False,
        "rerun": lambda: None,
        "form": lambda *args, **kwargs: DummyContext(),
        "form_submit_button": lambda *args, **kwargs: False,
        "text_input": lambda *args, **kwargs: "",
        "text_area": lambda *args, **kwargs: "",
        "selectbox": lambda label, options, **kwargs: options[0] if options else None,
        "multiselect": lambda *args, **kwargs: [],
        "number_input": lambda *args, **kwargs: 0,
        "checkbox": lambda *args, **kwargs: False,
        "caption": lambda *args, **kwargs: None,
        "write": lambda *args, **kwargs: None,
        "expander": lambda *args, **kwargs: DummyContext(),
    }
    for attr_name, value in fake_streamlit_attrs.items():
        setattr(fake_streamlit, attr_name, value)

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setenv("MOCK_MODE", "false")
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:8000")

    detail_module = importlib.import_module("frontend.views.circle_detail")
    return fake_streamlit, detail_module


def load_team_management_module(monkeypatch):
    """Load team_management module with mocked dependencies."""
    for name in [
        "frontend.pages.team_management",
        "frontend.utils.api",
        "frontend.utils.auth",
        "streamlit",
        "utils.api",
        "utils.auth",
    ]:
        sys.modules.pop(name, None)

    fake_streamlit = ModuleType("streamlit")
    fake_streamlit_attrs = {
        "session_state": SessionState(),
        "query_params": {},
        "set_page_config": lambda *args, **kwargs: None,
        "switch_page": lambda *args, **kwargs: None,
        "warning": lambda *args, **kwargs: None,
        "stop": lambda: None,
        "success": lambda *args, **kwargs: None,
        "error": lambda *args, **kwargs: None,
        "info": lambda *args, **kwargs: None,
        "markdown": lambda *args, **kwargs: None,
        "title": lambda *args, **kwargs: None,
        "header": lambda *args, **kwargs: None,
        "subheader": lambda *args, **kwargs: None,
        "caption": lambda *args, **kwargs: None,
        "write": lambda *args, **kwargs: None,
        "divider": lambda *args, **kwargs: None,
        "rerun": lambda: None,
        "button": lambda *args, **kwargs: False,
        "tabs": lambda labels: [DummyContext() for _ in labels],
        "columns": lambda spec: tuple(DummyContext() for _ in range(len(spec) if isinstance(spec, list) else spec)),
        "container": lambda *args, **kwargs: DummyContext(),
        "expander": lambda *args, **kwargs: DummyContext(),
        "form": lambda *args, **kwargs: DummyContext(),
        "form_submit_button": lambda *args, **kwargs: False,
        "text_input": lambda *args, **kwargs: "",
        "text_area": lambda *args, **kwargs: "",
        "selectbox": lambda label, options, **kwargs: options[0] if options else None,
        "multiselect": lambda *args, **kwargs: [],
        "number_input": lambda *args, **kwargs: 0,
    }
    for attr_name, value in fake_streamlit_attrs.items():
        setattr(fake_streamlit, attr_name, value)

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setenv("MOCK_MODE", "true")
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:8000")

    api_module = importlib.import_module("frontend.utils.api")
    auth_module = importlib.import_module("frontend.utils.auth")
    monkeypatch.setitem(sys.modules, "utils.api", api_module)
    monkeypatch.setitem(sys.modules, "utils.auth", auth_module)
    team_module = importlib.import_module("frontend.pages.team_management")
    return fake_streamlit, api_module, auth_module, team_module


def test_save_freedom_tag_profile_uses_put_endpoint(monkeypatch):
    """Test that save_freedom_tag_profile uses PUT /circles/{circle_id}/profile."""
    _, detail_module = load_circle_detail_module(monkeypatch)

    class Response:
        ok = True
        reason = "OK"

        def json(self):
            return {"message": "Profile saved"}

    captured = {}

    def fake_put(endpoint, data=None, params=None):
        captured["endpoint"] = endpoint
        captured["data"] = data
        captured["params"] = params
        return Response()

    monkeypatch.setattr(detail_module, "get_current_user", lambda: {"id": 42})
    monkeypatch.setattr(detail_module.api_client, "put", fake_put)

    success, message = detail_module.save_freedom_tag_profile(
        circle_id=5,
        freedom_tag_text="Python, AI, Machine Learning"
    )

    assert success is True
    assert captured["endpoint"] == "/circles/5/profile"
    assert captured["data"] == {"freedom_tag_text": "Python, AI, Machine Learning"}
    assert captured["params"] is None


def test_save_freedom_tag_profile_returns_error_on_failure(monkeypatch):
    """Test that save_freedom_tag_profile handles API errors."""
    _, detail_module = load_circle_detail_module(monkeypatch)

    class Response:
        ok = False
        reason = "Bad Request"

        def json(self):
            return {"detail": "Invalid freedom tag text"}

    def fake_put(endpoint, data=None, params=None):
        return Response()

    monkeypatch.setattr(detail_module, "get_current_user", lambda: {"id": 42})
    monkeypatch.setattr(detail_module.api_client, "put", fake_put)

    success, message = detail_module.save_freedom_tag_profile(
        circle_id=5,
        freedom_tag_text="too long" * 1000
    )

    assert success is False
    assert "Invalid freedom tag text" in message


def test_save_freedom_tag_profile_requires_login(monkeypatch):
    """Test that save_freedom_tag_profile requires a logged-in user."""
    _, detail_module = load_circle_detail_module(monkeypatch)

    monkeypatch.setattr(detail_module, "get_current_user", lambda: None)

    success, message = detail_module.save_freedom_tag_profile(
        circle_id=5,
        freedom_tag_text="Python"
    )

    assert success is False
    assert "login" in message.lower()


def test_fetch_freedom_tag_profile_uses_get_endpoint(monkeypatch):
    """Frontend should fetch the saved freedom tag profile from the circle profile endpoint."""
    _, detail_module = load_circle_detail_module(monkeypatch)

    class Response:
        ok = True
        reason = "OK"

        def json(self):
            return {
                "freedom_tag_text": "Python FastAPI Docker",
                "freedom_tag_profile": {"keywords": ["Python", "FastAPI", "Docker"]},
            }

    captured = {}

    def fake_get(endpoint, params=None):
        captured["endpoint"] = endpoint
        captured["params"] = params
        return Response()

    monkeypatch.setattr(detail_module.api_client, "get", fake_get)

    payload = detail_module.fetch_freedom_tag_profile(circle_id=5)

    assert captured["endpoint"] == "/circles/5/profile"
    assert captured["params"] is None
    assert payload["freedom_tag_text"] == "Python FastAPI Docker"
    assert payload["freedom_tag_profile"]["keywords"] == ["Python", "FastAPI", "Docker"]


def test_fetch_freedom_tag_profile_falls_back_to_empty(monkeypatch):
    """Frontend should gracefully fall back when the saved profile cannot be fetched."""
    _, detail_module = load_circle_detail_module(monkeypatch)

    class Response:
        ok = False
        reason = "Forbidden"

        def json(self):
            return {"detail": "User must join the circle first"}

    monkeypatch.setattr(detail_module.api_client, "get", lambda endpoint, params=None: Response())

    payload = detail_module.fetch_freedom_tag_profile(circle_id=5)

    assert payload == {"freedom_tag_text": "", "freedom_tag_profile": {"keywords": []}}


def test_create_team_includes_freedom_requirement_text(monkeypatch):
    """Test that create_team helper includes freedom_requirement_text in API payload."""
    _, _, _, team_module = load_team_management_module(monkeypatch)

    class Response:
        ok = True
        reason = "OK"

        def json(self):
            return {"id": 99, "name": "AI Team"}

    captured = {}

    def fake_post(endpoint, data=None, params=None):
        captured["endpoint"] = endpoint
        captured["data"] = data
        return Response()

    monkeypatch.setattr(team_module, "get_current_user", lambda: {"id": 7})
    monkeypatch.setattr(team_module.api_client, "post", fake_post)

    success, message = team_module.create_team(
        name="AI Team",
        description="A team for AI enthusiasts",
        max_members=4,
        required_tags=["Tech Stack"],
        required_tag_rules=[{"tag_name": "Tech Stack", "expected_value": "Python"}],
        circle_id=3,
        freedom_requirement_text="Looking for passionate developers",
    )

    assert success is True
    assert captured["data"]["freedom_requirement_text"] == "Looking for passionate developers"


def test_create_team_with_empty_freedom_requirement_text(monkeypatch):
    """Test that create_team handles empty freedom_requirement_text."""
    _, _, _, team_module = load_team_management_module(monkeypatch)

    class Response:
        ok = True
        reason = "OK"

        def json(self):
            return {"id": 100, "name": "Dev Team"}

    captured = {}

    def fake_post(endpoint, data=None, params=None):
        captured["endpoint"] = endpoint
        captured["data"] = data
        return Response()

    monkeypatch.setattr(team_module, "get_current_user", lambda: {"id": 7})
    monkeypatch.setattr(team_module.api_client, "post", fake_post)

    success, message = team_module.create_team(
        name="Dev Team",
        description="Development team",
        max_members=5,
        required_tags=[],
        required_tag_rules=[],
        circle_id=3,
        freedom_requirement_text="",
    )

    assert success is True
    assert captured["data"]["freedom_requirement_text"] == ""


def test_create_team_default_freedom_requirement_text(monkeypatch):
    """Test that create_team uses empty string as default for freedom_requirement_text."""
    _, _, _, team_module = load_team_management_module(monkeypatch)

    class Response:
        ok = True
        reason = "OK"

        def json(self):
            return {"id": 101, "name": "Default Team"}

    captured = {}

    def fake_post(endpoint, data=None, params=None):
        captured["endpoint"] = endpoint
        captured["data"] = data
        return Response()

    monkeypatch.setattr(team_module, "get_current_user", lambda: {"id": 7})
    monkeypatch.setattr(team_module.api_client, "post", fake_post)

    success, message = team_module.create_team(
        name="Default Team",
        description="Test team",
        max_members=3,
        required_tags=[],
        required_tag_rules=[],
        circle_id=3,
    )

    assert success is True
    assert captured["data"]["freedom_requirement_text"] == ""


def test_build_match_explanation_prefers_keyword_and_tag_signals(monkeypatch):
    """Explanation should summarize non-duplicate keyword/final-score signals without calling an LLM."""
    _, _, _, team_module = load_team_management_module(monkeypatch)

    explanation = team_module.build_match_explanation(
        {
            "matched_tags": ["role=backend"],
            "matched_freedom_keywords": ["Python", "FastAPI"],
            "final_score": 0.91,
            "keyword_overlap_score": 0.8,
        }
    )

    assert "Python" in explanation
    assert "FastAPI" in explanation
    assert "0.91" in explanation
    assert "Matched tags" not in explanation


def test_build_match_explanation_handles_missing_signals(monkeypatch):
    """Explanation should degrade gracefully when keyword/tag matches are absent."""
    _, _, _, team_module = load_team_management_module(monkeypatch)

    explanation = team_module.build_match_explanation(
        {
            "matched_tags": [],
            "matched_freedom_keywords": [],
            "final_score": 0.7,
            "keyword_overlap_score": 0.0,
        }
    )

    assert "Final score" in explanation
    assert "Keyword overlap" not in explanation


def test_build_team_freedom_summary_includes_text_and_keywords(monkeypatch):
    """Team freedom summary should surface saved free-text requirements and extracted keywords."""
    _, _, _, team_module = load_team_management_module(monkeypatch)

    summary = team_module.build_team_freedom_summary(
        {
            "freedom_requirement_text": "Looking for Python backend teammates who communicate directly.",
            "freedom_requirement_profile_keywords": ["Python", "backend", "direct communication"],
        }
    )

    assert "Looking for Python backend teammates" in summary
    assert "Python" in summary
    assert "backend" in summary


def test_build_team_freedom_summary_returns_empty_when_absent(monkeypatch):
    """Team freedom summary should be empty when no free-text requirement exists."""
    _, _, _, team_module = load_team_management_module(monkeypatch)

    summary = team_module.build_team_freedom_summary(
        {
            "freedom_requirement_text": "",
            "freedom_requirement_profile_keywords": [],
        }
    )

    assert summary == ""


def test_render_team_detail_hides_member_only_sections_for_non_team_member(monkeypatch):
    """Circle members outside the selected team should not see member-only team detail sections."""
    fake_streamlit, _, _, team_module = load_team_management_module(monkeypatch)

    warnings: list[str] = []
    subheaders: list[str] = []
    fetch_team_invitations_called = {"value": False}

    fake_streamlit.warning = lambda message, *args, **kwargs: warnings.append(message)
    fake_streamlit.subheader = lambda message, *args, **kwargs: subheaders.append(message)
    fake_streamlit.columns = lambda spec: tuple(DummyContext() for _ in range(len(spec) if isinstance(spec, list) else spec))
    fake_streamlit.container = lambda *args, **kwargs: DummyContext()
    fake_streamlit.button = lambda *args, **kwargs: False

    fake_streamlit.session_state.current_circle_id = 5
    fake_streamlit.session_state.selected_team_id = 11

    monkeypatch.setattr(team_module, "get_current_user", lambda: {"id": 7, "username": "outsider"})
    monkeypatch.setattr(
        team_module,
        "fetch_teams",
        lambda circle_id: [
            {
                "id": 11,
                "name": "Core Team",
                "creator_id": 2,
                "creator_username": "creator",
                "description": "Private details",
                "status": "Recruiting",
                "current_members": 2,
                "max_members": 5,
                "member_ids": [2, 3],
            }
        ],
    )
    monkeypatch.setattr(
        team_module,
        "fetch_circle_members",
        lambda circle_id: [
            {"id": 2, "username": "creator", "email": "creator@example.com"},
            {"id": 3, "username": "member", "email": "member@example.com"},
            {"id": 7, "username": "outsider", "email": "outsider@example.com"},
        ],
    )

    def fake_fetch_team_invitations(team_id: int):
        fetch_team_invitations_called["value"] = True
        raise AssertionError("Non-members should not load team invitations.")

    monkeypatch.setattr(team_module, "fetch_team_invitations", fake_fetch_team_invitations)

    team_module.render_team_detail()

    assert fetch_team_invitations_called["value"] is False
    assert any("join this team" in message.lower() for message in warnings)
    assert "Members" not in subheaders
    assert "Invite Members" not in subheaders


def test_team_management_main_hides_circle_hall_button_in_normal_state(monkeypatch):
    """The normal team management page should only show the back-to-circle-detail action."""
    fake_streamlit, _, _, team_module = load_team_management_module(monkeypatch)

    button_labels: list[str] = []

    fake_streamlit.session_state.current_circle_id = 5
    fake_streamlit.session_state.team_management_focus_detail = False
    fake_streamlit.button = lambda label, *args, **kwargs: button_labels.append(label) or False
    fake_streamlit.tabs = lambda labels: [DummyContext() for _ in labels]
    fake_streamlit.columns = lambda spec: tuple(
        DummyContext() for _ in range(len(spec) if isinstance(spec, list) else spec)
    )

    monkeypatch.setattr(team_module, "require_auth", lambda: None)
    monkeypatch.setattr(team_module, "can_access_current_circle", lambda circle_id: True)
    monkeypatch.setattr(team_module, "render_team_list", lambda: None)
    monkeypatch.setattr(team_module, "render_create_team", lambda: None)
    monkeypatch.setattr(team_module, "render_my_teams", lambda: None)
    monkeypatch.setattr(team_module, "render_invitation_management", lambda: None)
    monkeypatch.setattr(team_module, "render_matching_section", lambda: None)

    team_module.main()

    assert any("Back to Circle Detail" in label for label in button_labels)
    assert all("Back to Circle Hall" not in label for label in button_labels)

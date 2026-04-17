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


def load_team_modules(monkeypatch):
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


class DummyContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_accepting_invitation_updates_team_membership(monkeypatch):
    fake_streamlit, api_module, _, _ = load_team_modules(monkeypatch)
    fake_streamlit.session_state.user_id = 2
    fake_streamlit.session_state.logged_in = True
    fake_streamlit.session_state.mock_teams = {
        1: [
            {
                "id": 1,
                "name": "AI Team",
                "description": "Build an AI app",
                "max_members": 3,
                "current_members": 1,
                "status": "Recruiting",
                "creator_id": 1,
                "member_ids": [1],
            }
        ]
    }
    fake_streamlit.session_state.mock_invitations = [
        {
            "id": 10,
            "team_id": 1,
            "circle_id": 1,
            "team_name": "AI Team",
            "inviter_id": 1,
            "invitee_id": 2,
            "status": "pending",
        }
    ]

    response = api_module.api_client.post(
        "/invitations/10/respond",
        data={"accept": True},
    )

    payload = response.json()
    team = fake_streamlit.session_state.mock_teams[1][0]

    assert payload["success"] is True
    assert fake_streamlit.session_state.mock_invitations[0]["status"] == "accepted"
    assert team["member_ids"] == [1, 2]
    assert team["current_members"] == 2
    assert team["status"] == "Recruiting"


def test_split_user_teams_uses_member_ids_instead_of_other_peoples_teams(monkeypatch):
    _, _, _, team_module = load_team_modules(monkeypatch)

    teams = [
        {"id": 1, "name": "Created", "creator_id": 7, "member_ids": [7]},
        {"id": 2, "name": "Joined", "creator_id": 1, "member_ids": [1, 7]},
        {"id": 3, "name": "Other Team", "creator_id": 2, "member_ids": [2]},
    ]

    created, joined = team_module.split_user_teams(teams, user_id=7)

    assert [team["id"] for team in created] == [1]
    assert [team["id"] for team in joined] == [2]


def test_team_requirement_widget_keys_use_circle_and_tag_ids(monkeypatch):
    _, _, _, team_module = load_team_modules(monkeypatch)

    key_a = team_module.build_team_requirement_widget_key(3, {"id": 11, "name": "Major"})
    key_b = team_module.build_team_requirement_widget_key(3, {"id": 12, "name": "Major"})

    assert key_a == "team_requirement_3_11"
    assert key_b == "team_requirement_3_12"
    assert key_a != key_b


def test_open_team_detail_sets_focus_and_selected_team(monkeypatch):
    fake_streamlit, _, _, team_module = load_team_modules(monkeypatch)
    rerun_called = {"value": False}

    def fake_rerun():
        rerun_called["value"] = True

    fake_streamlit.rerun = fake_rerun

    team_module.open_team_detail(22)

    assert fake_streamlit.session_state.selected_team_id == 22
    assert fake_streamlit.session_state.team_management_focus_detail is True
    assert rerun_called["value"] is True

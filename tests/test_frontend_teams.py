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
        "frontend.pages.4_team_management",
        "frontend.utils.api",
        "frontend.utils.auth",
        "streamlit",
        "utils.api",
        "utils.auth",
    ]:
        sys.modules.pop(name, None)

    fake_streamlit = ModuleType("streamlit")
    fake_streamlit.session_state = SessionState()
    fake_streamlit.query_params = {}
    fake_streamlit.set_page_config = lambda *args, **kwargs: None
    fake_streamlit.switch_page = lambda *args, **kwargs: None
    fake_streamlit.warning = lambda *args, **kwargs: None
    fake_streamlit.stop = lambda: None
    fake_streamlit.success = lambda *args, **kwargs: None
    fake_streamlit.error = lambda *args, **kwargs: None
    fake_streamlit.info = lambda *args, **kwargs: None
    fake_streamlit.markdown = lambda *args, **kwargs: None
    fake_streamlit.title = lambda *args, **kwargs: None
    fake_streamlit.header = lambda *args, **kwargs: None
    fake_streamlit.subheader = lambda *args, **kwargs: None
    fake_streamlit.caption = lambda *args, **kwargs: None
    fake_streamlit.write = lambda *args, **kwargs: None
    fake_streamlit.divider = lambda *args, **kwargs: None
    fake_streamlit.rerun = lambda: None
    fake_streamlit.button = lambda *args, **kwargs: False
    fake_streamlit.tabs = lambda labels: [DummyContext() for _ in labels]
    fake_streamlit.columns = lambda spec: tuple(DummyContext() for _ in range(len(spec) if isinstance(spec, list) else spec))
    fake_streamlit.container = lambda *args, **kwargs: DummyContext()
    fake_streamlit.expander = lambda *args, **kwargs: DummyContext()
    fake_streamlit.form = lambda *args, **kwargs: DummyContext()
    fake_streamlit.form_submit_button = lambda *args, **kwargs: False
    fake_streamlit.text_input = lambda *args, **kwargs: ""
    fake_streamlit.text_area = lambda *args, **kwargs: ""
    fake_streamlit.selectbox = lambda label, options, **kwargs: options[0] if options else None
    fake_streamlit.multiselect = lambda *args, **kwargs: []
    fake_streamlit.number_input = lambda *args, **kwargs: 0

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setenv("MOCK_MODE", "true")
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:8000")

    api_module = importlib.import_module("frontend.utils.api")
    auth_module = importlib.import_module("frontend.utils.auth")
    monkeypatch.setitem(sys.modules, "utils.api", api_module)
    monkeypatch.setitem(sys.modules, "utils.auth", auth_module)
    team_module = importlib.import_module("frontend.pages.4_team_management")
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

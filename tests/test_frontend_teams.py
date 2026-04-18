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


def test_go_to_circle_detail_preserves_current_circle_and_switches_page(monkeypatch):
    fake_streamlit, _, _, team_module = load_team_modules(monkeypatch)
    switched = {}

    fake_streamlit.session_state.current_circle_id = 6
    fake_streamlit.session_state.circle_hall_focus_detail = False
    fake_streamlit.switch_page = lambda target: switched.setdefault("target", target)

    team_module.go_to_circle_detail()

    assert fake_streamlit.session_state.selected_circle_id == 6
    assert fake_streamlit.session_state.circle_hall_focus_detail is True
    assert switched["target"] == "pages/circles.py"


def test_go_to_circle_hall_clears_selected_circle_and_switches_page(monkeypatch):
    fake_streamlit, _, _, team_module = load_team_modules(monkeypatch)
    switched = {}

    fake_streamlit.session_state.current_circle_id = 6
    fake_streamlit.session_state.selected_circle_id = 6
    fake_streamlit.session_state.circle_hall_focus_detail = True
    fake_streamlit.switch_page = lambda target: switched.setdefault("target", target)

    team_module.go_to_circle_hall()

    assert fake_streamlit.session_state.circle_hall_focus_detail is False
    assert "selected_circle_id" not in fake_streamlit.session_state
    assert fake_streamlit.session_state.current_circle_id == 6
    assert switched["target"] == "pages/circles.py"


def test_open_public_profile_sets_return_context_and_switches_page(monkeypatch):
    fake_streamlit, _, _, team_module = load_team_modules(monkeypatch)
    switched = {}

    fake_streamlit.session_state.current_circle_id = 3
    fake_streamlit.session_state.selected_team_id = 31
    fake_streamlit.session_state.team_management_focus_detail = True
    fake_streamlit.switch_page = lambda target: switched.setdefault("target", target)

    team_module.open_public_profile(31)

    assert fake_streamlit.session_state.public_profile_return_page == "pages/team_management.py"
    assert fake_streamlit.session_state.public_profile_return_label == "Back to Team Management"
    assert fake_streamlit.session_state.public_profile_target_user_id == 31
    assert fake_streamlit.session_state.public_profile_return_context == {
        "current_circle_id": 3,
        "selected_team_id": 31,
        "team_management_focus_detail": True,
    }
    assert fake_streamlit.query_params["user_id"] == "31"
    assert switched["target"] == "pages/public_profile.py"


def test_get_stored_user_matches_only_returns_results_for_selected_team(monkeypatch):
    fake_streamlit, _, _, team_module = load_team_modules(monkeypatch)
    fake_streamlit.session_state.matching_selected_team_id = 9
    fake_streamlit.session_state.matching_user_results = [{"user_id": 3, "username": "carol"}]

    assert team_module.get_stored_user_matches(9) == [{"user_id": 3, "username": "carol"}]
    assert team_module.get_stored_user_matches(8) == []


def test_mock_join_request_flow_allows_creator_approval(monkeypatch):
    fake_streamlit, api_module, _, _ = load_team_modules(monkeypatch)
    fake_streamlit.session_state.logged_in = True
    fake_streamlit.session_state.mock_teams = {
        1: [
            {
                "id": 8,
                "name": "Systems Team",
                "description": "Need another member",
                "max_members": 3,
                "current_members": 1,
                "status": "Recruiting",
                "creator_id": 1,
                "circle_id": 1,
                "member_ids": [1],
            }
        ]
    }
    fake_streamlit.session_state.mock_invitations = []

    fake_streamlit.session_state.user_id = 4
    request_response = api_module.api_client.post("/teams/8/request-join")

    assert request_response.status_code == 201
    assert request_response.json()["kind"] == "join_request"
    assert request_response.json()["inviter_id"] == 4
    assert request_response.json()["invitee_id"] == 1

    fake_streamlit.session_state.user_id = 1
    creator_inbox = api_module.api_client.get("/invitations").json()
    assert any(item["kind"] == "join_request" and item["team_id"] == 8 for item in creator_inbox)

    approve_response = api_module.api_client.post(
        f"/invitations/{request_response.json()['id']}/respond",
        data={"accept": True},
    )

    assert approve_response.status_code == 200
    assert approve_response.json()["success"] is True
    assert fake_streamlit.session_state.mock_teams[1][0]["member_ids"] == [1, 4]


def test_request_join_helper_uses_join_request_endpoint(monkeypatch):
    _, _, _, team_module = load_team_modules(monkeypatch)
    captured = {}

    class DummyResponse:
        ok = True
        reason = "OK"

        def json(self):
            return {"message": "Join request sent.", "status": "pending", "kind": "join_request"}

    def fake_post(endpoint, data=None, params=None):
        captured["endpoint"] = endpoint
        captured["data"] = data
        return DummyResponse()

    team_module.api_client.post = fake_post

    success, message = team_module.request_to_join_team(12)

    assert success is True
    assert message == "Join request sent."
    assert captured["endpoint"] == "/teams/12/request-join"
    assert captured["data"] is None


def test_fetch_member_tags_uses_member_tags_endpoint(monkeypatch):
    _, _, _, team_module = load_team_modules(monkeypatch)
    captured = {}

    class DummyResponse:
        ok = True
        reason = "OK"

        def json(self):
            return [{"tag_name": "Tech Stack", "value": '["Python", "SQL"]'}]

    def fake_get(endpoint, params=None):
        captured["endpoint"] = endpoint
        return DummyResponse()

    team_module.api_client.get = fake_get

    payload = team_module.fetch_member_tags(6, 12)

    assert payload == [{"tag_name": "Tech Stack", "value": '["Python", "SQL"]'}]
    assert captured["endpoint"] == "/circles/6/members/12/tags"


def test_split_invitations_for_management_keeps_join_request_buckets_separate(monkeypatch):
    _, _, _, team_module = load_team_modules(monkeypatch)

    invitations = [
        {"id": 1, "kind": "invite", "invitee_id": 7, "inviter_id": 2, "status": "pending"},
        {"id": 2, "kind": "join_request", "invitee_id": 7, "inviter_id": 3, "status": "pending"},
        {"id": 3, "kind": "join_request", "invitee_id": 5, "inviter_id": 7, "status": "pending"},
        {"id": 4, "kind": "join_request", "invitee_id": 7, "inviter_id": 4, "status": "accepted"},
    ]

    pending, pending_requests, outgoing_requests, processed = team_module.split_invitations_for_management(
        invitations,
        user_id=7,
    )

    assert [item["id"] for item in pending] == [1]
    assert [item["id"] for item in pending_requests] == [2]
    assert [item["id"] for item in outgoing_requests] == [3]
    assert [item["id"] for item in processed] == [4]

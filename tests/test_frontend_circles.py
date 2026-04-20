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


def load_circle_modules(monkeypatch):
    for name in [
        "frontend.pages.circles",
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
        "form": lambda *args, **kwargs: None,
        "form_submit_button": lambda *args, **kwargs: False,
        "text_input": lambda *args, **kwargs: "",
        "text_area": lambda *args, **kwargs: "",
        "selectbox": lambda label, options, **kwargs: options[0] if options else None,
        "multiselect": lambda *args, **kwargs: [],
        "number_input": lambda *args, **kwargs: 0,
        "checkbox": lambda *args, **kwargs: False,
        "caption": lambda *args, **kwargs: None,
        "write": lambda *args, **kwargs: None,
        "avatar": lambda *args, **kwargs: None,
    }
    for attr_name, value in fake_streamlit_attrs.items():
        setattr(fake_streamlit, attr_name, value)

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setenv("MOCK_MODE", "false")
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:8000")

    circles_module = importlib.import_module("frontend.pages.circles")
    detail_module = importlib.import_module("frontend.views.circle_detail")
    return fake_streamlit, circles_module, detail_module


def test_create_circle_does_not_send_creator_id_query_param(monkeypatch):
    _, circles_module, _ = load_circle_modules(monkeypatch)

    class Response:
        ok = True
        reason = "OK"
        def json(self):
            return {"id": 9}

    captured = {}

    def fake_post(endpoint, data=None, params=None):
        captured["endpoint"] = endpoint
        captured["data"] = data
        captured["params"] = params
        return Response()

    monkeypatch.setattr(circles_module, "get_current_user", lambda: {"id": 42})
    monkeypatch.setattr(circles_module.api_client, "post", fake_post)

    success, message, circle_id = circles_module.create_circle("AI Circle", "desc", "Course")

    assert success is True
    assert message == "Circle created successfully!"
    assert circle_id == 9
    assert captured["endpoint"] == "/circles/"
    assert captured["params"] is None


def test_create_circle_success_message_can_be_shown_without_detail_navigation(monkeypatch):
    fake_streamlit, circles_module, _ = load_circle_modules(monkeypatch)

    class Response:
        ok = True
        reason = "OK"

        def json(self):
            return {"id": 9, "name": "AI Circle"}

    monkeypatch.setattr(circles_module, "get_current_user", lambda: {"id": 42})
    monkeypatch.setattr(circles_module.api_client, "post", lambda *args, **kwargs: Response())

    success, message, circle_id = circles_module.create_circle("AI Circle", "desc", "Course")

    assert success is True
    assert message == "Circle created successfully!"
    assert circle_id == 9
    assert "circle_create_success_message" not in fake_streamlit.session_state


def test_prepare_circle_detail_navigation_sets_detail_focus(monkeypatch):
    fake_streamlit, circles_module, _ = load_circle_modules(monkeypatch)

    circles_module.prepare_circle_detail_navigation(12)

    assert fake_streamlit.session_state.selected_circle_id == 12
    assert fake_streamlit.session_state.current_circle_id == 12
    assert fake_streamlit.session_state.circle_hall_focus_detail is True


def test_view_circle_detail_triggers_immediate_rerun(monkeypatch):
    fake_streamlit, circles_module, _ = load_circle_modules(monkeypatch)
    rerun_called = {"value": False}

    def fake_rerun():
        rerun_called["value"] = True

    fake_streamlit.rerun = fake_rerun

    circles_module.view_circle_detail(18)

    assert fake_streamlit.session_state.selected_circle_id == 18
    assert fake_streamlit.session_state.circle_hall_focus_detail is True
    assert rerun_called["value"] is True


def test_submit_member_tags_does_not_send_current_user_id_query_param(monkeypatch):
    _, _, detail_module = load_circle_modules(monkeypatch)

    class Response:
        ok = True
        reason = "OK"

    captured_calls = []

    def fake_post(endpoint, data=None, params=None):
        captured_calls.append(
            {"endpoint": endpoint, "data": data, "params": params}
        )
        return Response()

    monkeypatch.setattr(detail_module, "get_current_user", lambda: {"id": 42})
    monkeypatch.setattr(detail_module.api_client, "post", fake_post)

    success, message = detail_module.submit_member_tags(
        7,
        [{"id": 1, "name": "Role", "data_type": "string", "required": True}],
        {"Role": "Backend"},
    )

    assert success is True
    assert message == "Your tags have been updated."
    assert captured_calls == [
        {
            "endpoint": "/circles/7/tags/submit",
            "data": {"tag_definition_id": 1, "value": "Backend"},
            "params": None,
        }
    ]


def test_resolve_circle_id_prefers_session_state(monkeypatch):
    fake_streamlit, _, detail_module = load_circle_modules(monkeypatch)
    fake_streamlit.session_state.selected_circle_id = 9

    assert detail_module.resolve_circle_id({"circle_id": "3"}) == 9


def test_normalize_tag_definition_supports_backend_payload(monkeypatch):
    _, _, detail_module = load_circle_modules(monkeypatch)

    normalized = detail_module.normalize_tag_definition(
        {
            "id": 1,
            "name": "Grade",
            "data_type": "enum",
            "required": True,
            "options": "[\"Freshman\", \"Sophomore\"]",
        }
    )

    assert normalized == {
        "id": 1,
        "name": "Grade",
        "data_type": "enum",
        "required": True,
        "options": ["Freshman", "Sophomore"],
    }


def test_open_public_profile_sets_return_context_and_switches_page(monkeypatch):
    fake_streamlit, _, detail_module = load_circle_modules(monkeypatch)
    switched = {}

    fake_streamlit.session_state.selected_circle_id = 8
    fake_streamlit.session_state.current_circle_id = 8
    fake_streamlit.session_state.circle_hall_focus_detail = True
    fake_streamlit.switch_page = lambda target: switched.setdefault("target", target)

    detail_module.open_public_profile(23)

    assert fake_streamlit.session_state.public_profile_return_page == "pages/circles.py"
    assert fake_streamlit.session_state.public_profile_return_label == "Back to Circle Detail"
    assert fake_streamlit.session_state.public_profile_target_user_id == 23
    assert fake_streamlit.session_state.public_profile_return_context == {
        "selected_circle_id": 8,
        "current_circle_id": 8,
        "circle_hall_focus_detail": True,
    }
    assert fake_streamlit.query_params["user_id"] == "23"
    assert switched["target"] == "pages/public_profile.py"


def test_go_to_circle_hall_clears_detail_state_and_switches_page(monkeypatch):
    fake_streamlit, _, detail_module = load_circle_modules(monkeypatch)
    switched = {}

    fake_streamlit.session_state.circle_hall_focus_detail = True
    fake_streamlit.session_state.selected_circle_id = 8
    fake_streamlit.session_state.current_circle_id = 8
    fake_streamlit.switch_page = lambda target: switched.setdefault("target", target)

    detail_module.go_to_circle_hall()

    assert fake_streamlit.session_state.circle_hall_focus_detail is False
    assert "selected_circle_id" not in fake_streamlit.session_state
    assert "current_circle_id" not in fake_streamlit.session_state
    assert switched["target"] == "pages/circles.py"


def test_build_category_filter_options_uses_dynamic_circle_categories(monkeypatch):
    _, circles_module, _ = load_circle_modules(monkeypatch)

    categories = circles_module.build_category_filter_options(
        [
            {"id": 1, "category": "Course"},
            {"id": 2, "category": "Sports"},
            {"id": 3, "category": "Entertainment"},
            {"id": 4, "category": "Course"},
            {"id": 5, "category": ""},
        ]
    )

    assert categories == ["All", "Course", "Entertainment", "Sports"]


def test_circle_filter_mode_defaults_to_joined(monkeypatch):
    _, circles_module, _ = load_circle_modules(monkeypatch)

    assert circles_module.get_current_circle_filter_mode({}) == "joined"


def test_circle_filter_mode_cycle_rotates_joined_created_all(monkeypatch):
    _, circles_module, _ = load_circle_modules(monkeypatch)

    assert circles_module.advance_circle_filter_mode("joined") == "created"
    assert circles_module.advance_circle_filter_mode("created") == "all"
    assert circles_module.advance_circle_filter_mode("all") == "joined"


def test_filter_circles_by_membership_mode_supports_joined_created_and_all(monkeypatch):
    _, circles_module, _ = load_circle_modules(monkeypatch)
    circles = [
        {"id": 1, "name": "Created", "is_creator": True, "is_member": True},
        {"id": 2, "name": "Joined", "is_creator": False, "is_member": True},
        {"id": 3, "name": "Other", "is_creator": False, "is_member": False},
    ]

    joined = circles_module.filter_circles_by_membership_mode(circles, "joined")
    created = circles_module.filter_circles_by_membership_mode(circles, "created")
    all_circles = circles_module.filter_circles_by_membership_mode(circles, "all")

    assert [circle["id"] for circle in joined] == [1, 2]
    assert [circle["id"] for circle in created] == [1]
    assert [circle["id"] for circle in all_circles] == [1, 2, 3]


def test_circle_filter_mode_labels_match_current_state(monkeypatch):
    _, circles_module, _ = load_circle_modules(monkeypatch)

    assert circles_module.get_circle_filter_button_label("joined") == "Created by Me"
    assert circles_module.get_circle_filter_button_label("created") == "All Circles"
    assert circles_module.get_circle_filter_button_label("all") == "Joined Circles"
    assert circles_module.get_circle_list_heading("joined") == "Joined Circles"
    assert circles_module.get_circle_list_heading("created") == "Created by Me"
    assert circles_module.get_circle_list_heading("all") == "Available Circles"

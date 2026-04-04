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
        "frontend.pages.circle_detail",
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
    detail_module = importlib.import_module("frontend.pages.circle_detail")
    return fake_streamlit, circles_module, detail_module


def test_create_circle_sends_creator_id_query_param(monkeypatch):
    _, circles_module, _ = load_circle_modules(monkeypatch)

    class Response:
        ok = True
        reason = "OK"

    captured = {}

    def fake_post(endpoint, data=None, params=None):
        captured["endpoint"] = endpoint
        captured["data"] = data
        captured["params"] = params
        return Response()

    monkeypatch.setattr(circles_module, "get_current_user", lambda: {"id": 42})
    monkeypatch.setattr(circles_module.api_client, "post", fake_post)

    success, message = circles_module.create_circle("AI Circle", "desc", "Course")

    assert success is True
    assert message == "Circle created successfully!"
    assert captured["endpoint"] == "/circles"
    assert captured["params"] == {"creator_id": 42}


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

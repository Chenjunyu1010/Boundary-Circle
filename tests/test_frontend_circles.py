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
        "frontend.pages.2_Circles",
        "frontend.pages.3_Circle_Detail",
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
    fake_streamlit.page_link = lambda *args, **kwargs: None
    fake_streamlit.columns = lambda *args, **kwargs: (None, None)
    fake_streamlit.container = lambda *args, **kwargs: None
    fake_streamlit.button = lambda *args, **kwargs: False
    fake_streamlit.rerun = lambda: None
    fake_streamlit.form = lambda *args, **kwargs: None
    fake_streamlit.form_submit_button = lambda *args, **kwargs: False
    fake_streamlit.text_input = lambda *args, **kwargs: ""
    fake_streamlit.text_area = lambda *args, **kwargs: ""
    fake_streamlit.selectbox = lambda label, options, **kwargs: options[0] if options else None
    fake_streamlit.multiselect = lambda *args, **kwargs: []
    fake_streamlit.number_input = lambda *args, **kwargs: 0
    fake_streamlit.checkbox = lambda *args, **kwargs: False
    fake_streamlit.caption = lambda *args, **kwargs: None
    fake_streamlit.write = lambda *args, **kwargs: None
    fake_streamlit.avatar = lambda *args, **kwargs: None

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setenv("MOCK_MODE", "false")
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:8000")

    circles_module = importlib.import_module("frontend.pages.2_Circles")
    detail_module = importlib.import_module("frontend.pages.3_Circle_Detail")
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

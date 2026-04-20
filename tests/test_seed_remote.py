from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_trigger_admin_seed_calls_seed_endpoint(monkeypatch):
    from scripts import seed_remote

    captured: dict[str, object] = {}

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"action": "seed", "dataset": "stress", "summary": {"users": 48}}

    def fake_post(url, headers=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(seed_remote.requests, "post", fake_post)

    payload = seed_remote.trigger_admin_seed(
        base_url="https://example.up.railway.app",
        admin_key="secret-key",
        dataset="stress",
        reset=False,
    )

    assert captured["url"] == "https://example.up.railway.app/admin/seed?dataset=stress"
    assert captured["headers"] == {"X-Admin-Key": "secret-key"}
    assert captured["timeout"] == 60
    assert payload["action"] == "seed"


def test_trigger_admin_seed_calls_reset_endpoint(monkeypatch):
    from scripts import seed_remote

    captured: dict[str, object] = {}

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"action": "reset", "dataset": "stress", "summary": {"users": 48}}

    def fake_post(url, headers=None, timeout=None):
        captured["url"] = url
        return Response()

    monkeypatch.setattr(seed_remote.requests, "post", fake_post)

    payload = seed_remote.trigger_admin_seed(
        base_url="https://example.up.railway.app/",
        admin_key="secret-key",
        dataset="stress",
        reset=True,
    )

    assert captured["url"] == "https://example.up.railway.app/admin/seed/reset?dataset=stress"
    assert payload["action"] == "reset"

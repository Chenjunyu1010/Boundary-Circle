from __future__ import annotations

import httpx
from typing import TYPE_CHECKING

from src.core.settings import get_settings
from src.services.extraction import (
    FreedomProfileExtractor,
    build_freedom_profile_extractor,
    extract_freedom_profile,
)

if TYPE_CHECKING:
    from collections.abc import Callable


class MockExtractor(FreedomProfileExtractor):
    """Mock extractor for testing - returns deterministic keywords."""

    def __init__(self, keywords: list[str] | None = None):
        super().__init__()
        self._keywords = keywords or []

    def extract_keywords(self, text: str) -> dict[str, list[str]]:
        return {"keywords": self._keywords}


class _CallableExtractor(FreedomProfileExtractor):
    """Callable-based extractor for functional testing."""

    def __init__(self, func: "Callable[[str], dict[str, list[str]]]"):
        self._func = func

    def extract_keywords(self, text: str) -> dict[str, list[str]]:
        return self._func(text)


def test_extract_freedom_profile_returns_normalized_keyword_json() -> None:
    """successful extraction returns normalized keyword JSON"""
    text = "I love Python programming and building web applications with FastAPI."
    extractor = MockExtractor(["python", "fastapi", "web development"])
    result = extract_freedom_profile(text, extractor=extractor)
    assert result is not None
    assert "keywords" in result
    assert isinstance(result["keywords"], list)
    assert len(result["keywords"]) > 0


def test_extract_freedom_profile_blank_text_returns_empty_profile() -> None:
    """blank text returns empty profile"""
    result = extract_freedom_profile("")
    assert result is not None
    assert result.get("keywords") == []


def test_extract_freedom_profile_whitespace_only_returns_empty_profile() -> None:
    """whitespace-only text returns empty profile"""
    result = extract_freedom_profile("   ")
    assert result is not None
    assert result.get("keywords") == []


def test_extract_freedom_profile_malformed_output_falls_back() -> None:
    """malformed LLM output falls back to empty profile"""
    extractor = _CallableExtractor(lambda t: {"invalid_key": ["data"]})
    result = extract_freedom_profile("some text", extractor=extractor)
    assert result is not None
    assert result.get("keywords") == []


def test_extract_freedom_profile_none_extractor_returns_empty_profile() -> None:
    """None extractor returns empty profile"""
    result = extract_freedom_profile("some text", extractor=None)
    assert result is not None
    assert result.get("keywords") == []


def test_extract_freedom_profile_extractor_exception_falls_back() -> None:
    """extractor exception falls back to empty profile"""
    class FailingExtractor(FreedomProfileExtractor):
        def extract_keywords(self, text: str) -> dict[str, list[str]]:
            raise ValueError("Test error")

    extractor = FailingExtractor()
    result = extract_freedom_profile("some text", extractor=extractor)
    assert result is not None
    assert result.get("keywords") == []


def test_extract_freedom_profile_deduplicates_and_caps_keywords() -> None:
    """extractor output is deduplicated and capped at 5 keywords"""
    extractor = MockExtractor(["python", "python", "fastapi", "web", "development", "api", "python"])
    result = extract_freedom_profile("some text", extractor=extractor)
    assert result is not None
    assert "keywords" in result
    assert isinstance(result["keywords"], list)
    # Should be deduplicated and capped at 5
    assert len(result["keywords"]) <= 5
    # Check deduplication - no duplicates
    assert len(set(result["keywords"])) == len(result["keywords"])


def test_extract_freedom_profile_trims_whitespace_from_keywords() -> None:
    """extractor output keywords are trimmed of whitespace"""
    extractor = MockExtractor(["  python  ", " fastapi ", "  web  "])
    result = extract_freedom_profile("some text", extractor=extractor)
    assert result is not None
    assert "keywords" in result
    for keyword in result["keywords"]:
        assert keyword == keyword.strip()


def test_freedom_profile_extractor_default_raises_not_implemented() -> None:
    """default FreedomProfileExtractor raises NotImplementedError"""
    extractor = FreedomProfileExtractor()
    try:
        extractor.extract_keywords("test")
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError:
        pass


def test_build_freedom_profile_extractor_returns_none_without_config(monkeypatch) -> None:
    """factory returns None when no compatible LLM config is present"""
    monkeypatch.setenv("LLM_PROVIDER", "")
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("LLM_MODEL", "")
    monkeypatch.setenv("LLM_BASE_URL", "")
    get_settings.cache_clear()

    extractor = build_freedom_profile_extractor()

    assert extractor is None


def test_build_freedom_profile_extractor_returns_provider_for_openai_compatible(monkeypatch) -> None:
    """factory returns a provider when openai-compatible config is complete"""
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    get_settings.cache_clear()

    extractor = build_freedom_profile_extractor()

    assert extractor is not None
    assert extractor.__class__.__name__ == "OpenAICompatibleFreedomProfileExtractor"


def test_openai_compatible_extractor_parses_chat_completion_response(monkeypatch) -> None:
    """provider extracts keywords from a valid chat completions payload"""
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    get_settings.cache_clear()

    captured: dict[str, object] = {}

    def fake_post(url: str, headers: dict[str, str], json: dict, timeout: float):
        assert url == "https://example.test/v1/chat/completions"
        assert headers["Authorization"] == "Bearer test-key"
        assert json["model"] == "test-model"
        captured["system_prompt"] = json["messages"][0]["content"]
        return httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"keywords": ["python", "fastapi", " ai "]}',
                        }
                    }
                ]
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    extractor = build_freedom_profile_extractor()
    result = extract_freedom_profile("I build APIs in Python and FastAPI.", extractor=extractor)

    assert result == {"keywords": ["python", "fastapi", "ai"]}
    assert "Prefer exact wording from the text" in captured["system_prompt"]
    assert "Do not paraphrase into broader concepts" in captured["system_prompt"]
    assert "Do not include items the user explicitly dislikes" in captured["system_prompt"]
    assert "Do not include generic action words" in captured["system_prompt"]


def test_openai_compatible_extractor_falls_back_on_invalid_json(monkeypatch) -> None:
    """provider falls back to empty keywords when assistant content is not valid json"""
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    get_settings.cache_clear()

    def fake_post(url: str, headers: dict[str, str], json: dict, timeout: float):
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": "not-json"}}]},
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    extractor = build_freedom_profile_extractor()
    result = extract_freedom_profile("I build APIs in Python and FastAPI.", extractor=extractor)

    assert result == {"keywords": []}


def test_openai_compatible_extractor_uses_structured_timeout(monkeypatch) -> None:
    """provider should use a structured timeout configuration, not a single short float."""
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    get_settings.cache_clear()

    captured: dict[str, object] = {}

    def fake_post(url: str, headers: dict[str, str], json: dict, timeout):
        captured["timeout"] = timeout
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": '{"keywords": ["python"]}'}}]},
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    extractor = build_freedom_profile_extractor()
    result = extract_freedom_profile("Python", extractor=extractor)

    assert result == {"keywords": ["python"]}
    assert isinstance(captured["timeout"], httpx.Timeout)
    assert captured["timeout"].read >= 60.0


def test_openai_compatible_extractor_retries_once_on_read_timeout(monkeypatch) -> None:
    """provider should retry a transient read timeout and succeed on the second attempt."""
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    get_settings.cache_clear()

    attempts = {"count": 0}

    def fake_post(url: str, headers: dict[str, str], json: dict, timeout):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise httpx.ReadTimeout("timed out")
        return httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": '{"keywords": ["python", "sql"]}'}}]},
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    extractor = build_freedom_profile_extractor()
    result = extract_freedom_profile("Python and SQL", extractor=extractor)

    assert attempts["count"] == 2
    assert result == {"keywords": ["python", "sql"]}

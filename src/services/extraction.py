"""Freedom profile extraction service."""

from __future__ import annotations

import json
from typing import Any

import httpx

from src.core.settings import get_settings


class FreedomProfileExtractor:
    """Abstract base class for freedom profile extractors.

    Subclasses must implement extract_keywords to return a dict with a "keywords" list.
    """

    def extract_keywords(self, text: str) -> dict[str, list[str]]:
        """Extract keywords from text.

        Args:
            text: Input text to extract keywords from.

        Returns:
            Dict with "keywords" key containing list of keyword strings.

        Raises:
            NotImplementedError: This is the base class method.
        """
        raise NotImplementedError


class OpenAICompatibleFreedomProfileExtractor(FreedomProfileExtractor):
    """Keyword extractor backed by an OpenAI-compatible chat completions endpoint."""

    _MAX_ATTEMPTS = 2

    def __init__(self, *, api_key: str, model: str, base_url: str):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    def extract_keywords(self, text: str) -> dict[str, list[str]]:
        response = self._post_chat_completions(text)
        if response.status_code >= 400:
            raise RuntimeError(f"LLM request failed with status {response.status_code}")
        payload = response.json()
        content = _extract_message_content(payload)
        if not content:
            return {"keywords": []}
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            return {"keywords": []}
        keywords = parsed.get("keywords", [])
        if not isinstance(keywords, list):
            return {"keywords": []}
        return _normalize_keywords(keywords)

    def _post_chat_completions(self, text: str) -> httpx.Response:
        timeout = httpx.Timeout(connect=10.0, read=60.0, write=20.0, pool=10.0)
        last_exc: Exception | None = None
        for attempt in range(1, self._MAX_ATTEMPTS + 1):
            try:
                return httpx.post(
                    f"{self._base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._model,
                        "temperature": 0,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "Extract up to 5 short positive keyword phrases from the user text. "
                                    'Return JSON only in the form {"keywords": ["..."]}. '
                                    "Prefer exact wording from the text whenever possible. "
                                    "Do not paraphrase into broader concepts or inferred categories. "
                                    "Do not include items the user explicitly dislikes, rejects, or does not want. "
                                    "Do not include generic action words, vague traits, or filler words such as help, stable, work, or learn. "
                                    "Keep only concrete domains, technologies, roles, or task phrases that reflect positive interest or experience. "
                                    "Keep the output language aligned with the input text. "
                                    "Return an empty array when no confident keyword exists."
                                ),
                            },
                            {
                                "role": "user",
                                "content": text,
                            },
                        ],
                        "response_format": {"type": "json_object"},
                    },
                    timeout=timeout,
                )
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError) as exc:
                last_exc = exc
                if attempt >= self._MAX_ATTEMPTS:
                    raise
        assert last_exc is not None
        raise last_exc


def _extract_message_content(payload: dict[str, Any]) -> str:
    """Extract text content from an OpenAI-compatible chat completion payload."""
    choices = payload.get("choices", [])
    if not isinstance(choices, list) or not choices:
        return ""

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return ""

    message = first_choice.get("message", {})
    if not isinstance(message, dict):
        return ""

    content = message.get("content", "")
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_value = item.get("text")
                if isinstance(text_value, str):
                    text_parts.append(text_value)
        return "".join(text_parts)

    return ""


def _normalize_keywords(keywords: list[str]) -> dict[str, list[str]]:
    """Normalize keywords by trimming, deduping, and capping at 5.

    Args:
        keywords: List of keyword strings to normalize.

    Returns:
        Dict with "keywords" key containing normalized list (max 5 unique, trimmed keywords).
    """
    seen: set[str] = set()
    deduped: list[str] = []
    for item in keywords:
        if isinstance(item, str):
            trimmed = item.strip()
            if trimmed and trimmed not in seen:
                seen.add(trimmed)
                deduped.append(trimmed)
                if len(deduped) >= 5:
                    break
    return {"keywords": deduped}


def extract_freedom_profile(
    text: str | None,
    extractor: FreedomProfileExtractor | None = None,
) -> dict[str, list[str]]:
    """Extract a freedom profile from text.

    Args:
        text: Input text to extract keywords from. If blank or None, returns empty profile.
        extractor: Extractor instance to use. If None, returns empty profile.

    Returns:
        Dict with "keywords" key containing normalized list of up to 5 unique keywords.
        Returns empty profile on any error or malformed output.
    """
    # Handle None or blank text
    if text is None or not text.strip():
        return {"keywords": []}

    # Handle None extractor
    if extractor is None:
        return {"keywords": []}

    try:
        result = extractor.extract_keywords(text)
    except Exception:
        return {"keywords": []}

    # Validate output structure
    if not isinstance(result, dict):
        return {"keywords": []}

    keywords = result.get("keywords")
    if not isinstance(keywords, list):
        return {"keywords": []}

    # Normalize keywords
    return _normalize_keywords(keywords)


def build_freedom_profile_extractor() -> FreedomProfileExtractor | None:
    """Build the configured freedom-profile extractor, if any."""
    settings = get_settings()
    if settings.llm_provider.strip().lower() != "openai_compatible":
        return None
    if not settings.llm_api_key or not settings.llm_model or not settings.llm_base_url:
        return None

    return OpenAICompatibleFreedomProfileExtractor(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
    )

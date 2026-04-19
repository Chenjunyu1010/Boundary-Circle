# OpenAI-Compatible Freedom Tags Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire the existing freedom-tags feature to a real OpenAI-compatible extraction provider while preserving the current fallback behavior.

**Architecture:** Keep the existing extraction abstraction, add a provider factory driven by runtime settings, and inject that factory into the two save paths that currently hardcode `extractor=None`. Matching stays unchanged and continues to consume stored keyword JSON.

**Tech Stack:** FastAPI, SQLModel, httpx, pydantic-settings, pytest

---

### Task 1: Add failing extraction-provider tests

**Files:**
- Modify: `tests/test_extraction_service.py`

**Step 1: Write failing tests for provider factory and response parsing**

Add tests for:

- missing config returns `None`
- configured settings return an OpenAI-compatible extractor
- valid chat-completions payload returns parsed keywords
- malformed JSON response falls back to empty keywords

**Step 2: Run test to verify it fails**

Run: `pytest -v tests/test_extraction_service.py`
Expected: FAIL because the provider factory and concrete extractor do not exist yet.

### Task 2: Add failing API integration tests for configured extraction

**Files:**
- Modify: `tests/test_freedom_tags_api.py`

**Step 1: Write failing tests**

Add tests that monkeypatch the extractor factory in:

- `src.api.circles`
- `src.api.teams`

Use a fake extractor that returns deterministic keywords and assert the API response includes those keywords.

**Step 2: Run test to verify it fails**

Run: `pytest -v tests/test_freedom_tags_api.py`
Expected: FAIL because the API modules do not call the extractor factory yet.

### Task 3: Implement settings and extraction provider

**Files:**
- Modify: `src/core/settings.py`
- Modify: `src/services/extraction.py`

**Step 1: Add runtime settings**

Add:

- `llm_provider: str = ""`
- `llm_api_key: Optional[str] = None`
- `llm_model: Optional[str] = None`
- `llm_base_url: Optional[str] = None`

**Step 2: Add OpenAI-compatible extractor**

Implement:

- `OpenAICompatibleFreedomProfileExtractor`
- `_extract_message_content(...)`
- `build_freedom_profile_extractor()`

**Step 3: Run extraction tests**

Run: `pytest -v tests/test_extraction_service.py`
Expected: PASS

### Task 4: Inject provider into save paths

**Files:**
- Modify: `src/api/circles.py`
- Modify: `src/api/teams.py`

**Step 1: Replace hardcoded `extractor=None`**

Use `build_freedom_profile_extractor()` in both save paths.

**Step 2: Run API tests**

Run: `pytest -v tests/test_freedom_tags_api.py`
Expected: PASS

### Task 5: Run focused regression

**Files:**
- No code changes expected

**Step 1: Run the focused suite**

Run:

```bash
pytest -v tests/test_freedom_tags_models.py tests/test_extraction_service.py tests/test_freedom_tags_api.py tests/test_matching_freedom_tags.py tests/test_frontend_freedom_tags.py
```

Expected: PASS

**Step 2: Commit**

```bash
git add src/core/settings.py src/services/extraction.py src/api/circles.py src/api/teams.py tests/test_extraction_service.py tests/test_freedom_tags_api.py docs/plans/2026-04-18-openai-compatible-freedom-tags-design.md docs/plans/2026-04-18-openai-compatible-freedom-tags-implementation.md
git commit -m "feat: add openai compatible freedom tag extraction"
```

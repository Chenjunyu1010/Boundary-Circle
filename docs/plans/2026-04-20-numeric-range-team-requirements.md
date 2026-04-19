# Numeric Range Team Requirements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace exact-match numeric team requirements with closed-range requirements for `integer` and `float` tags.

**Architecture:** Keep user numeric circle tags as scalar values, but encode numeric team rules as `{min, max}` dictionaries. Frontend emits the structured payload, and backend matching interprets it as a closed interval while preserving backward compatibility for older scalar numeric rules.

**Tech Stack:** Python, FastAPI, SQLModel, Streamlit, pytest

---

### Task 1: Lock range behavior with tests

**Files:**
- Modify: `tests/test_frontend_teams.py`
- Modify: `tests/test_matching_service.py`
- Modify: `tests/test_matching_api.py`

**Step 1: Write the failing test**

- Add frontend assertions that numeric team rules serialize to `{min, max}`.
- Add service assertions that numeric values match inside the configured range.
- Add API assertions that matching endpoints respect numeric range rules.

**Step 2: Run test to verify it fails**

Run: `pytest -v tests/test_frontend_teams.py tests/test_matching_service.py tests/test_matching_api.py`

**Step 3: Write minimal implementation**

- Update UI helpers and backend matching.

**Step 4: Run test to verify it passes**

Run: `pytest -v tests/test_frontend_teams.py tests/test_matching_service.py tests/test_matching_api.py`

**Step 5: Commit**

```bash
git add docs/plans/2026-04-20-numeric-range-team-requirements-design.md docs/plans/2026-04-20-numeric-range-team-requirements.md tests/test_frontend_teams.py tests/test_matching_service.py tests/test_matching_api.py frontend/pages/team_management.py src/models/teams.py src/services/matching.py
git commit -m "feat: support numeric team requirement ranges"
```

### Task 2: Update team creation UI and payload formatting

**Files:**
- Modify: `frontend/pages/team_management.py`

**Step 1: Write the failing test**

- Add a test for numeric range normalization and caption formatting.

**Step 2: Run test to verify it fails**

Run: `pytest -v tests/test_frontend_teams.py`

**Step 3: Write minimal implementation**

- Add numeric range helpers.
- Render `Min ~ Max` inputs for `integer` and `float`.
- Validate open-ended ranges and reject `min > max`.

**Step 4: Run test to verify it passes**

Run: `pytest -v tests/test_frontend_teams.py`

**Step 5: Commit**

```bash
git add frontend/pages/team_management.py tests/test_frontend_teams.py
git commit -m "feat: add numeric range inputs to team requirements"
```

### Task 3: Update matching semantics

**Files:**
- Modify: `src/models/teams.py`
- Modify: `src/services/matching.py`
- Modify: `tests/test_matching_service.py`
- Modify: `tests/test_matching_api.py`

**Step 1: Write the failing test**

- Add service and API tests for closed-interval behavior and backward compatibility.

**Step 2: Run test to verify it fails**

Run: `pytest -v tests/test_matching_service.py tests/test_matching_api.py`

**Step 3: Write minimal implementation**

- Expand the rule schema type to accept numeric range dicts.
- Match user numeric scalar values against the range.

**Step 4: Run test to verify it passes**

Run: `pytest -v tests/test_matching_service.py tests/test_matching_api.py`

**Step 5: Commit**

```bash
git add src/models/teams.py src/services/matching.py tests/test_matching_service.py tests/test_matching_api.py
git commit -m "feat: match numeric team rules by range"
```

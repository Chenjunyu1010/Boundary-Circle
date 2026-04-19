# Strict Auth Boundaries Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove query-parameter identity spoofing from circle and tag flows and require Bearer authentication end-to-end.

**Architecture:** Move circle creation and tag ownership checks onto `get_current_user`, then update every frontend caller and test to use the existing Authorization header path. Keep route URLs stable while deleting the legacy identity-query contract so unauthorized requests fail fast with `401`.

**Tech Stack:** FastAPI, SQLModel, Streamlit, pytest, TestClient

---

### Task 1: Add red tests for strict Bearer-only circle creation

**Files:**
- Modify: `tests/test_api.py`

**Step 1: Write the failing test**
- Add one test that calls `POST /circles` without a token and asserts `401`.
- Add one test that calls `POST /circles?creator_id=<other>` without a token and asserts `401`.

**Step 2: Run test to verify it fails**
- Run: `pytest tests/test_api.py -k circles -v`
- Expected: at least one new test fails because the endpoint still accepts query-param identity.

**Step 3: Write minimal implementation**
- Update `src/api/circles.py` to depend on `get_current_user` and derive creator ID from the authenticated user.

**Step 4: Run test to verify it passes**
- Run: `pytest tests/test_api.py -k circles -v`
- Expected: the new circle-auth tests pass.

### Task 2: Add red tests for strict Bearer-only tag actions

**Files:**
- Modify: `tests/test_tags_api.py`

**Step 1: Write the failing test**
- Add tests that unauthenticated tag-definition creation and tag submission return `401`.
- Add one test that passes `current_user_id` in the query string without a token and still gets `401`.
- Add one authenticated happy-path test using Bearer headers instead of query params.

**Step 2: Run test to verify it fails**
- Run: `pytest tests/test_tags_api.py -v`
- Expected: the new auth tests fail because the endpoint still trusts query params.

**Step 3: Write minimal implementation**
- Update `src/api/tags.py` to use `get_current_user` for creator and submitter identity.

**Step 4: Run test to verify it passes**
- Run: `pytest tests/test_tags_api.py -v`
- Expected: all tag API tests pass.

### Task 3: Update frontend callers to the new contract

**Files:**
- Modify: `frontend/pages/circles.py`
- Modify: `frontend/views/circle_detail.py`

**Step 1: Write the failing test**
- Extend or add frontend-facing tests for code paths that should no longer append `creator_id/current_user_id`.

**Step 2: Run test to verify it fails**
- Run: `pytest tests/test_frontend_circles.py tests/test_frontend_auth.py tests/test_frontend_teams.py -v`
- Expected: frontend tests fail until requests stop sending removed query params.

**Step 3: Write minimal implementation**
- Remove identity query params from frontend API calls.
- Keep using the existing `Authorization` header from `frontend/utils/api.py`.

**Step 4: Run test to verify it passes**
- Run: `pytest tests/test_frontend_circles.py tests/test_frontend_auth.py tests/test_frontend_teams.py -v`
- Expected: relevant frontend tests pass.

### Task 4: Verify integrated behavior and regressions

**Files:**
- Modify as needed based on failing assertions

**Step 1: Run focused integration tests**
- Run: `pytest tests/test_auth_api.py tests/test_api.py tests/test_tags_api.py tests/test_team_integration.py -v`

**Step 2: Fix minimal regressions**
- Adjust only the affected routes/tests if any regressions remain.

**Step 3: Run the full suite**
- Run: `pytest -q`
- Expected: full suite passes.

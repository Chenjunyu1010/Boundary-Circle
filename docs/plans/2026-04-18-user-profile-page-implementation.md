# User Profile Page Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a dedicated user profile data model, profile APIs, and a Streamlit profile page with field-level visibility controls.

**Architecture:** Keep `full_name` and `email` on `User`, add a one-to-one `UserProfile` model for `gender`, `birthday`, `bio`, and all `show_*` flags, then compose profile responses from both tables. Expose self-read/update APIs plus a filtered public-read API, and add a dedicated frontend page for self-service profile editing.

**Tech Stack:** FastAPI, SQLModel, SQLite, Streamlit, pytest

---

### Task 1: Add backend regression tests for profile APIs

**Files:**
- Create: `tests/test_profile_api.py`
- Modify: `tests/conftest.py` if model registration requires imports

**Step 1: Write the failing test**

Add tests for:
- `GET /profile/me` returns default profile values for a user with no `UserProfile` row
- `PUT /profile/me` creates or updates the profile row and persists visibility flags
- `GET /users/{user_id}/profile` hides fields when `show_*` is `False`
- invalid `gender`, invalid `birthday`, and overlong `bio` are rejected

**Step 2: Run test to verify it fails**

Run: `pytest -v tests/test_profile_api.py`
Expected: FAIL because profile routes and profile model do not exist yet.

**Step 3: Write minimal implementation**

Add `UserProfile` model, profile schemas, and profile routes to satisfy the new tests.

**Step 4: Run test to verify it passes**

Run: `pytest -v tests/test_profile_api.py`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_profile_api.py src/models src/api src/main.py src/db/database.py
git commit -m "feat: add profile APIs"
```

### Task 2: Add dedicated profile storage and API composition

**Files:**
- Create: `src/api/profile.py`
- Create: `src/models/profile.py`
- Modify: `src/main.py`
- Modify: `src/db/database.py`

**Step 1: Write the failing test**

Use Task 1 tests as the red phase. Do not write production code before the route tests fail for the correct reason.

**Step 2: Run test to verify it fails**

Run: `pytest -v tests/test_profile_api.py`
Expected: route-not-found or import/model failures tied to the missing feature.

**Step 3: Write minimal implementation**

Implement:
- `UserProfile` SQLModel table with `user_id`, `gender`, `birthday`, `bio`, and `show_*`
- helper logic to return default profile values when no row exists
- `GET /profile/me`
- `PUT /profile/me`
- `GET /users/{user_id}/profile`
- model registration in app startup

**Step 4: Run test to verify it passes**

Run: `pytest -v tests/test_profile_api.py`
Expected: PASS

**Step 5: Commit**

```bash
git add src/api/profile.py src/models/profile.py src/main.py src/db/database.py
git commit -m "feat: add user profile model and routes"
```

### Task 3: Add frontend profile page and home-page navigation updates

**Files:**
- Create: `frontend/pages/profile.py`
- Modify: `frontend/Home.py`
- Modify: `frontend/utils/api.py`
- Modify: `frontend/utils/auth.py`
- Test: `tests/test_frontend_auth.py`

**Step 1: Write the failing test**

Add frontend-oriented tests for:
- auth/session utilities preserving `full_name` if returned
- mock API support for `/profile/me`
- profile page helper logic if extracted into testable functions

**Step 2: Run test to verify it fails**

Run: `pytest -v tests/test_frontend_auth.py`
Expected: FAIL because profile helpers or mock endpoints are missing.

**Step 3: Write minimal implementation**

Implement:
- `frontend/pages/profile.py` for self-view editing
- `/profile/me` mock GET/PUT support in `frontend/utils/api.py`
- session-state support for `full_name`
- `Home.py` navigation link to the profile page and removal of the home-page-as-profile pattern

**Step 4: Run test to verify it passes**

Run: `pytest -v tests/test_frontend_auth.py`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/Home.py frontend/pages/profile.py frontend/utils/api.py frontend/utils/auth.py tests/test_frontend_auth.py
git commit -m "feat: add frontend profile page"
```

### Task 4: Update seed data and profile-related consistency checks

**Files:**
- Modify: `scripts/seed_data.py`
- Modify: `tests/test_seed_data.py`
- Modify: `tests/test_seed_consistency.py`

**Step 1: Write the failing test**

Add assertions that seeded users have profile rows or equivalent profile data coverage for:
- `gender`
- `birthday`
- `bio`
- visibility flags

**Step 2: Run test to verify it fails**

Run: `pytest -v tests/test_seed_data.py tests/test_seed_consistency.py`
Expected: FAIL because seed profile data is not yet created.

**Step 3: Write minimal implementation**

Extend seed blueprints to include profile metadata and create `UserProfile` rows for seeded users.

**Step 4: Run test to verify it passes**

Run: `pytest -v tests/test_seed_data.py tests/test_seed_consistency.py`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/seed_data.py tests/test_seed_data.py tests/test_seed_consistency.py
git commit -m "test: seed profile data for sample users"
```

### Task 5: Run focused end-to-end verification

**Files:**
- Modify as needed based on failures found in verification

**Step 1: Run focused backend and frontend verification**

Run: `pytest -v tests/test_profile_api.py tests/test_frontend_auth.py tests/test_seed_data.py tests/test_seed_consistency.py tests/test_auth_api.py`

Expected: PASS

**Step 2: Run broader regression checks touching auth and teams**

Run: `pytest -v tests/test_api.py tests/test_integration.py tests/test_seed_integration.py`

Expected: PASS, or report exact failures before any completion claim.

**Step 3: Commit**

```bash
git add .
git commit -m "feat: add dedicated user profile page"
```

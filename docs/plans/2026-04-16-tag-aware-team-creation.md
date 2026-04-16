# Tag-Aware Team Creation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make circle tag definitions drive both member tag submission and team creation so selection-style fields are controlled by the circle schema instead of hard-coded frontend options.

**Architecture:** Extend tag definitions to express `single_select` and `multi_select` fields with pre-defined options and optional selection limits. Keep backend validation authoritative, then update frontend normalization and form rendering to consume the same schema for both member tags and team creation.

**Tech Stack:** FastAPI, SQLModel, Streamlit, pytest

---

### Task 1: Extend tag definition schema for controlled selection fields

**Files:**
- Modify: `src/models/tags.py`
- Test: `tests/test_tags_api.py`

**Step 1: Write the failing test**

Add tests that create:

- a `single_select` tag definition with valid options
- a `multi_select` tag definition with valid options and `max_selections`
- an invalid selection-style definition without options

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_tags_api.py -v`

Expected: FAIL because the schema does not yet support the new selection types or `max_selections`.

**Step 3: Write minimal implementation**

Update `TagDataType` and tag definition schemas in `src/models/tags.py`:

- add `SINGLE_SELECT`
- add `MULTI_SELECT`
- add `max_selections: Optional[int]`

Keep `options` stored as JSON text for now.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_tags_api.py -v`

Expected: PASS for the new schema-related tests.

**Step 5: Commit**

```bash
git add src/models/tags.py tests/test_tags_api.py
git commit -m "feat: extend tag definition schema for selection fields"
```

### Task 2: Make backend tag validation schema-aware

**Files:**
- Modify: `src/api/tags.py`
- Test: `tests/test_tags_api.py`

**Step 1: Write the failing test**

Add tests for:

- valid `single_select` member tag submission
- invalid `single_select` member tag submission outside configured options
- valid `multi_select` member tag submission
- invalid `multi_select` submission when selection count exceeds `max_selections`

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_tags_api.py -v`

Expected: FAIL because current validation only understands primitive values and legacy `enum`.

**Step 3: Write minimal implementation**

Update `src/api/tags.py` to:

- validate selection definitions on create/update
- parse submitted multi-select values as JSON arrays
- verify every selected item exists in configured options
- reject payloads that exceed `max_selections`
- preserve existing validation for integer, float, and boolean tags

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_tags_api.py -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/api/tags.py tests/test_tags_api.py
git commit -m "feat: validate selection-style tag values"
```

### Task 3: Normalize and render the new tag schema in circle detail forms

**Files:**
- Modify: `frontend/views/circle_detail.py`
- Test: `tests/test_frontend_auth.py`

**Step 1: Write the failing test**

Add or extend helper-focused tests that prove:

- `single_select` definitions render as a selectbox-compatible shape
- `multi_select` definitions preserve options and `max_selections`
- normalization handles backend payloads consistently

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_frontend_auth.py -v`

Expected: FAIL because normalization/rendering only supports legacy `string`, `enum`, and loosely defined forms.

**Step 3: Write minimal implementation**

Update `frontend/views/circle_detail.py` to:

- normalize `single_select` and `multi_select`
- carry `max_selections`
- render the correct Streamlit widgets
- show useful validation messaging when a multi-select exceeds the allowed count

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_frontend_auth.py -v`

Expected: PASS for the targeted cases.

**Step 5: Commit**

```bash
git add frontend/views/circle_detail.py tests/test_frontend_auth.py
git commit -m "feat: render questionnaire-style circle tags"
```

### Task 4: Replace hard-coded team creation tags with real circle schema

**Files:**
- Modify: `frontend/pages/team_management.py`
- Modify: `frontend/utils/api.py`
- Test: `tests/test_api.py`

**Step 1: Write the failing test**

Add tests or helper-level assertions covering:

- team creation UI loads tag definitions for the active circle
- schema-driven required-tag inputs replace the hard-coded multiselect
- submitted team requirements are derived from actual tag definitions

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py -v`

Expected: FAIL because team creation currently uses fixed options such as `skill`, `availability`, `role`, `experience`, `interest`.

**Step 3: Write minimal implementation**

Update team creation flow to:

- fetch active circle tag definitions
- normalize them similarly to the circle detail page
- render the proper widget for each tag type
- submit selected requirement values in a backend-compatible form

Keep changes scoped to team creation only; do not redesign team matching in this task.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py -v`

Expected: PASS for the new team-creation-related checks.

**Step 5: Commit**

```bash
git add frontend/pages/team_management.py frontend/utils/api.py tests/test_api.py
git commit -m "feat: drive team creation from circle tag definitions"
```

### Task 5: Update project docs and verify end-to-end

**Files:**
- Modify: `docs/2026-04-15-project-backlog.md`
- Modify: `README.md`

**Step 1: Write the failing test**

No code test here. Define verification commands first.

**Step 2: Run verification before doc updates**

Run:

```bash
pytest tests/test_tags_api.py tests/test_api.py tests/test_frontend_auth.py -v
pytest -q
```

Expected: PASS after the previous tasks are complete.

**Step 3: Write minimal implementation**

Update docs to:

- mark the team creation task as completed when implementation is done
- describe supported selection-style tag types and creator-configured limits

**Step 4: Run verification again**

Run:

```bash
pytest tests/test_tags_api.py tests/test_api.py tests/test_frontend_auth.py -v
pytest -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add docs/2026-04-15-project-backlog.md README.md
git commit -m "docs: record schema-driven team creation"
```

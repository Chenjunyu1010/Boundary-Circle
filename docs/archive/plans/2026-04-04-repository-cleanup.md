# Repository Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Aggressively clean and reorganize the repository so the active backend, frontend, tests, and docs are easier to understand and maintain.

**Architecture:** The active application already has a reasonable split between `src/`, `frontend/`, and `tests/`, but the repository still contains historical files, local runtime artifacts, and outdated documentation. This plan removes clutter, normalizes layout, and updates references without changing the intended runtime architecture.

**Tech Stack:** Git, Python, pytest, FastAPI, Streamlit, filesystem search tools.

---

### Task 1: Clean local/generated artifacts from the workspace

**Files:**
- Remove local artifacts under `.venv/`, `.pytest_cache/`, and all `__pycache__/`
- Review: `boundary_circle.db`
- Review: `.gitignore`

**Step 1: Inspect ignore coverage**

Check whether the repository already ignores:

- `.venv/`
- `.pytest_cache/`
- `__pycache__/`
- `*.pyc`
- `boundary_circle.db` or `*.db`

**Step 2: Update `.gitignore` if needed**

Add missing ignore rules only if they are not already present.

**Step 3: Remove local generated directories from the workspace**

Delete:

- `.venv/`
- `.pytest_cache/`
- all `__pycache__/`

**Step 4: Decide and apply database-file policy**

If `boundary_circle.db` is only local runtime state, remove it from the working tree and ensure it is ignored.

**Step 5: Verify**

Run search/list commands to confirm generated artifacts are gone from the active workspace.

### Task 2: Move and normalize the outlier test file

**Files:**
- Move: `test_circles_join.py` -> `tests/test_circles_join.py`
- Modify if needed: `tests/conftest.py`

**Step 1: Move the file into `tests/`**

Preserve the current test code initially.

**Step 2: Keep fixture isolation intact**

If the moved test still needs file-local fixture control for dependency override restoration, keep that logic inside `tests/test_circles_join.py` rather than forcing premature fixture consolidation.

**Step 3: Search for path-sensitive assumptions**

Check whether any code, docs, or tooling refer specifically to root-level `test_circles_join.py`.

**Step 4: Verify**

Run:

`pytest -v tests/test_circles_join.py`

Expected: PASS.

### Task 3: Remove or archive obsolete demo and historical code more cleanly

**Files:**
- Review/remove: `frontend_demo.py`
- Review/move/remove: `legacy/root_backend/`
- Review/move/remove: `docs/plans/2026-04-04-root-backend-archive*.md`

**Step 1: Confirm `frontend_demo.py` has no active references**

Search docs and code for references.

**Step 2: Remove or archive `frontend_demo.py`**

Preferred default: delete it if fully superseded by `frontend/Home.py` and `frontend/pages/`.

**Step 3: Reassess `legacy/root_backend/`**

Choose one of:

- keep with clearer labeling if historical retention matters,
- move under a documentation/archive convention,
- or delete if the repo no longer needs code-level archival.

Use the least destructive option consistent with the chosen aggressive cleanup.

**Step 4: Reassess temporary planning docs**

If the root-backend archive planning files no longer provide durable value after cleanup, move them to a plan archive location or remove them.

### Task 4: Normalize frontend page naming and references

**Files:**
- Rename: `frontend/pages/1_auth.py`
- Rename: `frontend/pages/2_Circles.py`
- Rename: `frontend/pages/3_Circle_Detail.py`
- Rename: `frontend/pages/4_team_management.py`
- Modify: `frontend/Home.py`
- Modify: any frontend page using `st.page_link()` or `st.switch_page()` with old filenames

**Step 1: Rename pages to a consistent convention**

Recommended targets:

- `frontend/pages/auth.py`
- `frontend/pages/circles.py`
- `frontend/pages/circle_detail.py`
- `frontend/pages/team_management.py`

**Step 2: Update all page references**

Search all of `frontend/` for old filenames and update links/switches/import-adjacent references.

**Step 3: Verify navigation references**

Search again to ensure no old page filenames remain.

### Task 5: Rewrite README and align docs with the cleaned structure

**Files:**
- Modify: `README.md`
- Review: `docs/*.md`

**Step 1: Update local run instructions**

Make README point to the actual frontend command:

`streamlit run frontend/Home.py`

**Step 2: Remove outdated feature and endpoint claims**

Only describe implemented features and currently valid API areas.

**Step 3: Add or refresh structure overview**

Document the cleaned repo layout clearly.

**Step 4: Verify by reading the README as a newcomer**

Confirm the instructions now match the actual codebase.

### Task 6: Full verification and cleanup review

**Files:**
- Whole repository

**Step 1: Run targeted searches**

Confirm:

- no root-level `test_circles_join.py`
- no stale `frontend_demo.py` references if removed
- no stale old frontend page filenames
- no leftover generated artifact directories in active workspace

**Step 2: Run full test suite**

Run:

`pytest -v`

Expected: PASS.

**Step 3: Inspect final git status**

Run:

`git status --short`

Expected: only intentional cleanup/refactor changes remain.

**Step 4: Commit**

```bash
git add -A
git commit -m "refactor: clean and unify repository structure"
```

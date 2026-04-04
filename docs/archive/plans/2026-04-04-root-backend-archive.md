# Root Backend Archive Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Archive the obsolete root-level backend files into `legacy/root_backend/` while preserving the active `src/` backend and keeping tests green.

**Architecture:** The repository currently has one active backend under `src/` and one obsolete backend-like set of files at the root. This plan keeps runtime behavior unchanged by moving only the inactive root backend files into a clearly labeled archive folder, then verifies that no imports or docs were unintentionally broken.

**Tech Stack:** Git, Python, pytest, repository-wide search tools.

---

### Task 1: Prepare the archive location

**Files:**
- Create: `legacy/root_backend/`
- Create: `legacy/root_backend/README.md`

**Step 1: Create the archive directory**

Run: `mkdir legacy\root_backend`

**Step 2: Add a short archive note**

Create `legacy/root_backend/README.md` with content like:

```md
# Archived Root Backend

These files are preserved for reference only.
The active backend lives under `src/`.
```

**Step 3: Verify the directory exists**

Run: `ls legacy\root_backend`
Expected: the directory exists and contains `README.md`

### Task 2: Move the obsolete root backend files

**Files:**
- Modify by move: `main.py`
- Modify by move: `circles.py`
- Modify by move: `teams.py`
- Modify by move: `database.py`
- Modify by move: `models.py`
- Modify by move: `schemas.py`
- Modify by move: `seed_data.py`

**Step 1: Move the files**

Run:

```bash
move main.py legacy\root_backend\main.py && move circles.py legacy\root_backend\circles.py && move teams.py legacy\root_backend\teams.py && move database.py legacy\root_backend\database.py && move models.py legacy\root_backend\models.py && move schemas.py legacy\root_backend\schemas.py && move seed_data.py legacy\root_backend\seed_data.py
```

**Step 2: Verify the root is cleaner**

Run: `ls`
Expected: those seven files are no longer in the repository root.

**Step 3: Verify archive contents**

Run: `ls legacy\root_backend`
Expected: all seven moved files plus `README.md`

### Task 3: Check for broken references after the move

**Files:**
- Inspect references across the repository

**Step 1: Search for old filenames and `app.` imports**

Check for references to:

- `main.py` at the root backend level where relevant
- `circles.py`, `teams.py`, `database.py`, `models.py`, `schemas.py`, `seed_data.py`
- `app.` imports outside the archive directory

**Step 2: If references exist, update only the ones broken by the move**

Do not refactor unrelated code. Only adjust docs or scripts that still point at the archived files.

**Step 3: Re-run search**

Expected: no newly broken active references remain.

### Task 4: Verify behavior stays intact

**Files:**
- Test: `tests/`
- Test: `test_circles_join.py`

**Step 1: Run the full test suite**

Run: `pytest -v`
Expected: PASS

**Step 2: Check git diff**

Run: `git status --short`
Expected: only the archive move, archive note, and any minimal doc/script fixes appear.

**Step 3: Commit**

```bash
git add legacy/root_backend docs/plans/2026-04-04-root-backend-archive-design.md docs/plans/2026-04-04-root-backend-archive.md
git add -A
git commit -m "refactor: archive obsolete root backend files"
```

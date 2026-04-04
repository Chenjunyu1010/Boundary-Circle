# Repository Cleanup Design

**Goal:** Refactor the repository into a cleaner long-term structure by removing generated clutter, consolidating active code into clear top-level areas, eliminating confusing historical leftovers, and aligning documentation with the actual runtime layout.

## Why This Cleanup Is Needed

The repository currently works, but its structure tells multiple conflicting stories at once:

- The active backend lives under `src/`, but historical backend code still exists under `legacy/root_backend/`.
- The active frontend lives under `frontend/`, but `README.md` still tells contributors to run `frontend_demo.py`.
- Most tests live under `tests/`, but `test_circles_join.py` still lives at the repository root.
- Generated and local-only artifacts such as `.venv/`, `__pycache__/`, `.pytest_cache/`, and `boundary_circle.db` make the repository feel like a working directory instead of a clean project root.
- The frontend page naming scheme mixes numbering and inconsistent casing, which makes the UI tree harder to read and maintain.

This is not just a cosmetic issue. The current layout makes onboarding slower and increases the chance that future contributors will edit the wrong files or follow outdated run instructions.

## Chosen Scope: Aggressive Cleanup

This pass should do more than remove junk files. It should reshape the repository into a structure that clearly communicates which files are active, which are historical, and how the app is meant to be run.

The cleanup includes:

- Removing local/generated artifacts from the repository workspace and hardening ignore rules if needed.
- Moving `test_circles_join.py` into `tests/` and unifying test layout.
- Deciding whether `frontend_demo.py` should be deleted or archived; default recommendation is delete unless it still provides unique value.
- Renaming Streamlit pages to a cleaner, consistent naming scheme.
- Updating internal references that depend on those page filenames.
- Reassessing whether `legacy/root_backend/` should remain as a code archive or move to a more documentation-like archive location.
- Updating `README.md` so the run instructions and architecture description match the actual repository.
- Trimming temporary plan documents once the cleanup they describe is complete, if they no longer add durable value.

## Target Repository Shape

After cleanup, the repository should communicate this structure clearly:

- `src/` — active FastAPI backend
- `frontend/` — active Streamlit frontend
- `tests/` — all automated tests
- `docs/` — durable documentation only
- `README.md`, `Dockerfile`, `requirements.txt`, `agents.md` — project-level files only

Everything else should either be:

- deleted as generated/local state,
- merged into one of the areas above,
- or explicitly archived with a strong reason to keep it.

## Proposed Cleanup Decisions

### 1. Generated and Local-Only Artifacts

Remove from the workspace and keep ignored:

- `.venv/`
- `.pytest_cache/`
- every `__pycache__/`
- Python bytecode files

`boundary_circle.db` needs a policy decision in the implementation:

- If it is only local runtime state, remove it from versioned workspace and ignore it.
- If the project intentionally relies on a checked-in starter database, move it to a clearer data/bootstrap location and document that choice.

The default recommendation is to treat it as local runtime state, not source code.

### 2. Tests

Move `test_circles_join.py` into `tests/test_circles_join.py` and keep its fixture isolation behavior.

The key constraint is that this file currently preserves and restores `app.dependency_overrides` explicitly, while `tests/conftest.py` applies a simpler global override. The move should preserve behavior while reducing structural inconsistency. If needed, this test can keep file-local fixtures inside `tests/test_circles_join.py` rather than forcing everything into `tests/conftest.py` immediately.

### 3. Frontend Structure

The current numbered page names are functional but awkward:

- `frontend/pages/1_auth.py`
- `frontend/pages/2_Circles.py`
- `frontend/pages/3_Circle_Detail.py`
- `frontend/pages/4_team_management.py`

Rename them to a consistent convention, ideally lowercase and descriptive. For example:

- `frontend/pages/auth.py`
- `frontend/pages/circles.py`
- `frontend/pages/circle_detail.py`
- `frontend/pages/team_management.py`

Then update all `st.page_link()` / `st.switch_page()` / string-based page references accordingly.

### 4. Demo and Historical Files

`frontend_demo.py` appears to be a leftover prototype and is currently misleading because `README.md` still points to it. The preferred approach is:

- delete it if it is fully superseded,
- otherwise move it into an explicit archive/demo location with a clear label.

`legacy/root_backend/` should not continue to feel like part of the active codebase. The implementation should decide between:

- keeping it as a temporary archive with clearer documentation, or
- moving it under a documentation/archive convention if the project wants historical preservation without code-level prominence.

### 5. Documentation

`README.md` should be updated to reflect the actual project:

- backend entrypoint: `src.main:app`
- frontend entrypoint: `frontend/Home.py`
- current implemented features only
- current directory structure only

It should stop advertising outdated commands or endpoints that no longer match the codebase.

`docs/plans/` should be reviewed so that only useful durable plans remain. Temporary cleanup planning documents can be removed or moved to an archive subfolder after this refactor is complete.

## Risks and How to Handle Them

- **Page rename risk:** Streamlit page navigation may break if file references are missed.
  - Mitigation: search all `frontend/` files for page filename strings and verify manually.

- **Test move risk:** `test_circles_join.py` may interact unexpectedly with `tests/conftest.py`.
  - Mitigation: move it carefully, preserve local fixture setup, then run the full test suite.

- **Database file policy risk:** deleting `boundary_circle.db` might surprise contributors if they rely on pre-seeded local state.
  - Mitigation: inspect README and current workflows first, then choose explicit local-state handling.

- **Archive deletion risk:** historical files may still be useful as reference.
  - Mitigation: prefer moving/labeling over deleting when historical value is uncertain.

## Verification Criteria

The cleanup is complete when:

- root-level clutter is gone and the repository root only contains intentional project-level files,
- all tests live under `tests/`,
- frontend page names are consistent and navigation still works,
- `README.md` matches the actual runtime entrypoints and structure,
- no generated/local-only artifacts remain as active workspace clutter,
- and `pytest -v` passes after the refactor.

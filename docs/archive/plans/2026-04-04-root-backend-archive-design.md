# Root Backend Archive Design

**Goal:** Remove ambiguity in the repository by separating the active `src/` backend from the obsolete root-level backend files without changing current runtime behavior.

## Current State

The repository contains two backend layouts:

- The active implementation under `src/`, which is the code path covered by the current test suite.
- A second backend-like set of files at the repository root: `main.py`, `circles.py`, `teams.py`, `database.py`, `models.py`, `schemas.py`, and `seed_data.py`.

These root-level files are not aligned with the active project structure. They still import from `app.*`, which does not exist in the current repository layout. This makes the root directory misleading because it looks like there are multiple valid backend entry points when only the `src/` implementation is actually wired into tests and current development.

## Chosen Scope

Use the minimum-risk cleanup:

- Keep the active `src/`, `frontend/`, and `tests/` layout unchanged.
- Do not change runtime entry points, scripts, or frontend code.
- Do not archive `frontend_demo.py` in this pass.
- Move only the obsolete root-level backend files into an archive directory.

## Proposed Structure

Create a dedicated archive location:

- `legacy/root_backend/main.py`
- `legacy/root_backend/circles.py`
- `legacy/root_backend/teams.py`
- `legacy/root_backend/database.py`
- `legacy/root_backend/models.py`
- `legacy/root_backend/schemas.py`
- `legacy/root_backend/seed_data.py`

After this change, the repository root will more clearly communicate the actual architecture:

- `src/` for the backend
- `frontend/` for the Streamlit UI
- `tests/` plus `test_circles_join.py` for tests
- `legacy/` for historical code that is intentionally not active

## Why This Approach

This is safer than deleting the files because it preserves historical reference material while removing ambiguity from the active workspace. It is also much smaller in scope than a full structural refactor, so it avoids accidental breakage in imports, docs, and contributor workflows.

## Risks and Mitigations

- **Risk:** Some documentation or scripts might still reference the root-level files.
  - **Mitigation:** Run repository-wide searches for those filenames and for `app.` imports after the move.
- **Risk:** A move could accidentally affect tests if hidden imports rely on root paths.
  - **Mitigation:** Run the full test suite after the move.
- **Risk:** Contributors may not realize the archive is intentionally inactive.
  - **Mitigation:** Add a short README inside `legacy/root_backend/` explaining that the files are preserved for reference only.

## Verification

The cleanup is complete when all of the following are true:

- The seven obsolete root-level backend files exist only under `legacy/root_backend/`.
- Searches show no broken references introduced by the move.
- `pytest -v` still passes.
- The repository root clearly reflects a single active backend layout.

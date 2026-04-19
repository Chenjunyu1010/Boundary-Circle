# AGENTS.md

This file gives agentic coding tools the repository-specific guidance they need to work safely and predictably in this project.

It is distilled from `CLAUDE.md`, `README.md`, `.github/workflows/ci.yml`, and representative source and test files under `src/`, `frontend/`, and `tests/`.

## Rule Files

- Repo-root `AGENTS.md`: this file.
- Existing `CLAUDE.md`: detailed project guidance for coding agents; keep it aligned with this file.
- Cursor rules: none found in `.cursor/rules/` and no `.cursorrules` file was present when this file was written.
- Copilot rules: no `.github/copilot-instructions.md` file was present when this file was written.

## Environment and Stack

- Python 3.9+
- FastAPI backend in `src/`
- Streamlit frontend in `frontend/`
- SQLite database via SQLModel in `data/boundary_circle.db`
- pytest test suite in `tests/`
- CI runs on GitHub Actions from `.github/workflows/ci.yml`

## High-Value Commands

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the backend from the repository root:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Run the frontend:

```bash
streamlit run frontend/Home.py
```

Run the full test suite:

```bash
pytest -v
```

Run a single test file:

```bash
pytest -v tests/test_matching_api.py
```

Run a single test case:

```bash
pytest -v tests/test_matching_api.py::test_match_users_requires_team_membership
```

Run backend-only coverage:

```bash
pytest --cov=src --cov-report=term-missing
```

Run the same pytest command CI uses:

```bash
mkdir -p test-results
pytest \
  --junitxml=test-results/pytest.xml \
  --cov=src \
  --cov=frontend \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml
```

Build and run Docker:

```bash
docker build -t boundary-circle .
docker run -p 8000:8000 boundary-circle
```

Seed local demo data:

```bash
python scripts/seed_data.py demo
python scripts/seed_data.py stress
python scripts/seed_data.py demo --reset
python scripts/seed_data.py stress --reset
```

## Commands That Do Not Exist Yet

Do not invent repo-wide tooling that is not configured.

- No repo-wide lint command is configured.
- No repo-wide static typecheck command is configured.
- CI currently runs pytest plus coverage only.

If you add linting or typechecking, wire it into the repo explicitly before documenting it as standard workflow.

## Repository Layout

Active code lives here:

- `src/main.py`: FastAPI entrypoint, lifespan, router registration, root and health endpoints
- `src/api/`: feature-based route modules (`auth.py`, `circles.py`, `tags.py`, `teams.py`, `matching.py`, `users.py`, `profile.py`)
- `src/auth/`: token parsing, password hashing, auth dependencies
- `src/core/settings.py`: environment-backed runtime settings
- `src/db/database.py`: SQLModel engine, session dependency, startup DB creation and local schema upgrade helpers
- `src/models/`: SQLModel tables and API-facing schemas, grouped by domain
- `src/services/`: reusable business logic such as matching and user creation
- `frontend/Home.py`: Streamlit multipage root
- `frontend/pages/`: main Streamlit pages
- `frontend/views/`: heavier view composition such as circle detail
- `frontend/utils/`: frontend auth/session and HTTP client helpers
- `tests/`: pytest backend, integration, schema, seed, and frontend tests

Historical code lives under `docs/archive/` and should not be treated as the active implementation.

## Architecture Notes

This project is circle-centric.

Typical flow:

1. Users register and log in.
2. Users create or join circles.
3. Circle creators define tag schemas.
4. Users submit tag values inside a circle.
5. Teams are created within circles.
6. Matching and invitations build on circle membership, team membership, and submitted tag values.

Important implications:

- Many permissions are based on circle membership, team membership, or creator status.
- Matching logic spans `src/api/matching.py` and `src/services/matching.py`.
- Team required tags are stored as JSON text in the team model and encoded/decoded in `src/models/teams.py`.
- The app uses explicit IDs and query logic more than rich ORM relationship traversal.

## Backend Conventions

Follow the existing backend patterns instead of introducing a new style.

- Keep routes in feature modules under `src/api/`, not mixed into `src/main.py`.
- Use FastAPI `APIRouter` and dependency injection for sessions and current-user checks.
- Use Pydantic or SQLModel models for request and response validation.
- Use `HTTPException` with clear status codes and details for API errors.
- Put reusable non-route logic in `src/services/` when it does not belong in a model or router.
- Keep startup wiring in `src/main.py`; it already creates tables on startup.
- Preserve the `/docs` and `/health` behavior unless the task explicitly changes them.

Representative files:

- `src/main.py`
- `src/api/auth.py`
- `src/api/circles.py`
- `src/services/matching.py`
- `src/services/users.py`

## Frontend Conventions

The frontend is a Streamlit app, not a React SPA.

- Prefer the existing page structure under `frontend/pages/`.
- Reuse shared helpers in `frontend/utils/api.py` and `frontend/utils/auth.py`.
- `API_BASE_URL` defaults to `http://127.0.0.1:8000`; do not hardcode alternate URLs into page code.
- `MOCK_MODE` exists as a fallback, but the normal demo path is the real backend.

## Code Style

Python style in this repo is straightforward and should remain consistent.

- Follow PEP 8.
- Use `snake_case` for functions, variables, and module-level helpers.
- Use `PascalCase` for classes and schema/model types.
- Keep imports at the top of the file.
- Match the repo's existing import style: standard library first, then third-party packages, then `src.*` imports.
- Prefer clear, explicit names over abbreviations.
- Add docstrings for public functions; existing entrypoints and settings objects already follow this pattern.
- Keep comments sparse and practical; avoid narrating obvious code.

## Types and Data Modeling

Type discipline matters in this repo.

- Add type annotations to function parameters and return values.
- Use standard typing constructs such as `Optional[...]`, `List[...]`, `Set[...]`, or modern built-in generics where the file already uses them.
- Do not use `Any` unless there is a genuine need and the surrounding code already justifies it.
- Do not use `# type: ignore`.
- Do not use TypeScript-style `as any` or similar suppression patterns.
- Keep SQLModel table models and related API schemas aligned inside the domain model files.

## Error Handling and Security

- Use `HTTPException` for expected API failures.
- Use precise status codes such as 400, 401, 403, 404, or 422 based on the actual failure.
- Do not use empty `except` blocks or `except: pass`.
- Do not hardcode secrets, tokens, or passwords.
- Runtime auth settings come from `src/core/settings.py` and environment variables.
- In production-like environments, `SECRET_KEY` must be configured.
- Authentication is custom: password hashing uses PBKDF2 and auth uses signed bearer tokens.

## Database Rules

- Use SQLModel and the shared session dependency from `src/db/database.py`.
- Do not write raw SQL for normal feature work; use the ORM/query layer.
- Remember that tests override the production DB dependency with in-memory SQLite via `tests/conftest.py`.
- Do not assume Postgres features; the app runs on SQLite.
- Be careful with local schema compatibility: the project includes lightweight SQLite upgrade helpers for older local DB files.

## Testing Expectations

Tests are a first-class part of changes here.

- Put new tests in `tests/`.
- Match the existing pytest naming style: `test_<feature>_<scenario>_<expected_result>` when practical.
- Use fixtures from `tests/conftest.py` rather than creating ad hoc DB bootstrapping in each file.
- For backend changes, add or update route, integration, or model/service tests as appropriate.
- For frontend changes, follow the existing lightweight frontend tests that use fake Streamlit modules instead of a live browser.
- Good end-to-end references: `tests/test_integration.py`, `tests/test_team_integration.py`, `tests/test_circles_join.py`, `tests/test_matching_api.py`.

Before calling work complete, run the smallest relevant test first, then the broader suite if the change touches shared behavior.

## Git and Change Discipline

- Work on feature branches, not directly on `main`.
- Do not force-push to `main` or `master`.
- Use Conventional Commit style when making commits.
- Keep diffs focused; do not mix unrelated refactors into a bug fix.
- Do not delete failing tests just to get a green run.

## Practical Guidance for Agents

- Read the surrounding feature files before editing cross-cutting behavior.
- When changing matching, inspect both the API layer and the service layer.
- When changing team or tag behavior, trace effects through circles, tags, teams, and matching together.
- Prefer extending existing patterns over introducing a new abstraction.
- If a command or workflow is not documented here, `CLAUDE.md`, `README.md`, or CI, verify it before relying on it.

## Test Result Reporting

When reporting completed feature or bug-fix work, use the repository's preferred format:

```text
【测试结果申报】
- Environment: Windows 11, Python 3.9
- Test module: users registration and circle query
- Command: pytest -v
- Result: 20 passed, 0 failed in 0.85s
- Notes: All core boundary conditions covered, no failures
```

Include that information in PR descriptions or commit messages when relevant.

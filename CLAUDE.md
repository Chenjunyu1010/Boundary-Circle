# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development commands

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the FastAPI backend from the repo root:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Run the Streamlit frontend:

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

Run the same pytest command used in CI:

```bash
mkdir -p test-results
pytest \
  --junitxml=test-results/pytest.xml \
  --cov=src \
  --cov=frontend \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml
```

Build and run the Docker image:

```bash
docker build -t boundary-circle .
docker run -p 8000:8000 boundary-circle
```

## Repo-specific notes

- Active code lives in `src/`, `frontend/`, and `tests/`.
- `docs/archive/root_backend/` contains historical backend code and should not be treated as the current implementation.
- Daily development is centered on running `uvicorn` and `streamlit` directly; Docker exists, but the repo docs position it mainly as a demo/deployment artifact.
- The backend creates `data/boundary_circle.db` automatically. Startup table creation happens in `src/main.py` via `create_db_and_tables()`.
- There is no repo-wide lint/typecheck command configured today. CI currently runs pytest + coverage only; do not invent `ruff`, `black`, `mypy`, or `pyright` workflows unless you add and wire them explicitly.

## High-level architecture

### Backend shape

- `src/main.py` is the FastAPI entrypoint. It registers the app lifespan, creates tables on startup, and mounts the feature routers.
- `src/api/` is organized by feature rather than by HTTP verb:
  - `auth.py` handles register/login/current-user.
  - `circles.py` handles circle CRUD plus join/leave.
  - `tags.py` handles tag definition management and per-user tag submission.
  - `teams.py` handles team creation, team listing, invitations, and leave flows.
  - `matching.py` exposes recommendation endpoints.
- `src/db/database.py` provides the shared SQLModel engine/session dependency. The app uses SQLite, not Postgres.

### Auth and permission model

- Authentication is custom and lightweight, not an external auth provider. `src/auth/security.py` implements password hashing with PBKDF2 plus signed bearer tokens.
- Protected endpoints use `src/auth/dependencies.py:get_current_user`, which reads the `Authorization: Bearer ...` header, decodes the token, and loads the current `User` from the database.
- The main authorization boundaries are circle membership and team membership. Many behaviors intentionally enforce "must be a circle member / creator" or "must be a team member / creator" checks before allowing access to team and matching data.

### Data model layout

- Models are split by domain, with table models and API-facing schemas living together in the same files:
  - `src/models/core.py`: users and circles.
  - `src/models/tags.py`: circle membership, tag definitions, and submitted user tags.
  - `src/models/teams.py`: teams, team membership, invitations, and required-tag serialization.
- The codebase mostly uses explicit foreign-key IDs and query logic instead of rich ORM relationship traversal.
- Team required tags are stored as JSON text (`required_tags_json`) and converted with `encode_required_tags()` / `decode_required_tags()` in `src/models/teams.py`.

### Core domain flow

The product flow is circle-centric:

1. Users register/login.
2. Authenticated users create circles or join existing circles.
3. Circles define tag schemas.
4. Users submit tag values within a circle.
5. Teams are created inside a circle, with optional required tags.
6. Invitations and matching operate on top of circle membership, team membership, and submitted tags.

When working on behavior, trace it through `circles.py`, `tags.py`, `teams.py`, and `matching.py` together rather than treating each endpoint in isolation.

### Matching subsystem

- `src/services/matching.py` contains the reusable scoring helpers; `src/api/matching.py` wraps them in API permissions and response models.
- Matching is tag-based and currently uses:
  - coverage of required tags
  - Jaccard similarity across tag-name sets
- Team recommendations exclude locked/full teams and teams the current user already joined.
- User recommendations exclude existing team members and candidates with zero required-tag coverage.

### Frontend shape

- The frontend is a Streamlit multipage app rooted at `frontend/Home.py`.
- `frontend/pages/` contains the main page modules (`auth.py`, `circles.py`, `team_management.py`).
- `frontend/views/circle_detail.py` holds the heavier circle-detail rendering and tag/join flows, which are reused from the circle page.
- `frontend/utils/auth.py` manages login state in `st.session_state`.
- `frontend/utils/api.py` is the HTTP client layer. It adds bearer tokens automatically and supports a `MOCK_MODE` path backed by in-session fake data.
- `API_BASE_URL` defaults to `http://127.0.0.1:8000`; if the frontend is pointed elsewhere, update that environment variable instead of hardcoding URLs.

### Testing strategy

- Tests are all in `tests/` and are pytest-based.
- `tests/conftest.py` overrides the production DB dependency with an in-memory SQLite database using `StaticPool`, so backend tests do not touch `data/boundary_circle.db`.
- Coverage is broad across:
  - API route tests
  - workflow/integration tests
  - model/helper tests
  - frontend module tests using fake Streamlit modules instead of a live browser session
- Good reference tests for end-to-end behavior are `tests/test_integration.py`, `tests/test_team_integration.py`, `tests/test_circles_join.py`, and `tests/test_matching_api.py`.

### Tech stack

| Layer | Technology | Version/Notes |
|-------|------------|---------------|
| Backend | FastAPI | Python 3.9+ |
| Frontend | Streamlit | Prototype stage |
| Database | SQLite | Single file (`data/boundary_circle.db`) |
| ORM | SQLModel | Pydantic + SQLAlchemy combined |
| CI/CD | GitHub Actions | Automated testing |
| Testing | pytest | Unit and integration tests |

---

## Coding standards

### Python style
- Follow **PEP 8** conventions
- Use `snake_case` for functions and variables
- Use `PascalCase` for class names
- All public functions must have docstrings

### FastAPI conventions
- All routes must be in separate modules under `src/api/`
- Use Pydantic models for request/response validation
- All API endpoints should have OpenAPI descriptions
- Error handling uses FastAPI's `HTTPException`

### Type annotations
- **Required**: All function parameters and return values must have type annotations
- Use `typing` module for complex types
- Avoid `Any` type unless absolutely necessary

### Test conventions
- Test files are in `tests/` directory
- Test function naming: `test_<feature>_<scenario>_<expected_result>()`
- Use pytest fixtures for test data setup
- CI must pass all tests

---

## Constraints

### Type safety (BLOCKING)
- Do NOT use `as Any` for type coercion
- Do NOT use `# type: ignore` to suppress type errors

### Code quality
- Do NOT use empty catch blocks `except: pass`
- Do NOT delete failing tests to "pass" CI
- Do NOT commit hardcoded passwords/keys in code
- Do NOT write raw SQL (use ORM or parameterized queries)

### Git workflow
- Do NOT force push to main/master branch
- All feature development must be on feature branches
- Commit messages should follow Conventional Commits format

---

## Development workflow

1. Create feature branch: `git checkout -b feature/<name>`
2. Implement feature + write tests
3. Run local tests: `pytest`
4. Commit code and create PR
5. Wait for CI to pass + code review
6. Merge to main branch

### Code review checklist
- [ ] Code follows PEP 8
- [ ] All functions have type annotations
- [ ] New code has corresponding tests
- [ ] No sensitive information leaked
- [ ] Commit messages are规范

---

## Troubleshooting

### Common errors

**`ModuleNotFoundError: No module named 'src'`**
- Cause: Terminal is not in the project root directory
- Fix: `cd` to the project root before running commands

**API testing (Swagger UI)**
- After starting the server, visit `http://localhost:8000/docs` to test endpoints interactively

---

## Test result reporting

When completing any feature or bug fix, report test results in this format:

```
【测试结果申报】
- Environment: Windows 11, Python 3.9
- Test module: users registration and circle query
- Command: pytest -v
- Result: 20 passed, 0 failed in 0.85s
- Notes: All core boundary conditions covered, no failures
```

This information should be included in PR descriptions or commit messages.

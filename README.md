# Boundary Circle

Boundary Circle is a FastAPI + Streamlit project for circle-based identity, tag submission, and lightweight teammate discovery workflows.

## What is implemented

- User registration, login, and current-user lookup
- Circle creation and browsing
- Per-circle tag definition management
- Per-user tag submission and update flows
- Controlled tag schema with `single_select` and `multi_select` definitions
- Schema-driven team creation that uses real circle tag definitions instead of a fixed frontend tag list
- Value-aware team matching based on structured team requirement rules
- Circle join-related tag workflow coverage in automated tests
- Team creation, invitation, response, and leave flows with backend/API tests
- Matching recommendations for teams and users (backend APIs and Streamlit "Matching" tab)
- Streamlit pages for auth, circle browsing, circle detail, and team-management UI scaffolding

## Project structure

```text
.
|-- src/                # Active FastAPI backend
|   |-- api/
|   |-- auth/
|   |-- db/
|   `-- models/
|-- frontend/           # Active Streamlit frontend
|   |-- pages/
|   `-- utils/
|-- tests/              # Automated test suite
|-- docs/
|   `-- archive/        # Historical plans and archived legacy code
|-- Dockerfile
|-- requirements.txt
`-- agents.md
```

Historical backend files that are no longer active are preserved under `docs/archive/root_backend/`.

## Requirements

- Python 3.9+

## Environment variables

Auth-related configuration is now centralized and should be controlled through environment variables.

Recommended variables:

- `APP_ENV`
  - Use `development` for local work
  - Use `test` for test-specific setups
  - Use `production` for deployment
- `SECRET_KEY`
  - Required in production
  - If omitted in `development` or `test`, the app uses an in-process ephemeral secret
  - This avoids the old hard-coded shared fallback secret, but also means tokens are not stable across restarts unless you set `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
  - Optional
  - Defaults to `60`
- `PASSWORD_HASH_ITERATIONS`
  - Optional
  - Defaults to `100000`
  - Controls the PBKDF2 iteration count used for password hashing

Example local setup:

```bash
APP_ENV=development
SECRET_KEY=your-local-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=60
PASSWORD_HASH_ITERATIONS=100000
```

## Local development

```bash
git clone https://github.com/BSAI301/course-project-ex2-team-12.git
cd course-project-ex2-team-12
python -m pip install -r requirements.txt
```

Run the backend:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Run the frontend:

```bash
streamlit run frontend/Home.py
```

The backend creates a local SQLite database file automatically under `data/boundary_circle.db` when needed.

## Tests

Run the full suite:

```bash
pytest -v
```

Run focused workflow tests:

```bash
pytest -v tests/test_circles_join.py
pytest -v tests/test_teams_api.py
pytest -v tests/test_integration.py
```

Generate a coverage report for backend code:

```bash
pytest --cov=src --cov-report=html
```

Generate local JUnit and coverage outputs equivalent to CI:

```bash
mkdir -p test-results
pytest \
  --junitxml=test-results/pytest.xml \
  --cov=src \
  --cov=frontend \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml
```

The repository includes `pytest-cov`, and the CI workflow now uploads two report-friendly artifacts on every run:

- `pytest-results` containing `test-results/pytest.xml`
- `coverage-report` containing `coverage.xml`

These artifacts are intended to provide verifiable testing evidence for project tracking and progress-report writing.

See `docs/report-evidence.md` for a quick mapping from report sections to repository evidence.

Coverage should be discussed with the correct scope:

- Backend-only coverage: `pytest --cov=src --cov-report=term-missing`
- Broader repository coverage used by CI: `pytest --cov=src --cov=frontend --cov-report=term-missing`

The backend-only percentage is higher because the current automated tests exercise the FastAPI backend more thoroughly than the Streamlit page code.

## API surface

Current backend routes are centered around these areas:

- `/auth` - register, login, current user
- `/users` - create and read users
- `/circles` - create and read circles
- `/circles/{circle_id}/tags` - create and list tag definitions
- `/circles/{circle_id}/tags/submit` - submit or update a user tag
- `/circles/{circle_id}/tags/my` - list a user's submitted tags in a circle
- `/tags/definitions/{tag_def_id}` - update and delete tag definitions
- `/tags/{user_tag_id}` - delete a submitted user tag
- `/teams` - create teams
- `/circles/{circle_id}/teams` - list teams in a circle
- `/circles/{circle_id}/members` - list circle members
- `/teams/{team_id}/invite` - send team invitations
- `/invitations` - list invitations for the current user
- `/invitations/{invite_id}/respond` - accept or reject an invitation
- `/teams/{team_id}/leave` - leave a team
- `/matching/users` - recommend users for a given team (team creator or members only)
- `/matching/teams` - recommend suitable teams for the current user in a circle

Interactive docs are available at `http://localhost:8000/docs` once the backend is running.

## Tag schema notes

Circle creators can now define tags using these field types:

- `integer`
- `float`
- `boolean`
- `single_select`
- `multi_select`

For selection-style tags:

- creators must provide a non-empty options list
- `multi_select` can also define `max_selections`
- backend validation remains the source of truth

The current matching backend still treats team requirements as tag-name requirements, so the new schema-driven team creation flow improves correctness and UX without yet adding value-level matching.

## Matching semantics

Team creation can now persist structured requirement rules alongside legacy `required_tags`.

Current matching behavior:

- `single_select`: exact equality
- `multi_select`: any overlap counts as a match
- `integer`, `float`, `boolean`, `string`: exact equality
- legacy teams without structured rules still fall back to tag-name-based matching

This keeps existing team data compatible while allowing newer teams to match on actual selected values.

## Docker

```bash
docker build -t boundary-circle .
docker run -p 8000:8000 boundary-circle
```

## Notes

- The repository includes archived planning and legacy files under `docs/archive/` for reference only.
- Team-management frontend pages exist, and backend team/invitation support now covers creation, invitation, response, and leave flows.
- This project is maintained as a course software-engineering repository rather than a polished production service.

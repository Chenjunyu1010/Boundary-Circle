# Boundary Circle

Boundary Circle is a FastAPI + Streamlit project for circle-based identity, tag submission, and lightweight teammate discovery workflows.

## What is implemented

- User registration, login, and current-user lookup
- Circle creation and browsing
- Per-circle tag definition management
- Per-user tag submission and update flows
- Circle join-related tag workflow coverage in automated tests
- Team creation, invitation, response, and leave flows with backend/API tests
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

Interactive docs are available at `http://localhost:8000/docs` once the backend is running.

## Docker

```bash
docker build -t boundary-circle .
docker run -p 8000:8000 boundary-circle
```

## Notes

- The repository includes archived planning and legacy files under `docs/archive/` for reference only.
- Team-management frontend pages exist, and backend team/invitation support now covers creation, invitation, response, and leave flows.
- This project is maintained as a course software-engineering repository rather than a polished production service.

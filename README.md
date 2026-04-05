# Boundary Circle

Boundary Circle is a FastAPI + Streamlit project for circle-based identity, tag submission, and lightweight teammate discovery workflows.

## What is implemented

- User registration, login, and current-user lookup
- Circle creation and browsing
- Per-circle tag definition management
- Per-user tag submission and update flows
- Circle join-related tag workflow coverage in automated tests
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

Run a focused workflow test:

```bash
pytest -v tests/test_circles_join.py
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

Interactive docs are available at `http://localhost:8000/docs` once the backend is running.

## Docker

```bash
docker build -t boundary-circle .
docker run -p 8000:8000 boundary-circle
```

## Notes

- The repository includes archived planning and legacy files under `docs/archive/` for reference only.
- Team-management frontend pages exist, but backend support is still incomplete compared with auth/circle/tag flows.
- This project is maintained as a course software-engineering repository rather than a polished production service.

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
- Circle-scoped free-text profile submission and freedom-tag matching (rerank-only)
- Circle join-related tag workflow coverage in automated tests
- Team creation, invitation, response, and leave flows with backend/API tests
- Matching recommendations for teams and users (backend APIs and Streamlit "Matching" tab)
- Streamlit pages for auth, circle browsing, circle detail, and team-management UI scaffolding

## Demo Flow Dependencies

The main demonstratable paths in the Streamlit frontend now **default to the real backend**. Mock mode (`MOCK_MODE=true`) is strictly a fallback for development.

During a demo or report evaluation, the following features depend entirely on a live `uvicorn` backend:
- Registration and Login: Requires the real SQLite database and token issuance.
- Circle and Tag Creation: Relies on `src/api/circles.py` and `src/api/tags.py` to persist data.
- Team Creation and Joining: Drives through `src/api/teams.py`, executing actual business logic rather than session-state dictionary updates.
- Value-Aware Matching: Calls `src/api/matching.py` to evaluate user-submitted values against team `required_tag_rules_json`.

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
- `LLM_PROVIDER`
  - Optional
  - Set to `openai_compatible` to enable real freedom-tag keyword extraction
- `LLM_API_KEY`
  - Optional unless `LLM_PROVIDER=openai_compatible`
  - API key for the compatible chat-completions endpoint
- `LLM_MODEL`
  - Optional unless `LLM_PROVIDER=openai_compatible`
  - Model name sent to `/chat/completions`
- `LLM_BASE_URL`
  - Optional unless `LLM_PROVIDER=openai_compatible`
  - Base URL for the compatible API, for example `https://api.openai.com/v1`

Example local setup:

```bash
cp .env.example .env

APP_ENV=development
SECRET_KEY=your-local-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=60
PASSWORD_HASH_ITERATIONS=100000
```

If you want real freedom-tag extraction instead of the empty-keyword fallback, add:

```bash
LLM_PROVIDER=openai_compatible
LLM_API_KEY=your-api-key
LLM_MODEL=qwen3-coder-next
LLM_BASE_URL=https://coding.dashscope.aliyuncs.com/v1
```

You can use the included `.env.example` as a starting point:

```bash
cp .env.example .env
```

## LLM integration

The repository supports real freedom-tag extraction through an OpenAI-compatible chat-completions API.

Current integration points:

- user free-text profile save: `PUT /circles/{circle_id}/profile`
- team free-text requirement save: `POST /teams` with `freedom_requirement_text`

When `LLM_PROVIDER=openai_compatible` and the other LLM variables are configured:

- the backend sends the free-text content to the configured `/chat/completions` endpoint
- the model returns JSON in the form `{"keywords": ["..."]}`
- the backend normalizes, deduplicates, and caps the result at 5 keywords
- these keywords are then used for rerank-only freedom matching

When the LLM variables are not configured:

- the backend falls back to an empty freedom profile: `{"keywords": []}`
- the rest of the application still works

Implementation notes:

- configuration is centralized in `src/core/settings.py`
- the OpenAI-compatible provider lives in `src/services/extraction.py`
- the current extractor uses structured timeout settings plus one retry for transient network failures
- current product logic intentionally caps extracted keywords at 5

## LLM provider notes

Real-provider validation in this project started with `qwen3.5-plus`. It produced strong results on some clear samples, but repeated live testing showed that it was too unstable for efficient manual validation because calls often timed out or were interrupted.

To improve practical testing stability, the active validation model was switched to `qwen3-coder-next`. This lighter model made sample-by-sample testing much more workable, and prompt tuning was then used to improve:

- negation handling
- over-broad paraphrasing
- generic filler-word extraction

See `docs/LLM-test/SUMMARY.md` for the current testing conclusions.

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

For the full local demo flow, including `.env` setup, LLM API configuration, backend/frontend startup, `stress2` seed usage, test accounts, and recommended end-to-end scenarios, see:

- `00_local-llm-demo-guide.md`

On startup, the app also applies a small SQLite-only compatibility upgrade for known
missing columns in older local database files. This currently covers:

- `tagdefinition.max_selections`
- `team.required_tag_rules_json`

This is a lightweight local schema patch for developer convenience, not a full
migration framework.

## Seed data

For local demos and exploratory testing, you can populate the SQLite database with
deterministic sample data:

```bash
python scripts/seed_data.py demo
python scripts/seed_data.py stress
python scripts/seed_data.py stress2
```

Reset one dataset without touching the other seed set or unrelated local records:

```bash
python scripts/seed_data.py demo --reset
python scripts/seed_data.py stress --reset
python scripts/seed_data.py stress2 --reset
```

Recommended usage:

- `demo`: smaller, presentation-friendly data for report walkthroughs
- `stress`: larger, more varied data for matching, invitation, leave-team, and lock/unlock testing
- `stress2`: the most complete local demo dataset for frontend walkthroughs, LLM-assisted freedom-tag scenarios, and richer matching/invitation cases

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

Run seed-data specific checks:

```bash
pytest -v tests/test_seed_data.py
pytest -v tests/test_seed_integration.py
pytest -v tests/test_seed_consistency.py
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

### LLM tests and CI policy

Real LLM tests are intentionally **not** part of the default CI path.

Reasons:

- they require network access
- they require valid API credentials
- they depend on provider uptime and model behavior
- model outputs can drift over time even when the prompt is unchanged

The repository separates these layers:

- default automated tests: deterministic local tests and mocked provider tests
- live LLM tests: opt-in only
- manual sample validation logs: stored under `docs/LLM-test/results/`

The CI workflow excludes live LLM tests by default through:

```bash
pytest -m "not llm_live"
```

If you want to run live LLM tests manually, enable them explicitly:

```bash
RUN_LLM_LIVE_TESTS=1 pytest -v tests/test_llm_live.py
```

For manual single-sample validation against the real provider, use:

```bash
python scripts/run_llm_sample.py S001
```

This reads from `docs/LLM-test/corpus.json` and writes a new result file such as `docs/LLM-test/results/R024.json`.

Relevant LLM testing assets:

- `docs/LLM-test/corpus.json`
- `docs/LLM-test/results/`
- `docs/LLM-test/README.md`
- `docs/LLM-test/SUMMARY.md`
- `tests/test_extraction_service.py`
- `tests/test_run_llm_sample.py`
- `tests/test_llm_live.py`

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
- `/circles/{circle_id}/profile` - update circle-scoped free-text profile (freedom-tag save)
- `/teams` - create teams (supports `freedom_requirement_text`)
- `/circles/{circle_id}/teams` - list teams in a circle
- `/circles/{circle_id}/members` - list circle members
- `/teams/{team_id}/invite` - send team invitations
- `/invitations` - list invitations for the current user
- `/invitations/{invite_id}/respond` - accept or reject an invitation
- `/teams/{team_id}/leave` - leave a team
- `/matching/users` - recommend users for a given team (team creator or members only; includes `freedom_score` and `matched_freedom_keywords`)
- `/matching/teams` - recommend suitable teams for the current user in a circle (includes `freedom_score` and `matched_freedom_keywords`)

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

## Matching semantics

Team creation can now persist structured requirement rules alongside legacy `required_tags`.
Freedom-tag matching adds an additive reranking layer:

- Freedom tags are saved as raw text via `PUT /circles/{circle_id}/profile`
- Backend extracts keywords and computes a freedom score for matching
- Freedom matching is rerank-only: fixed-tag gating remains the primary filter
- Candidates that fail fixed-tag requirements are excluded entirely
- Among already-eligible matches, freedom scoring reorders results
- If freedom matching fails or is unavailable, matches fall back to standard behavior

Current structured matching behavior:
- `single_select`: exact equality
- `multi_select`: any overlap counts as a match
- `integer`, `float`, `boolean`, `string`: exact equality
- legacy teams without structured rules still fall back to tag-name-based matching

This keeps existing team data compatible while allowing newer teams to match on actual selected values and free-text freedom preferences.

## Docker

```bash
docker build -t boundary-circle .
docker run -p 8000:8000 boundary-circle
```

## Notes

- The repository includes archived planning and legacy files under `docs/archive/` for reference only.
- Team-management frontend pages exist, and backend team/invitation support now covers creation, invitation, response, and leave flows.
- This project is maintained as a course software-engineering repository rather than a polished production service.

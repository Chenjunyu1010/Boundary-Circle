# Report Evidence Index

This document maps progress-report claims to repository evidence that can be checked directly.

## 1. Project Summary and Requirements

- Project scope summary: `README.md`
- Current architecture and stack: `README.md`
- Proposal baseline for comparison: `docs/proposal.md`

## 2. System Design and Current Implementation

- Backend entry point and router registration: `src/main.py`
- Circle APIs: `src/api/circles.py`
- Auth APIs: `src/api/auth.py`
- Tag APIs: `src/api/tags.py`
- Frontend pages: `frontend/pages/`

## 3. Progress Against Plan

- Historical planning material: `docs/archive/`
- Current repository structure: `README.md`
- Pull requests should summarize evidence using `.github/pull_request_template.md`

## 4. Current Feature Status and Scope Update

- Stable implemented backend areas: `src/api/auth.py`, `src/api/circles.py`, `src/api/tags.py`, `src/api/teams.py`, `src/api/matching.py`
- Frontend team-management scaffolding: `frontend/pages/team_management.py`, aligned with the real backend.
- Frontend API client: `frontend/utils/api.py` with real backend integration replacing mock behaviors.

## 5. Testing and CI Status

- CI workflow definition: `.github/workflows/ci.yml`
- Core backend/API tests: `tests/test_auth_api.py`, `tests/test_tags_api.py`, `tests/test_circles_join.py`
- Frontend page tests: `tests/test_frontend_auth.py`, `tests/test_frontend_circles.py`, `tests/test_frontend_teams.py`
- CI outputs after each run:
  - `pytest-results` artifact with JUnit XML
  - `coverage-report` artifact with `coverage.xml`
- Coverage statements should distinguish:
  - backend-only coverage from `pytest --cov=src`
  - broader repository coverage from `pytest --cov=src --cov=frontend`

## 6. Risks, Issues, and Actions Taken

- Complex team matching rules implementation and backend transition completed: `README.md`, `src/api/matching.py`, `src/api/teams.py`
- CI maturity improvements and remaining limitations: `.github/workflows/ci.yml`

## 7. Next Milestones and Task Assignment

The most defensible next milestones should be grounded in currently visible gaps:

- continue expanding automated tests around edge cases and remaining workflow combinations
- enhance frontend UI/UX for complex structured tag submission and team requirements
- use uploaded CI artifacts as recurring evidence for progress tracking

## Writing Guardrail

Use direct file evidence first. Ensure backend API logic in `src/api/` and `src/services/` accurately maps to the features claimed in progress reports.

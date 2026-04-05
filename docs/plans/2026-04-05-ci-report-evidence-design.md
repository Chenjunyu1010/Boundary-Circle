# CI and Report Evidence Design

## Goal

Improve the repository so the progress report can reference concrete, reproducible evidence for testing and CI without overstating project maturity.

## Scope

- Upgrade the GitHub Actions workflow to produce machine-readable test and coverage outputs.
- Document how those outputs are generated locally and in CI.
- Add a report-oriented evidence index so team members can cite repository artifacts consistently.
- Add a lightweight pull request template to encourage test evidence and report-relevant notes.

## Decisions

### 1. Keep a single CI job

The current project is small and already runs successfully with a single `build-and-test` job. Splitting the workflow into multiple jobs or a version matrix would increase failure surface without adding much value for the course report.

### 2. Add evidence, not process theater

The workflow will add:

- `pip` dependency caching
- JUnit XML output
- coverage XML output
- terminal coverage summary
- artifact upload that runs even if tests fail

This gives the team tangible evidence for report section 5 while staying aligned with the current repository size.

### 3. Do not oversell backend completeness

Supporting documentation will remain explicit that:

- CI now produces better testing evidence
- team/invitation workflows are still frontend-heavy and partially mocked
- the repository is still a course project MVP rather than a production service

### 4. Add report-facing documentation

Instead of relying on memory during report writing, add a concise document that maps report claims to repository files and generated CI outputs.

## Files To Change

- `.github/workflows/ci.yml`
- `README.md`
- `.github/pull_request_template.md`
- `docs/report-evidence.md`

## Verification Plan

- Run `pytest -q`
- Run `pytest --junitxml=test-results/pytest.xml --cov=src --cov=frontend --cov-report=term-missing --cov-report=xml:coverage.xml`
- Review generated outputs


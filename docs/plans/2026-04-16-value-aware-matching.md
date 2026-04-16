# Value-Aware Matching Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make backend matching use structured team requirement values while preserving compatibility with legacy tag-name-only teams.

**Architecture:** Add structured `required_tag_rules` beside legacy `required_tags`, then make matching prefer parsed value rules and fall back to old name-only coverage when structured rules are absent.

**Tech Stack:** FastAPI, SQLModel, pytest

---

### Task 1: Add structured team requirement schemas and serializers

**Files:**
- Modify: `src/models/teams.py`
- Test: `tests/test_teams_api.py`

**Step 1: Write the failing test**

Add tests that prove:

- `TeamCreate` accepts `required_tag_rules`
- encode/decode helpers round-trip structured rules
- malformed stored JSON decodes to an empty list safely

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_teams_api.py -v`

Expected: FAIL because structured team requirement rules do not exist yet.

**Step 3: Write minimal implementation**

Update `src/models/teams.py` to add:

- `TeamRequirementRule`
- `required_tag_rules_json` on `Team`
- `required_tag_rules` on `TeamCreate` and `TeamRead`
- encode/decode helpers for structured rules

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_teams_api.py -v`

Expected: PASS for the new schema tests.

### Task 2: Persist and return structured team requirement rules

**Files:**
- Modify: `src/api/teams.py`
- Test: `tests/test_teams_api.py`

**Step 1: Write the failing test**

Add tests that create a team with `required_tag_rules` and verify:

- the API stores the rules
- the response includes both `required_tags` and `required_tag_rules`
- legacy team creation without rules still works

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_teams_api.py -v`

Expected: FAIL because the teams API does not persist or expose structured rules yet.

**Step 3: Write minimal implementation**

Update `src/api/teams.py` to:

- store `required_tag_rules_json`
- return decoded `required_tag_rules` in `TeamRead`
- keep `required_tags` behavior unchanged

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_teams_api.py -v`

Expected: PASS.

### Task 3: Add value-aware matching helpers

**Files:**
- Modify: `src/services/matching.py`
- Test: `tests/test_matching_api.py`

**Step 1: Write the failing test**

Add helper-level or API-level tests covering:

- exact match for `single_select`
- mismatch for `single_select`
- overlap match for `multi_select`
- no-overlap miss for `multi_select`

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_matching_api.py -v`

Expected: FAIL because matching only compares tag names today.

**Step 3: Write minimal implementation**

Update `src/services/matching.py` to add helpers for:

- parsing user tags into typed values by tag name
- evaluating one structured rule against one user value
- computing structured coverage and explanation text

Keep fallback helpers for legacy tag-name matching.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_matching_api.py -v`

Expected: PASS for the new value-aware cases.

### Task 4: Make matching endpoints prefer structured rules

**Files:**
- Modify: `src/api/matching.py`
- Test: `tests/test_matching_api.py`
- Test: `tests/test_team_integration.py`

**Step 1: Write the failing test**

Add endpoint-level tests that prove:

- `/matching/users` uses structured rules when present
- `/matching/teams` uses structured rules when present
- legacy teams without structured rules still match as before

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_matching_api.py tests/test_team_integration.py -v`

Expected: FAIL because endpoints still use `required_tags` name-only coverage.

**Step 3: Write minimal implementation**

Update `src/api/matching.py` to:

- load structured rules from teams
- use structured coverage and explanations when rules exist
- fall back to name-only matching otherwise

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_matching_api.py tests/test_team_integration.py -v`

Expected: PASS.

### Task 5: Update docs and verify end-to-end

**Files:**
- Modify: `README.md`
- Modify: `docs/2026-04-15-project-backlog.md`

**Step 1: Define verification commands**

Run:

```bash
pytest tests/test_teams_api.py tests/test_matching_api.py tests/test_team_integration.py -v
pytest -q
```

**Step 2: Write minimal documentation updates**

Document:

- that team requirements now support structured value rules
- the current matching semantics:
  - exact equality for single-value fields
  - overlap for multi-select fields
- the remaining future work around richer numeric/range matching

**Step 3: Run verification again**

Run:

```bash
pytest tests/test_teams_api.py tests/test_matching_api.py tests/test_team_integration.py -v
pytest -q
```

Expected: PASS.

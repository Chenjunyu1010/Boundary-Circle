# Issue 37 Test Expansion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reorganize and expand the team, invitation, and circle membership API tests so issue #37 has explicit, maintainable coverage including one end-to-end team formation flow.

**Architecture:** Keep production code unchanged unless tests expose a real backend defect. Split tests by responsibility: circle membership flow, team API flow, invitation API flow, and integration flow. Reuse existing authenticated registration helpers and current API behavior to avoid brittle rewrites.

**Tech Stack:** FastAPI, SQLModel, pytest, TestClient

---

### Task 1: Audit Current Coverage

**Files:**
- Modify: `tests/test_teams_api.py`
- Modify: `tests/test_circles_join.py`
- Test: `tests/test_integration.py`

**Step 1: Review existing tests**

Confirm which issue #37 acceptance items are already covered and which are missing or mixed into the wrong file.

**Step 2: Identify target file ownership**

Move circle membership assertions to `tests/test_circles_join.py`, team lifecycle assertions to `tests/test_teams_api.py`, invitation assertions to `tests/test_invitations_api.py`, and the end-to-end flow to `tests/test_team_integration.py`.

### Task 2: Restructure Invitation Coverage

**Files:**
- Create: `tests/test_invitations_api.py`
- Modify: `tests/test_teams_api.py`

**Step 1: Move invitation scenarios**

Create invitation-focused tests for sending, duplicate invites, authorization failures, inbox behavior, acceptance, rejection, and capacity conflicts.

**Step 2: Keep team tests focused**

Leave only team creation and team leave behaviors in `tests/test_teams_api.py`.

### Task 3: Add Explicit End-to-End Coverage

**Files:**
- Create: `tests/test_team_integration.py`
- Modify: `tests/test_integration.py`

**Step 1: Write one full issue-aligned workflow**

Cover: join circle, submit tags, create team, send invite, accept invite, verify final team state.

**Step 2: Remove overlapping broad flow test**

Avoid duplicate integration ownership by moving the team-formation flow out of `tests/test_integration.py`.

### Task 4: Run Verification

**Files:**
- Test: `tests/test_circles_join.py`
- Test: `tests/test_teams_api.py`
- Test: `tests/test_invitations_api.py`
- Test: `tests/test_team_integration.py`
- Test: `tests/test_integration.py`

**Step 1: Run focused verification**

Run: `pytest -v tests/test_teams_api.py tests/test_circles_join.py tests/test_invitations_api.py tests/test_team_integration.py tests/test_integration.py`

**Step 2: Run broader suite if focused tests pass**

Run: `pytest -v`

**Step 3: Report results**

Summarize environment, command, timing, passed/failed/warnings, and any residual risk before any commit request.

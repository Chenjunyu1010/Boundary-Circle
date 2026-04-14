# Matching System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a matching system that recommends suitable users for a given team and suitable teams for a given user within a circle, based on tags and membership data.

**Architecture:** Introduce a small service module `src/services/matching.py` that encapsulates matching calculations (tag aggregation, coverage score, Jaccard similarity), and expose two FastAPI routes in `src/api/matching.py` that rely on existing auth, team, circle, and tag models. Keep all heavy logic out of route functions, and reuse existing SQLModel models where possible.

**Tech Stack:** FastAPI, SQLModel, SQLite, existing auth dependencies (`get_current_user`), pytest.

---

### Task 1: Add matching service module

**Files:**
- Create: `src/services/matching.py`

**Steps:**
1. Define a `get_user_tag_names_for_circle(session: Session, user_id: int, circle_id: int) -> set[str]` helper that returns tag *names* for the user in that circle by joining `UserTag` and `TagDefinition`.
2. Define a `get_team_member_ids(session: Session, team_id: int) -> list[int]` helper using `TeamMember`.
3. Define a `build_team_profile(session: Session, team: Team) -> set[str]` helper that returns union of `decode_required_tags(team.required_tags_json)` and all tag names of current team members in the same circle.
4. Implement `coverage_score(required: set[str], user_tags: set[str]) -> float` returning `1.0` when `required` is empty, otherwise `|required ∩ user_tags| / |required|`.
5. Implement `jaccard_score(a: set[str], b: set[str]) -> float` returning `0.0` when union is empty, otherwise `|a ∩ b| / |a ∪ b|`.

### Task 2: Implement matching API models and router

**Files:**
- Create: `src/api/matching.py`

**Steps:**
1. Define response models using `SQLModel` (non-table):
   - `UserMatch` with `user_id: int`, `username: str`, `email: str`, `coverage_score: float`, `jaccard_score: float`, `matched_tags: list[str]`, `missing_required_tags: list[str]`.
   - `TeamMatch` with `team: TeamRead`, `coverage_score: float`, `jaccard_score: float`, `missing_required_tags: list[str]`.
2. Create `router = APIRouter(prefix="/matching", tags=["Matching"])`.
3. Implement `GET /matching/users` endpoint:
   - Query params: `team_id: int`, optional `limit: int = 10`.
   - Dependencies: `current_user: User = Depends(get_current_user)`, `session: Session = Depends(get_session)`.
   - Load `Team` by id and ensure its circle exists.
   - Ensure `current_user` is a member or creator of the team and is a member of the circle (using `CircleMember` and `Circle.creator_id`).
   - Compute `required_tags` (set of strings) from `decode_required_tags(team.required_tags_json)`.
   - Build `team_profile` using the service helper.
   - Collect candidate user ids: all `CircleMember` in the circle excluding current team members and current user.
   - For each candidate, compute user tag set, coverage score and Jaccard score (team_profile vs user profile), and skip candidates with `coverage_score == 0.0`.
   - Sort by `coverage_score` desc, then `jaccard_score` desc, apply `limit`, and return list of `UserMatch`.
4. Implement `GET /matching/teams` endpoint:
   - Query params: `circle_id: int`, optional `limit: int = 10`.
   - Dependencies: `current_user: User = Depends(get_current_user)`, `session: Session = Depends(get_session)`.
   - Ensure circle exists and `current_user` is circle creator or a `CircleMember`.
   - Compute `user_tags` as the current user's tag set in that circle.
   - Enumerate all teams in the circle and build `TeamRead` via existing `build_team_read` helper from `src.api.teams`.
   - Skip teams where current user is already a member, team is locked/full, or `coverage_score == 0.0` for this user.
   - For each remaining team, build `team_profile` and compute Jaccard with `user_tags`.
   - Sort by `coverage_score` desc then `jaccard_score` desc, apply `limit`, and return list of `TeamMatch`.

### Task 3: Wire router into application

**Files:**
- Modify: `src/main.py`
- Possibly modify: `src/api/__init__.py`

**Steps:**
1. Import the new `matching` module in `src/main.py` alongside existing routers.
2. Call `app.include_router(matching.router)` after other router registrations.
3. If `src/api/__init__.py` re-exports router modules, add `matching` to its exports to keep import style consistent.

### Task 4: Add pytest coverage for matching API

**Files:**
- Create: `tests/test_matching_api.py`

**Steps:**
1. Reuse the `register_and_login` helper from `tests/test_teams_api.py` (or copy a minimal variant) to obtain `(user_payload, headers)` pairs.
2. Write `test_match_users_for_team_orders_by_coverage_and_jaccard`:
   - Create circle and creator; ensure creator is circle member.
   - Create a team with `required_tags = ["role", "stack"]`.
   - Create tag definitions `role`, `stack`, and at least one extra tag, then submit tags for several users with different combinations.
   - Call `GET /matching/users?team_id=...` as creator and assert:
     - Users with more required tags matched appear before those with fewer.
     - Users with zero coverage are not included.
3. Write `test_match_teams_for_user_basic`:
   - Create circle and user; make user a member.
   - Create two teams in that circle with different `required_tags` values.
   - Assign tags to the user so that coverage differs per team.
   - Call `GET /matching/teams?circle_id=...` and assert ordering and presence.
4. Add at least one permission test (e.g. non-circle-member cannot call `/matching/teams`) and one unauthorized test (no token returns 401).

### Task 5: Run tests and adjust

**Files:**
- Existing tests and new matching tests.

**Steps:**
1. Run `pytest -v tests/test_matching_api.py` and ensure all new tests pass.
2. Run full suite `pytest -v` if feasible to confirm no regressions.
3. If any failures or type issues arise, adjust service or API implementations while keeping behavior aligned with the tests.


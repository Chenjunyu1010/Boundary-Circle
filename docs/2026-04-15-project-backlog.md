# Boundary Circle Backlog

Last updated: 2026-04-16

This document lists the main remaining engineering fixes and feature opportunities for the project after the strict auth-boundary cleanup. It is meant to help the team decide what to prioritize next for course delivery and for any post-course hardening.

## Completed recently

### Completed on 2026-04-16: unify user creation and auth registration
- `POST /users/` and `POST /auth/register` now share the same backend creation logic.
- Both paths enforce the same duplicate email and duplicate username checks.
- Users created from the legacy `/users/` path now use the real password hashing flow and can log in through `/auth/login`.
- Follow-up still recommended:
  - Decide whether `/users/` should remain as a compatibility path or be formally deprecated later.
  - Move login/register request and response schemas into a more consistent API schema module if the auth surface keeps growing.
**Completed items:**
- #1 Unify user creation - ✅ Completed (PR #75)
- #2 Remove JWT secret fallback - ✅ Completed (PR #74)
- #3 Fix encoding issues - ✅ Completed (PR #73)

## 1. High-priority fixes

### 1. Unify user creation into one path
- Status:
  - Completed as a compatibility-safe fix on 2026-04-16.
- Current problem:
  - The repository still has both `/users` and `/auth/register`.
  - `src/api/users.py` stores passwords with a fake hash pattern, while `/auth/login` uses the real password verification flow.
- Risk:
  - Users created from `/users` are inconsistent with the auth system.
  - This is a correctness and security issue, not just a code-style issue.
- Recommendation:
  - Short term: keep `/users` for compatibility, but route it through the same shared creation service as `/auth/register`.
  - Later: decide whether to deprecate `/users` creation and keep only `/auth/register`.
  - Keep regression tests that prove both valid creation and valid login for the chosen path.

### 2. Remove hard-coded fallback JWT secret
- Current problem:
  - `src/auth/security.py` still falls back to `development-secret-change-me`.
- Risk:
  - If the environment variable is not set, deployments share a predictable signing key.
- Recommendation:
  - Fail fast when `SECRET_KEY` is missing outside local development.
  - Document the required environment variables in `README.md`.

### 3. Fix encoding / text corruption in source and docs
- Current problem:
  - Several files contain mojibake in Chinese comments and some emoji text.
  - This is visible in `agents.md`, `docs/project-completion-evaluation.md`, and some frontend files.
- Risk:
  - It reduces readability, makes maintenance harder, and looks unprofessional in demos.
- Recommendation:
  - Normalize affected files to UTF-8.
  - Replace corrupted comments and UI strings with clean English or clean Chinese consistently.

### 4. Add static quality gates (Skipped)
- ~~Current problem:~~
  - ~~The project has tests and CI, but there is no consistent lint or type-check stage.~~
- ~~Risk:~~
  - ~~Regressions in typing, formatting, and import hygiene will not be caught early.~~
- ~~Recommendation:~~
  - ~~Add `ruff` and either `mypy` or `pyright`.~~
  - ~~Wire them into GitHub Actions.~~
- **Status**: Skipped - Tests provide sufficient coverage; lint/type-check is optional for this course project.

### 5. Separate business logic from route handlers further
- Current problem:
  - The codebase already has a `services/` folder, but most business rules still live directly in route files.
- Risk:
  - As workflows grow, handlers will become harder to test and evolve.
- Recommendation:
  - Move more rules from `src/api/*.py` into service-layer helpers.
  - Keep routers focused on request parsing, authorization, and response shaping.

## 2. Medium-priority fixes

### 6. Improve configuration management
- Current problem:
  - Runtime behavior is still configured in an ad-hoc way.
- Recommendation:
  - Centralize config with `pydantic-settings`.
  - Explicitly model database path, JWT secret, token expiry, API base URLs, and mock mode.

### 7. Improve API consistency and error payloads
- Current problem:
  - Some endpoints return plain dictionaries, some rely on response models, and error detail style is not fully standardized.
- Recommendation:
  - Define a more consistent error contract.
  - Add a small set of common response schemas for success/error envelopes where useful.

### 8. Expand negative-path tests
- Current problem:
  - Main flows are tested well, but some authorization and boundary cases are still only lightly covered.
- Recommendation:
  - Add more tests for:
    - invalid or expired tokens
    - cross-circle tag access
    - deleting or updating resources owned by other users
    - malformed payloads for enum and numeric tag values

### 9. Clean up legacy docs and archived references
- Current problem:
  - Some docs are outdated, partially corrupted, or refer to planned functionality as if it were still current.
- Recommendation:
  - Mark archived docs more clearly.
  - Add one current architecture/status document that matches the repository as it exists today.

## 3. High-value feature additions

### 10. Matching explanation UI
- Why it matters:
  - Matching exists, but the user-facing explanation is still basic.
- Suggested addition:
  - Show why a user/team was recommended:
    - matched tags
    - missing tags
    - coverage score
    - similarity score
  - Add sorting and filtering in the matching tab.

### 11. Tag-aware team creation experience
- Why it matters:
  - Team creation currently uses a fixed multiselect list for required tags in the frontend.
- Suggested addition:
  - Load actual circle tag definitions dynamically when creating a team.
  - Let creators choose required tags from the real circle schema instead of hard-coded options.

### 12. Team join workflow improvements
- Why it matters:
  - Team membership currently depends on invitation flow only.
- Suggested addition:
  - Add optional "request to join" flow.
  - Add invitation withdrawal and team-owner review actions.

### 13. Circle membership management
- Why it matters:
  - Circles support join/leave, but there is little admin tooling.
- Suggested addition:
  - Add creator/admin actions for:
    - viewing members with roles
    - removing members
    - promoting or demoting circle roles if role management is kept

### 14. Better account management
- Why it matters:
  - For demo and realism, account lifecycle is still minimal.
- Suggested addition:
  - Add:
    - change password
    - edit profile
    - optional password reset flow

## 4. Stretch features

### 15. LLM-generated matching explanation
- Why it matters:
  - This aligns well with the course theme and can strengthen the demo story.
- Suggested addition:
  - Use an LLM to turn structured matching scores into short natural-language explanations.
- Constraint:
  - Keep it optional and clearly separated from the deterministic scoring logic.

### 16. Notification or activity layer
- Suggested addition:
  - Add a simple activity feed or notifications for:
    - invitation received
    - invitation accepted/rejected
    - team locked/full

### 17. Frontend polish beyond Streamlit defaults
- Suggested addition:
  - Improve information hierarchy and empty/error states.
  - Make the circle detail and team management pages feel more intentional for demo usage.

## 5. Suggested priority order

As of 2026-04-16, items #1-#3 are completed and #4 is skipped. Remaining tasks:

1. ~~Unify `/users` and `/auth/register`~~ ✅
2. ~~Remove the fallback JWT secret and centralize config~~ ✅
3. ~~Fix corrupted encoding in docs and UI strings~~ ✅
4. ~~Add lint/type-check gates~~ (skipped - not critical for course project)
5. Make team creation use real circle tag definitions.
6. Improve the matching explanation UI.
7. Decide whether to add one standout stretch feature, ideally LLM-generated matching explanations.

# Boundary Circle Backlog

Last updated: 2026-04-16

This document tracks the main engineering fixes and feature opportunities after the auth-boundary cleanup and recent schema-driven tag work.

## Completed recently

### Completed on 2026-04-16: unify user creation and auth registration
- `POST /users/` and `POST /auth/register` now share the same backend creation logic.
- Both paths enforce the same duplicate email and duplicate username checks.
- Users created from the legacy `/users/` path now use the real password hashing flow and can log in through `/auth/login`.
- Follow-up still recommended:
  - Decide whether `/users/` should remain as a compatibility path or be formally deprecated later.
  - Move login/register request and response schemas into a more consistent API schema module if the auth surface keeps growing.

### Completed on 2026-04-16: tag-aware team creation and controlled selection tags
- Circle tag definitions now support `single_select` and `multi_select`.
- Circle creators can define allowed options for selection-style tags.
- `multi_select` tags can enforce `max_selections`.
- Circle member forms and team creation forms now load real circle tag definitions instead of using hard-coded frontend tag lists.
- Backend validation now enforces submitted selection values against the stored circle schema.

### Completed on 2026-04-16: value-aware backend matching
- Teams can now store structured `required_tag_rules` in addition to legacy `required_tags`.
- Backend matching now prefers structured value rules when they exist.
- `single_select` fields use exact equality.
- `multi_select` fields match on overlap.
- Legacy teams without structured rules continue to use tag-name-based matching.
- Team creation in the frontend now sends structured rules so the real UI path uses the new backend behavior.

**Completed items:**
- #1 Unify user creation - completed (PR #75)
- #2 Remove JWT secret fallback - completed (PR #74)
- #3 Fix encoding issues - completed (PR #73)
- #11 Tag-aware team creation experience - completed on 2026-04-16
- #10 Matching explanation and correctness improvements - partially completed on 2026-04-16

## 1. High-priority fixes

### 1. Unify user creation into one path
- Status:
  - Completed as a compatibility-safe fix on 2026-04-16.
- Current problem:
  - The repository still has both `/users` and `/auth/register`.
  - `src/api/users.py` previously stored passwords with a fake hash pattern, while `/auth/login` used the real password verification flow.
- Risk:
  - Users created from `/users` were inconsistent with the auth system.
- Recommendation:
  - Short term: keep `/users` for compatibility, but route it through the same shared creation service as `/auth/register`.
  - Later: decide whether to deprecate `/users` creation and keep only `/auth/register`.
  - Keep regression tests that prove both valid creation and valid login.

### 2. Remove hard-coded fallback JWT secret
- Status:
  - Completed on 2026-04-16.
- Recommendation:
  - Keep `README.md` aligned with the required environment variables and deployment expectations.

### 3. Fix encoding / text corruption in source and docs
- Status:
  - Completed on 2026-04-16.
- Recommendation:
  - Continue replacing any remaining mojibake when touched by future work.

### 4. Add static quality gates (Skipped)
- Status:
  - Skipped for the course project.
- Recommendation:
  - If the repository continues after the course, add `ruff` and either `mypy` or `pyright`.

### 5. Separate business logic from route handlers further
- Current problem:
  - The codebase already has a `services/` folder, but many business rules still live directly in route files.
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
  - Add a small set of common response schemas where useful.

### 8. Expand negative-path tests
- Current problem:
  - Main flows are tested well, but some authorization and boundary cases are still only lightly covered.
- Recommendation:
  - Add more tests for invalid or expired tokens.
  - Add cross-circle tag access coverage.
  - Add more ownership-boundary tests for update/delete flows.
  - Add malformed payload coverage for numeric and selection-style tag values.

### 9. Clean up legacy docs and archived references
- Current problem:
  - Some docs are outdated, partially corrupted, or refer to planned functionality as if it were still current.
- Recommendation:
  - Mark archived docs more clearly.
  - Keep one current architecture/status document aligned with the repository as it exists today.

## 3. High-value feature additions

### 10. Matching explanation UI
- Status:
  - Partially completed on 2026-04-16.
- Delivered:
  - Matching correctness now uses structured requirement values when available.
  - API explanations now report matched and missing structured requirements more precisely.
- Remaining work:
  - Improve the frontend presentation of those explanations.
  - Add sorting and filtering in the matching tab.

### 11. Tag-aware team creation experience
- Status:
  - Completed on 2026-04-16.
- Follow-up still recommended:
  - Extend numeric fields from exact equality to richer range-based matching if needed later.

### 12. Team join workflow improvements
- Why it matters:
  - Team membership currently depends on invitation flow only.
- Suggested addition:
  - Add optional request-to-join flow.
  - Add invitation withdrawal and team-owner review actions.

### 13. Circle membership management
- Why it matters:
  - Circles support join/leave, but there is little admin tooling.
- Suggested addition:
  - Add creator or admin actions for viewing members with roles.
  - Add remove-member and role-management actions if role management stays in scope.

### 14. Better account management
- Why it matters:
  - Account lifecycle is still minimal.
- Suggested addition:
  - Add change password.
  - Add edit profile.
  - Add optional password reset.

## 4. Stretch features

### 15. LLM-generated matching explanation
- Why it matters:
  - This aligns well with the course theme and strengthens the demo story.
- Suggested addition:
  - Use an LLM to turn structured matching scores into short natural-language explanations.
- Constraint:
  - Keep it optional and clearly separated from deterministic scoring logic.

### 16. Notification or activity layer
- Suggested addition:
  - Add notifications for invitation received, invitation accepted or rejected, and team locked/full.

### 17. Frontend polish beyond Streamlit defaults
- Suggested addition:
  - Improve information hierarchy and empty/error states.
  - Make the circle detail and team management pages feel more intentional for demo use.

## 5. Suggested priority order

As of 2026-04-16, items #1, #2, #3, and #11 are completed, #10 is partially completed, and #4 is skipped. Suggested next steps:

1. Improve the frontend matching explanation UI.
2. Decide whether numeric team requirements should support range-based matching.
3. Expand negative-path tests around malformed structured rules and ownership boundaries.
4. Separate more business logic from route handlers into services.
5. Decide whether to add one standout stretch feature, ideally LLM-generated matching explanations.

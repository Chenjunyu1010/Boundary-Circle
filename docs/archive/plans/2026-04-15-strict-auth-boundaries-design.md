# Strict Auth Boundaries Design

**Goal:** Remove query-parameter identity injection from circle and tag workflows and require Bearer authentication for all user-scoped or creator-scoped actions.

**Scope**
- Protect `POST /circles` with token-based identity.
- Protect all `src/api/tags.py` endpoints that currently trust `current_user_id`.
- Update Streamlit callers to stop sending `creator_id` and `current_user_id`.
- Update tests to validate Bearer-only behavior and ensure spoofed query params no longer grant access.

**Approach**
- Reuse `src.auth.dependencies.get_current_user` as the single identity source.
- Replace external `creator_id/current_user_id` inputs with `current_user.id` inside handlers.
- Keep route paths stable where possible, but make authentication mandatory and remove the legacy query-param contract.
- Update frontend helpers to rely on the existing Authorization header already managed by `frontend/utils/api.py`.

**API Changes**
- `POST /circles`:
  - Before: caller provides `creator_id` query param.
  - After: authenticated user becomes creator automatically.
- `POST /circles/{circle_id}/tags`
- `POST /circles/{circle_id}/tags/submit`
- `GET /circles/{circle_id}/tags/my`
- `DELETE /tags/{user_tag_id}`
- `PUT /tags/definitions/{tag_def_id}`
- `DELETE /tags/definitions/{tag_def_id}`
  - Before: caller provides `current_user_id` query param.
  - After: current authenticated user is used for authorization and ownership.

**Authorization Rules**
- Circle creation requires any authenticated user.
- Tag-definition create/update/delete requires the authenticated circle creator.
- User-tag submit/read/delete requires the authenticated user operating on their own records only.

**Testing Strategy**
- Add failing API tests first for:
  - unauthenticated create-circle rejected with `401`
  - unauthenticated tag submit rejected with `401`
  - spoofed `current_user_id` query param does not bypass auth
  - authenticated Bearer calls still succeed for create-circle and tag workflows
- Run focused tests during red/green, then run the full suite.

**Risks**
- Existing tests and frontend pages currently rely on query params, so they will fail until updated.
- Any undocumented external callers using the old query-param contract will break, which is intended for this strict fix.

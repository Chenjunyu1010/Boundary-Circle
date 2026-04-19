# Plans Index

This index explains which files in `docs/plans/` are still worth reading and which ones have been archived to reduce noise.

## What Stays In `docs/plans/`

`docs/plans/` now keeps the main implementation threads that still help explain the current codebase.

### Matching and team creation

- `2026-04-14-matching-implementation.md`
  - Early matching implementation notes.
  - Useful for understanding how the project moved from basic matching to the current backend-driven flow.

- `2026-04-16-tag-aware-team-creation-design.md`
  - Team creation based on real circle tag definitions.
  - Useful for understanding why the frontend now depends on live circle tag schema instead of a fixed list.

- `2026-04-16-value-aware-matching-design.md`
  - Matching on tag values instead of tag names only.
  - Useful for understanding the current structured matching behavior.

### LLM freedom-tags work

- `2026-04-17-llm-freedom-tags-design.md`
  - Main product design for user/team free text plus LLM extraction.
  - Useful as the top-level design document for this feature line.

- `2026-04-18-openai-compatible-freedom-tags-design.md`
  - Design for the OpenAI-compatible provider integration.
  - Useful for understanding why extraction happens on save, not during matching.

- `2026-04-18-openai-compatible-freedom-tags-implementation.md`
  - Compact implementation plan for the compatible provider integration.
  - Useful as concise process evidence.

- `2026-04-18-llm-freedom-tags-v1-implementation.md`
  - Very detailed implementation plan.
  - Useful as process evidence, but not a good first document to read.

### User profile and richer seed data

- `2026-04-17-user-profile-page-design.md`
  - User profile design.
  - Useful for understanding the split between `User` and `UserProfile`.

- `2026-04-18-user-profile-page-implementation.md`
  - Implementation record for the profile page and seed-related profile enrichment.
  - Useful when tracing why current seed users include richer profile data.

### Backend migration and deployment

- `2026-04-17-real-backend-migration-completion.md`
  - Short record of the transition to the current real-backend flow.
  - Useful for quickly understanding why the frontend now defaults to the live backend.

- `2026-04-17-deployment-design.md`
  - Deployment-oriented design notes.
  - Useful if you need deployment context; lower priority for local-only work.

### Testing and report evidence

- `2026-04-05-ci-report-evidence.md`
- `2026-04-05-ci-report-evidence-design.md`
- `2026-04-14-issue-37-test-expansion.md`
  - These are mostly course-delivery and testing-process records.
  - Useful as evidence of engineering process, but not part of the product logic mainline.

## What Was Archived

The following files were moved to `docs/archive/plans/` because they are lower priority, narrower in scope, or covered by later documents:

- `2026-04-15-project-backlog.md`
- `2026-04-15-strict-auth-boundaries.md`
- `2026-04-15-strict-auth-boundaries-design.md`
- `2026-04-17-gemini-ui-design-brief.md`

They are still kept in the repository as process evidence, just not in the main plans folder.

## Suggested Reading Order

If you want the shortest path to understanding the current system, read in this order:

1. `2026-04-16-tag-aware-team-creation-design.md`
2. `2026-04-16-value-aware-matching-design.md`
3. `2026-04-17-llm-freedom-tags-design.md`
4. `2026-04-18-openai-compatible-freedom-tags-design.md`
5. `00_local-llm-demo-guide.md` in the repo root

## One-Line Summary

The main retained process threads are:

- fixed tags to value-aware matching
- structured matching plus freedom text and LLM extraction
- mock/demo-oriented frontend flows to real backend end-to-end flows

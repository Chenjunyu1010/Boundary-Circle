# UI Execution Checklist (Phase 1)

Date: 2026-04-19  
Owner: EX2-Team-12

## 1. Scope Lock (Do Not Change)

- Do not change backend API contracts.
- Do not change the main workflow order (Auth -> Circle -> Tags -> Team -> Matching).
- Do not introduce new frontend frameworks.
- Do not add high-complexity interactions that are hard to maintain in Streamlit.

## 2. Page Priority

- P0: Team Management page (highest demo value)
- P1: Circle Detail page
- P2: Auth page and Circle Hall page

## 3. Baseline Screenshot Pack (Before UI Changes)

Create a folder `docs/ui-baseline/` and capture screenshots with this naming format:

- `P0-team-list-before.png`
- `P0-matching-before.png`
- `P0-invitations-before.png`
- `P1-circle-overview-before.png`
- `P1-tag-panel-before.png`
- `P2-auth-before.png`
- `P2-circles-before.png`

Required capture states:

- normal list state
- form state
- recommendation/result state
- invitation/review state
- empty-state if visible

## 4. Acceptance Criteria (Phase 1)

### P0: Team Management

- Recommendation cards show both matched conditions and missing conditions.
- Team status is visually scannable (Recruiting vs Locked).
- Invitation and join-request actions are grouped and readable without scrolling confusion.

### P1: Circle Detail

- The page is clearly divided into overview, tags, and actions.
- Primary button priority is obvious for join/update actions.
- Tag-related content is readable for both creators and members.

### P2: Auth + Circle Hall

- Auth page has one clear primary action per context.
- Circle cards are easy to scan with category/creator/membership status.
- Navigation to circle detail is visually clear.

## 5. Gemini Prompt Input (Ready to Use)

Use this prompt input when asking Gemini for UI ideas:

1. Keep backend and workflow unchanged.
2. Focus on clarity, hierarchy, card composition, and demo readability.
3. Prioritize pages in this order: Team Management, Circle Detail, Auth, Circle Hall.
4. Return output as:
   - one visual direction summary
   - one section per page
   - component-level suggestions
   - microcopy improvements
   - Streamlit-feasible implementation notes

## 6. Task Breakdown Board (Phase 1)

| ID | Task | Priority | Owner | Est. Time | Done Definition |
|---|---|---|---|---|---|
| UI-01 | Capture baseline screenshots | P0 | Member C | 30m | All baseline files created in docs/ui-baseline/ |
| UI-02 | Draft per-page acceptance checklist | P0 | Member A | 20m | Checklist reviewed by team |
| UI-03 | Prepare Gemini design request | P0 | Member B | 20m | Prompt finalized and sent |
| UI-04 | Team Management layout pass | P0 | Member C | 90m | Matching/invitation panels meet criteria |
| UI-05 | Circle Detail layout pass | P1 | Member D | 60m | Overview/tags/actions separated clearly |
| UI-06 | Auth + Circle Hall polish | P2 | Member B | 60m | Primary actions and card metadata improved |
| UI-07 | Demo readability review round | P0 | Member A | 30m | Team signs off on demo readability |
| UI-08 | Collect before/after evidence | P0 | Member D | 20m | Final screenshot set stored under docs/ui-evidence/ |

## 7. Implementation Notes

- Keep changes focused on page composition, wording, spacing, and grouping.
- Avoid changing business rules during UI work.
- If a UI change requires API changes, record it as a separate backlog item instead of mixing scope.

## 8. Daily Execution Plan (Suggested)

1. 00:00-00:30 baseline screenshots (UI-01)
2. 00:30-00:50 acceptance checklist review (UI-02)
3. 00:50-01:10 Gemini request handoff (UI-03)
4. 01:10-02:40 P0 Team Management pass (UI-04)
5. 02:40-03:40 P1/P2 polish pass (UI-05, UI-06)
6. 03:40-04:00 demo readability review and evidence export (UI-07, UI-08)

## 9. Completion Gate

Phase 1 is complete only when:

- P0 acceptance criteria are all met.
- Before/after screenshots are exported.
- Demo owner confirms the new UI can be presented within 10-12 minutes without confusion.
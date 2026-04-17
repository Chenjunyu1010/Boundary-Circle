# Gemini UI Design Brief

Date: 2026-04-17

## Goal

Prepare a focused UI design brief for Gemini so it can improve the visual presentation of the current Streamlit frontend without changing the core product logic or backend contract.

## Problem

The current frontend is functional but visually basic.

Current limitations:

- page layouts are utilitarian and mostly default Streamlit structure
- visual hierarchy is weak
- key workflows are understandable but not polished
- the interface does not communicate the product value strongly during demos or report review

For this project, UI is primarily a presentation layer.

That means the design goal is not to redefine product behavior. The design goal is to make the existing workflows clearer, more polished, and more persuasive in demonstrations.

## Product Decision

Delegate UI design exploration to Gemini.

This project will treat Gemini as a design assistant responsible for:

- page-level layout ideas
- visual hierarchy
- component grouping
- text and interaction polish
- presentation-oriented improvements

This project will not ask Gemini to redefine backend behavior, API shape, or core workflow rules.

## Scope

This UI brief should cover:

- current frontend page map
- current product concepts
- visual improvement goals
- workflow-specific UI priorities
- constraints Gemini must respect
- expected deliverables from Gemini

This brief should not cover:

- implementation details for Streamlit
- CSS or component code
- backend schema redesign
- business logic changes

## Current Project Context

### Product summary

Boundary Circle is a circle-based teammate discovery system with:

- user registration and login
- circle browsing and creation
- circle tag definition and submission
- team creation and invitation
- matching recommendations for teams and users

### Current frontend structure

The active frontend is a Streamlit app under `frontend/`.

Relevant pages:

- `frontend/Home.py`
- `frontend/pages/auth.py`
- `frontend/pages/circles.py`
- `frontend/pages/team_management.py`
- `frontend/views/circle_detail.py`

### Current UX intent

The interface already supports the main workflows:

- login and registration
- browse circles
- open a circle detail view
- join a circle
- manage fixed tags
- create teams
- invite members
- review matching results

The UI redesign should preserve these workflows and make them look more intentional and easier to present.

## Design Objective For Gemini

Gemini should improve visual quality and presentation value while preserving the existing product structure.

The design should aim for:

- clearer information hierarchy
- more cohesive page composition
- more polished card and panel layouts
- stronger emphasis on the matching and team-formation value proposition
- cleaner presentation of circle status, team status, and recommendation explanations

The design should feel:

- modern
- clean
- academic-project appropriate
- demo-friendly

It should not feel:

- overdesigned
- playful to the point of harming clarity
- dependent on interactions that Streamlit cannot reasonably support

## Workflow Priorities

### 1. Authentication

Pages:

- `frontend/pages/auth.py`

Goals:

- make login and registration feel more polished
- reduce the impression of a default form page
- create a cleaner first impression for demos

Gemini should improve:

- hero copy
- tab framing
- spacing
- visual emphasis on primary actions

### 2. Circle Hall

Pages:

- `frontend/pages/circles.py`

Goals:

- make circle browsing more attractive and scannable
- make status distinctions clear:
  - created by user
  - already joined
  - not joined
- improve search and filter prominence

Gemini should improve:

- circle list card layout
- category and creator metadata presentation
- create-circle entry point
- transition from list view to detail view

### 3. Circle Detail

Pages:

- `frontend/views/circle_detail.py`

Goals:

- make the circle page feel like the main product workspace
- clearly separate:
  - circle overview
  - tag definition or submission area
  - membership state
  - team management entry points

Gemini should improve:

- layout zoning
- section titles
- action button priority
- readability of tag-related content

### 4. Team Management

Pages:

- `frontend/pages/team_management.py`

Goals:

- make team creation and team discovery look structured rather than crowded
- make matching results feel valuable and interpretable
- surface invitations and team membership state more clearly

Gemini should improve:

- team list and team detail layout
- create-team form grouping
- recommendation cards
- invitation panel hierarchy
- explanation display for matched and missing conditions

### 5. Future LLM-enhanced fields

The UI brief should already anticipate future display of:

- user `freedom tag`
- team `freedom requirement`
- matching explanations derived from both fixed tags and free-text extraction

Gemini does not need to redesign backend behavior for these fields.

Gemini should only propose where these new items should appear visually:

- where a user would write their free-text profile
- where a team creator would write free-text extra requirements
- how recommendation cards might explain a match such as `羽毛球`

## Constraints Gemini Must Respect

Gemini must not change:

- the core workflow order
- backend routes
- data model assumptions
- fixed-tag matching semantics
- authentication model

Gemini should assume:

- the frontend remains Streamlit-based
- implementation should be realistic for a student project
- visual improvements matter more than advanced animation or novel UI patterns

Gemini should avoid:

- designs that require custom frontend frameworks
- designs that depend on persistent drag-and-drop layouts
- highly dynamic interactions that are awkward in Streamlit
- adding new product features disguised as design suggestions

## Recommended Design Direction

Recommended direction for Gemini:

- use a restrained, clean interface with stronger sectioning and card composition
- treat circles and teams as the core visual objects
- make recommendations visually distinct from management actions
- use concise labels and status chips
- improve demo readability before pursuing originality

This is preferred over:

- a highly experimental visual concept
- a dashboard-heavy aesthetic with unnecessary metrics
- a design that assumes custom React-like interaction capability

## Deliverables Expected From Gemini

Gemini should return a design package with:

- a high-level visual direction summary
- page-by-page layout suggestions
- component-level suggestions for cards, forms, status displays, and recommendation panels
- suggested microcopy improvements
- notes for how future `freedom tag` and `freedom requirement` fields should appear
- implementation-conscious advice that can later be adapted to Streamlit

Preferred output format:

- one concise overview
- one section per page
- flat bullet lists
- optional low-fidelity wireframe descriptions in text

## Suggested Prompt Frame For Gemini

Use Gemini as a UI/UX designer for a student software engineering project.

Give it the following instructions:

- redesign the visual presentation of an existing Streamlit app
- preserve the current workflows and backend-driven behavior
- focus on clarity, hierarchy, and demo quality
- do not invent major new product features
- include suggestions for authentication, circle browsing, circle detail, and team management pages
- account for future display of LLM-enhanced free-text matching fields

## Success Criteria

This brief is successful if Gemini produces UI guidance that:

- can be mapped back to the existing Streamlit pages
- improves presentation quality without changing core logic
- makes circle, team, and matching workflows easier to demo
- leaves implementation complexity at a reasonable level

## Follow-up

After Gemini returns its design suggestions, the next step should be:

- review which ideas are realistic in Streamlit
- keep only the high-value visual improvements
- convert approved UI changes into an implementation plan if needed

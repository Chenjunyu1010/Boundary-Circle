# Tag-Aware Team Creation Design

Date: 2026-04-16

## Goal

Make circle tag definitions behave like a controlled questionnaire schema so both member tag submission and team creation use the real circle-defined fields instead of hard-coded frontend options.

## Scope

This change will cover:

- circle tag definition modeling for selection-style fields
- backend validation for member tag submission
- frontend rendering for member tag forms
- frontend rendering for team creation based on real circle tag definitions

This change will not cover:

- generic questionnaire branching logic
- free-form string matching improvements
- new matching algorithms

## Problem

The current project already lets a circle creator define tags, but the schema is too weak for reliable selection-based data.

Current issues:

- `string` tags allow uncontrolled user input, which produces inconsistent values
- `enum` only models single-choice values and does not capture selection limits
- team creation still uses hard-coded required tag options in the frontend
- member-side tag forms and team-side tag forms are not driven by one shared schema

That makes tags less useful for matching, validation, and recommendation explanations.

## Product Decision

Circle creators should define tags as structured fields, similar to building a lightweight questionnaire.

Supported field types:

- `integer`
- `float`
- `boolean`
- `single_select`
- `multi_select`

Selection-style tags must support pre-defined choices:

- `single_select` must provide a non-empty option list
- `multi_select` must provide a non-empty option list
- `multi_select` may define a creator-controlled `max_selections`

Examples:

- `major` as `single_select` with options such as `Artificial Intelligence`, `Computer Science`, `Software Engineering`
- `tech_stack` as `multi_select` with options such as `Python`, `Java`, `React`, `SQL`, with `max_selections = 3`
- `gpa` as `float`
- `weekly_hours` as `integer`
- `remote_ok` as `boolean`

## Architecture

### Backend data model

Extend tag definition metadata so the schema can express controlled selection fields.

`TagDefinition` should represent:

- name
- data type
- required flag
- options list for selection fields
- `max_selections` for multi-select fields
- optional description

The existing `options` storage can remain JSON-serialized for now to minimize migration surface.

### Backend validation

Validation must move from "type only" to "schema-aware" validation.

Rules:

- `integer` must parse as integer
- `float` must parse as float
- `boolean` must accept explicit boolean-like values only
- `single_select` must match exactly one configured option
- `multi_select` must decode to a JSON list
- every multi-select item must exist in configured options
- multi-select submitted length must not exceed `max_selections` when configured

The backend remains the final source of truth even if frontend validation exists.

### Frontend rendering

Team creation and member tag submission should both derive inputs from normalized circle tag definitions.

Rendering rules:

- `integer` -> integer number input
- `float` -> decimal number input
- `boolean` -> checkbox
- `single_select` -> selectbox
- `multi_select` -> multiselect with selection cap messaging

The current hard-coded team `required_tags` multiselect should be replaced with a schema-driven form that reflects the active circle.

## Data Flow

### Circle creator flow

1. Creator opens circle detail admin tag management.
2. Creator defines a tag name and data type.
3. If the type is selection-based, creator must provide options.
4. If the type is multi-select, creator may also set `max_selections`.
5. Backend stores the tag definition.

### Member flow

1. Member joins the circle or updates their profile tags.
2. Frontend loads circle tag definitions.
3. Frontend renders a schema-driven form.
4. Backend validates submitted values against the stored schema.

### Team creator flow

1. Team creator opens the create team page.
2. Frontend loads current circle tag definitions.
3. Frontend renders required team fields from the same schema.
4. Submitted team requirements are constrained to valid circle-defined values.

## Validation and Error Handling

Validation errors should be consistent and explicit:

- missing options for selection tag definitions -> `400`
- invalid selection value -> `400`
- malformed multi-select payload -> `400`
- too many multi-select values -> `400`

Frontend should pre-empt obvious invalid input, but backend must still enforce all rules.

## Testing Strategy

Backend tests should cover:

- creating `single_select` and `multi_select` definitions
- rejecting selection definitions without options
- rejecting invalid member tag values
- rejecting multi-select submissions above `max_selections`

Frontend-adjacent tests or targeted helper tests should cover:

- normalized tag definitions for new data types
- dynamic team form behavior for real circle tag definitions

## Incremental Delivery

To keep risk controlled, implement in this order:

1. Extend tag schema and validation
2. Update member tag form normalization/rendering
3. Replace hard-coded team creation tag options with dynamic schema-driven rendering
4. Update docs/backlog to reflect the new behavior

## Follow-up

Possible later extensions:

- `min_selections`
- display labels distinct from stored names
- help text or placeholders
- optional "Other" choice
- migration from legacy `enum` to explicit `single_select`

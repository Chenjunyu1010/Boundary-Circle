# Value-Aware Matching Design

Date: 2026-04-16

## Goal

Make backend matching use value-level team requirements instead of only tag-name presence, while keeping existing teams and tests compatible.

## Problem

The current matching flow only compares tag names.

That means:

- a team requiring `Major` matches any user who filled `Major`, regardless of the selected value
- a team requiring `Tech Stack` matches any user who filled `Tech Stack`, regardless of the chosen options
- matching explanations are therefore coarse and can overstate fit

This became more visible after the tag schema was upgraded to support `single_select` and `multi_select`.

## Product Decision

Use value-aware matching with these rules:

- `single_select`: exact equality is required
- `multi_select`: any overlap between team requirement values and user values counts as a match
- `integer`, `float`, and `boolean`: exact equality for now
- empty or missing team requirement values do not count as value-level requirements

Compatibility rule:

- legacy teams that only store `required_tags` as tag-name lists must continue to work
- new teams may additionally store structured requirement rules

## Scope

This change will cover:

- structured storage for team requirement rules
- backend team create/read models
- value-aware matching logic for both `/matching/users` and `/matching/teams`
- compatibility with existing `required_tags`
- matching test coverage

This change will not cover:

- frontend redesign of the team creation payload beyond what already exists
- numeric range queries such as `gpa >= 3.5`
- weighted scoring or fuzzy matching

## Architecture

### Team requirement storage

Keep the existing `required_tags_json` field for compatibility.

Add a parallel structured field:

- `required_tag_rules_json`

Each rule stores:

- `tag_name`
- `expected_value`

Example:

```json
[
  {"tag_name": "Major", "expected_value": "Artificial Intelligence"},
  {"tag_name": "Tech Stack", "expected_value": ["Python", "SQL"]},
  {"tag_name": "Remote OK", "expected_value": true}
]
```

This allows:

- old teams to continue matching by tag names only
- new teams to provide value-level requirements

### API contract

`TeamCreate` and `TeamRead` should expose:

- existing `required_tags`
- new `required_tag_rules`

Creation behavior:

- if only `required_tags` is provided, preserve old behavior
- if `required_tag_rules` is also provided, persist both
- `required_tags` should remain the list of tag names for backward compatibility and explanation fallbacks

### Matching representation

Matching should stop relying only on user tag names.

Introduce helpers that build a user tag map per circle:

- key: tag name
- value: parsed user value

Examples:

- `{"Major": "Artificial Intelligence"}`
- `{"Tech Stack": ["Python", "SQL"]}`
- `{"Remote OK": true}`

Then compare each team rule against the corresponding user value.

### Matching rules

For a given rule:

- `single_select`, `string`, `integer`, `float`, `boolean`: exact equality
- `multi_select`: match when the intersection is non-empty

Coverage should be computed over structured rules when they exist.

Fallback behavior:

- if a team has no structured rules, use the existing tag-name-based coverage logic

### Explanation output

Keep the existing response fields for now:

- `matched_tags`
- `missing_required_tags`

But populate them with more specific strings when structured rules exist.

Examples:

- matched: `Major=Artificial Intelligence`
- matched: `Tech Stack overlaps with ['Python', 'SQL']`
- missing: `Major=Artificial Intelligence`
- missing: `Tech Stack needs one of ['Python', 'SQL']`

This avoids widening the API response shape in the same change.

## Data Flow

### Team creation

1. Frontend creates a team from real circle tag schema.
2. Backend receives `required_tags` and, when available, `required_tag_rules`.
3. Backend stores:
   - tag names in `required_tags_json`
   - structured rules in `required_tag_rules_json`

### User recommendation for a team

1. Backend loads the team.
2. Backend loads the team rules.
3. Backend loads candidate users' submitted tags as parsed values.
4. Backend computes:
   - structured coverage
   - Jaccard-like profile similarity
   - matched rule explanations
   - missing rule explanations

### Team recommendation for a user

1. Backend loads the current user's submitted tags as parsed values.
2. Backend compares them against each team's structured rules.
3. Backend skips teams with zero structured coverage.

## Compatibility Strategy

Use additive changes only.

- do not remove `required_tags_json`
- do not change old test data format
- do not require immediate migration of existing team rows

Decoding helpers should treat missing or malformed `required_tag_rules_json` as an empty rule list.

## Testing Strategy

Add tests for:

- `single_select` exact match success
- `single_select` mismatch failure
- `multi_select` overlap success
- `multi_select` no-overlap failure
- legacy `required_tags` matching still works
- read models preserve both `required_tags` and `required_tag_rules`

## Recommended Implementation Order

1. Add structured team rule schema and serialization helpers
2. Update team create/read API to persist and expose structured rules
3. Add matching service helpers for parsed user values and rule comparison
4. Update matching endpoints to prefer structured rules and fall back to legacy behavior
5. Update docs and tests

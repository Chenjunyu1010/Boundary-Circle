# Numeric Range Team Requirements Design

## Goal

Replace exact-match numeric team requirement inputs with bounded range inputs for `integer` and `float` tags, and treat user numeric tag values as matched when they fall inside the configured closed interval.

## Scope

- Change team creation UI in `frontend/pages/team_management.py` for numeric tags.
- Keep circle member numeric tag submission as a single scalar value.
- Change backend matching in `src/services/matching.py` so numeric rules support range payloads.
- Update summary and explanation text anywhere team required rules are rendered.

## UI Design

- Numeric tags in team creation use one row with two inputs: `Min` and `Max`.
- The two inputs are visually connected with a centered `~`.
- Empty `Min` means negative infinity.
- Empty `Max` means positive infinity.
- In `Not required` mode, the numeric inputs are disabled and show `Not required`.
- In `Required only` mode, the numeric inputs are disabled and show `Any value accepted`.
- In `Must match value` mode, both numeric inputs are enabled.
- Validation rejects `min > max`.

## Data Contract

- Numeric `expected_value` changes from scalar values like `10` to structured values:
  - `{"min": 8, "max": 12}`
  - `{"min": 8, "max": null}`
  - `{"min": null, "max": 12}`
- Non-numeric rules keep their existing payload shapes.

## Matching Semantics

- Numeric matching uses a closed interval.
- A user value matches when:
  - `min is None or user_value >= min`
  - `max is None or user_value <= max`
- Exact scalar numeric rules are preserved as backward-compatible equality rules so older data still works.

## Risks

- Existing tests assume exact numeric equality and must be updated.
- Team rule captions and match explanation strings should avoid dumping raw dicts where possible.
- Legacy stored scalar numeric rules should still decode and match correctly.

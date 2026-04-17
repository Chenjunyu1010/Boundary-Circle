# LLM Freedom Tags Design

Date: 2026-04-17

## Goal

Add one circle-specific free-text profile field for each user and one free-text recruitment field for each team, then use an LLM to extract structured matching signals from both texts without replacing the existing fixed-tag matching flow.

## Problem

The current system only matches on fixed circle tags and structured team requirements.

That means:

- users cannot express extra identity or preferences outside the circle-defined schema
- team creators cannot express extra natural-language requirements outside the structured fixed tags
- matching cannot connect related free-text statements such as:
  - user: `喜欢打羽毛球`
  - team requirement: `了解羽毛球`

This is a product gap because some useful signals are too specific, too contextual, or too costly to model as fixed tags for every circle.

## Product Decision

Introduce a new free-text matching channel in parallel with the existing fixed-tag channel.

The new feature will add:

- one user-side free-text field per circle membership
- one team-side free-text requirement field per team
- an LLM extraction step that converts both texts into the same structured JSON schema
- a combined matching score that keeps fixed tags as the primary signal and uses free-text extraction as a secondary signal

This change will not replace:

- `TagDefinition`
- `UserTag`
- `required_tags`
- `required_tag_rules`

The existing fixed-tag workflow remains the stable core of the recommendation system.

## Scope

This change will cover:

- persistent storage for user free-text profile content
- persistent storage for team free-text requirement content
- LLM-backed extraction into a normalized JSON profile
- free-text-aware matching score computation
- matching explanations for free-text hits
- failure fallback when LLM extraction is unavailable

This change will not cover:

- vector embedding similarity
- negative-preference avoidance matching
- replacing fixed tags with natural language
- fully asynchronous background extraction pipelines

Vector-based semantic matching should be documented as future work in the report.

## Architecture

### Two parallel matching channels

Matching will be computed from two independent channels:

- fixed-tag channel
- free-text channel

The fixed-tag channel keeps current behavior:

- `required_tag_rules` if present
- otherwise legacy `required_tags`

The free-text channel adds:

- user `freedom_tag_text`
- team `freedom_requirement_text`
- LLM-extracted normalized profiles from both texts

The final recommendation score should combine both channels instead of letting the LLM directly rank candidates.

### Why free-text should not be stored as a normal tag

The new user free-text field should not be modeled as `TagDefinition + UserTag`.

Reasons:

- fixed tags are circle-defined schema fields
- the new free-text field is one built-in per-circle user profile area, not an admin-defined questionnaire field
- it has a different validation path
- it needs an attached extracted profile JSON

For the same reason, team-side free-text requirements should not be merged into `required_tag_rules`.

## Data Model Design

### User-side storage

Store the new user free-text profile on the circle membership record.

Recommended location:

- extend `CircleMember` in `src/models/tags.py`

Recommended fields:

- `freedom_tag_text: str = ""`
- `freedom_tag_profile_json: str = "{\"keywords\":[],\"traits\":[],\"domains\":[]}"`

Rationale:

- the text belongs to a user within a specific circle
- it should travel with circle membership
- it is independent from fixed tag definitions

### Team-side storage

Store the new team recruitment text directly on the `Team` model.

Recommended location:

- extend `Team` in `src/models/teams.py`

Recommended fields:

- `freedom_requirement_text: str = ""`
- `freedom_requirement_profile_json: str = "{\"keywords\":[],\"traits\":[],\"domains\":[]}"`

Rationale:

- the text belongs to one team posting
- it is an additive recruitment signal, not a fixed tag rule

### Structured extraction schema

Both user text and team requirement text should be extracted into the same schema:

```json
{
  "keywords": [],
  "traits": [],
  "domains": []
}
```

Field meanings:

- `keywords`: explicit topics, interests, skills, or domains of knowledge
- `traits`: collaboration style or personal working characteristics
- `domains`: coarse categories such as `运动`, `学习`, or `开发`

This schema is intentionally small for version one because:

- it is easy to explain
- it is easy to validate
- it is easy to test
- it is enough for examples like `羽毛球`

## API Design

### User-side API

Users need a way to save or update their free-text profile for a circle.

Recommended additive endpoint:

- `PUT /circles/{circle_id}/profile`

Example payload:

```json
{
  "freedom_tag_text": "喜欢打羽毛球，沟通直接，希望队友高效。"
}
```

Recommended behavior:

1. verify the current user is a member or creator of the circle
2. persist `freedom_tag_text`
3. call the extraction service
4. persist validated `freedom_tag_profile_json`
5. return both raw text and extracted profile

This endpoint should be separate from fixed tag submission so the two concepts stay decoupled.

### Team creation API

Extend `TeamCreate` with:

- `freedom_requirement_text: str = ""`

Example payload:

```json
{
  "name": "Study Group 1",
  "description": "Exam preparation",
  "circle_id": 3,
  "max_members": 4,
  "required_tag_rules": [
    {"tag_name": "GPA", "expected_value": 3.8}
  ],
  "freedom_requirement_text": "希望队友了解羽毛球，平时愿意主动沟通。"
}
```

Recommended behavior:

1. persist the raw free-text requirement
2. call the extraction service
3. persist the validated extracted profile JSON

### Read APIs

Team reads and user profile reads should include:

- the raw text field
- the extracted structured profile if needed by the frontend

At minimum, team reads should expose `freedom_requirement_text`.

## LLM Extraction Design

### Service boundary

The LLM should only be responsible for extraction, not ranking.

The backend remains responsible for:

- validating extraction output
- normalizing extracted values
- calculating scores
- generating explanations

This keeps recommendation behavior deterministic and testable even when extraction is probabilistic.

### Required extraction output

The LLM must output only:

```json
{
  "keywords": [],
  "traits": [],
  "domains": []
}
```

Hard rules:

- every field must be a string array
- every field may contain at most 5 entries
- target 3 to 5 short phrases when enough information exists
- extract nouns or noun phrases where possible
- do not output explanations, comments, markdown, or extra fields
- return empty arrays when the text does not contain confident positive matching signals
- detect negation and do not convert negative statements into positive extracted features

Examples of forbidden mis-extraction:

- `不喜欢羽毛球` must not produce `羽毛球`
- `不了解羽毛球` must not produce `羽毛球`
- `不想和太强势的人组队` must not produce a positive trait such as `强势`
- `不是很擅长沟通` must not produce `沟通`

Version-one rule:

- only extract positive signals that can help matching
- do not introduce `negative_keywords` or other negative-profile fields yet

This keeps the first implementation small and avoids widening matching semantics beyond the agreed scope.

### Post-processing and validation

The backend must not trust raw model output directly.

Required post-processing:

- parse JSON safely
- fill missing fields with empty arrays
- discard non-string items
- trim whitespace
- deduplicate values
- cap each field at 5 items
- optionally normalize obvious duplicates or phrasing variants

If parsing or validation fails, the backend should store the empty profile shape instead of blocking the request.

## Matching Design

### Free-text scoring

The free-text channel compares the team extracted profile against the user extracted profile.

Recommended per-field scoring:

- `keywords_score = 0.0 if len(team.keywords) == 0 else overlap(user.keywords, team.keywords) / len(team.keywords)`
- `traits_score = 0.0 if len(team.traits) == 0 else overlap(user.traits, team.traits) / len(team.traits)`
- `domains_score = 0.0 if len(team.domains) == 0 else overlap(user.domains, team.domains) / len(team.domains)`

Recommended weighted free-text score:

```text
freedom_score =
0.6 * keywords_score +
0.3 * traits_score +
0.1 * domains_score
```

Rationale:

- `keywords` carry the most precise signal
- `traits` matter, but are less precise than direct topic overlap
- `domains` are broad and should only slightly influence rank

If the team free-text requirement is empty, `freedom_score` should be `0.0`.

If the user free-text profile is empty or extraction produced no positive signals, `freedom_score` should also be `0.0`.

If the team text exists but extraction yields an empty array for one field, that field's score should still resolve to `0.0` rather than dividing by zero.

### Combined score

Keep fixed tags as the dominant signal.

Recommended total score:

```text
final_score =
0.7 * fixed_score +
0.3 * freedom_score
```

Where:

- `fixed_score` is the current structured requirement coverage or legacy tag-name coverage
- `freedom_score` is the new free-text structured overlap score

This keeps backward behavior stable and prevents LLM extraction noise from overwhelming the established tag-based logic.

### Matching explanations

Add explanation fields so the frontend can show why a result was recommended.

Recommended additions:

- `freedom_score`
- `final_score`
- `matched_freedom_keywords`
- `missing_freedom_keywords`

This will allow explanations like:

- matched fixed tags: `GPA=3.8`
- matched free-text keywords: `羽毛球`

## Failure Handling

### Extraction failure policy

The request should still succeed if LLM extraction fails.

Required behavior:

- always save the raw text
- if extraction fails, save an empty normalized profile:

```json
{
  "keywords": [],
  "traits": [],
  "domains": []
}
```

- return a status flag or message that extraction failed
- keep matching available, with `freedom_score = 0.0` for that item

This avoids turning LLM uptime into a blocker for joining circles or creating teams.

### Why synchronous fallback is acceptable

For version one, synchronous extraction on save is acceptable because:

- it keeps implementation small
- extracted profile freshness is immediate
- it avoids background job complexity

If extraction latency becomes a product problem later, asynchronous refresh can be a follow-up improvement.

## Testing Strategy

### Unit tests

Add tests for:

- valid profile normalization
- malformed JSON fallback
- non-string item cleanup
- per-field size cap
- overlap scoring
- total score combination
- negation safety for extraction post-processing contracts

### Service tests

Mock the LLM client and verify:

- valid JSON extraction
- missing field extraction
- extra-field output is ignored
- parse failure falls back to empty profile
- timeout or API error falls back to empty profile

### API and integration tests

Add tests for:

- saving a user `freedom_tag_text`
- creating a team with `freedom_requirement_text`
- matching that succeeds through free-text overlap such as `羽毛球`
- matching that does not falsely succeed on negated text such as `不喜欢羽毛球`
- mixed fixed-tag plus free-text ranking behavior

## Report Positioning

This design should be described in the report as:

- an LLM-assisted feature extraction pipeline
- a deterministic recommendation system built on top of extracted structured signals
- a pragmatic compromise between semantic flexibility and system explainability

Future work should mention:

- embedding-based semantic similarity
- richer synonym normalization
- explicit negative preference modeling
- asynchronous extraction or batch refresh

## Recommended Implementation Order

1. Add persistence fields for user and team free-text profiles
2. Add profile schema helpers and serialization utilities
3. Implement the extraction service boundary and validation layer
4. Add user profile save/update API
5. Extend team create/read API
6. Extend matching scoring and explanation output
7. Add failure-path and negation-focused tests
8. Update README and report-facing docs

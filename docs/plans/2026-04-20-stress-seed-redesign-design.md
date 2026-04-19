# Stress Seed Redesign Design

## Goal

Rebuild the `stress` seed dataset so it better exercises the current product:

- larger scale: 40-60 users
- more circle diversity: not only work/study, also sports and entertainment
- richer tags: include `float` fields such as `GPA`
- richer matching: numeric team rules should use range payloads instead of exact numeric equality
- more overlap: users should participate in multiple circles to create more complex relationships

## Target Shape

- 48 users
- 8 circles
- 32 teams
- 32+ invitations

## Circle Families

- Study / project:
  - `AI Factory`
  - `Product Garage`
  - `Research Exchange`
  - `Open Source Sprint`
- Sports:
  - `Badminton Club`
  - `City Run Crew`
- Entertainment:
  - `Board Game Night`
  - `Indie Music Jam`

## Tag Families

### Study / project circles

- `Major` (`single_select`)
- `Preferred Role` (`single_select`)
- `Tech Stack` (`multi_select`)
- `Weekly Hours` (`integer`)
- `GPA` (`float`, 0.0-4.0)
- `Willing To Lead` (`boolean`)
- `Focus Track` (`single_select`)

### Sports circles

- `Sport Level` (`single_select`)
- `Preferred Position` (`single_select`)
- `Available Days` (`multi_select`)
- `Weekly Hours` (`integer`)
- `Stamina Score` (`float`)
- `Willing To Lead` (`boolean`)
- `Injury Concern` (`boolean`)

### Entertainment circles

- `Favorite Genre` (`single_select`)
- `Play Style` (`single_select`)
- `Instruments` or `Game Types` (`multi_select`)
- `Budget Level` (`integer`)
- `Event Frequency` (`single_select`)
- `Night Owl` (`boolean`)
- `Social Energy` (`float`)

## Matching Design

- Each circle should have 4 teams.
- Mix plain required tags and structured tag rules.
- Numeric rules must prefer range objects:
  - `{"min": 8, "max": 12}`
  - `{"min": 3.2, "max": 4.0}`
  - `{"min": null, "max": 10}`
  - `{"min": 6, "max": null}`
- Keep non-numeric rules mixed in so the dataset covers:
  - tag presence only
  - exact single-select match
  - multi-select overlap
  - numeric closed interval
  - open-ended numeric interval

## Distribution

- `GPA` should cluster around realistic student values, not uniform random:
  - most users in `2.8-3.8`
  - some low values near `2.2-2.7`
  - some high values near `3.9-4.0`
- `Weekly Hours` should cluster around `4-14`, with a few lighter/heavier cases.
- Some users should miss selected tags in selected circles to preserve incomplete-profile cases.

## Relationship Complexity

- Users should appear in 2-4 circles.
- Cross-type memberships should exist:
  - e.g. someone in `AI Factory` and `Badminton Club`
  - someone in `Product Garage` and `Board Game Night`
- Team creators and invitees should create pending, accepted, rejected, and join-request states.

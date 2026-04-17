# Seed Data Design

## Goal

Provide a manual-only database seed workflow for local demo and exploratory testing without affecting existing real data in `data/boundary_circle.db`.

## Scope

- Add a single script at `scripts/seed_data.py`.
- Support two seed datasets:
  - `demo`: compact, presentation-friendly records
  - `stress`: larger and more varied records for manual testing
- Support optional cleanup for seeded records only:
  - `python scripts/seed_data.py demo --reset`
  - `python scripts/seed_data.py stress --reset`

## Non-Goals

- No automatic seeding on application startup.
- No hidden reset of unrelated data.
- No production-grade fixture management system.

## Design

### Invocation Model

The script runs manually from the repo root and uses the existing SQLModel engine and table bootstrap:

- `python scripts/seed_data.py demo`
- `python scripts/seed_data.py stress`
- `python scripts/seed_data.py demo --reset`
- `python scripts/seed_data.py stress --reset`

### Data Ownership Markers

Every seeded record must be attributable to one dataset only.

- Users:
  - usernames prefixed with `seed_demo_` or `seed_stress_`
  - emails in a reserved local namespace such as `seed_demo_*@example.test`
- Circles:
  - names prefixed with `[SEED DEMO]` or `[SEED STRESS]`
- Teams:
  - names prefixed with `[SEED DEMO]` or `[SEED STRESS]`
- Tags:
  - tag names may remain realistic, but are reachable only through seeded circles

Cleanup must use these ownership boundaries plus relationship traversal, not broad table wipes.

### Write Strategy

- Reuse `src.db.database.create_db_and_tables()` and `src.db.database.engine`.
- Reuse `src.services.users.create_user_account()` for password hashing and duplicate checks.
- Insert circles, memberships, tag definitions, user tags, teams, team members, and invitations directly through a SQLModel session.

### Reset Strategy

`--reset` removes only the selected dataset.

Reset order:

1. Load seeded users and circles for the selected dataset marker.
2. Delete invitations tied to seeded teams or seeded users.
3. Delete team memberships tied to seeded teams or seeded users.
4. Delete seeded teams.
5. Delete user tags and tag definitions for seeded circles.
6. Delete circle memberships for seeded circles or seeded users.
7. Delete seeded circles.
8. Delete seeded users.

This preserves unrelated records even if they coexist in the same database.

### Idempotency

- Running `demo` or `stress` multiple times without `--reset` should not create duplicates.
- The simplest acceptable behavior is:
  - perform selected dataset cleanup first
  - recreate the dataset deterministically
- This keeps the script repeatable and reduces merge-state complexity.

## Dataset Shape

### Demo Dataset

Small and readable for report screenshots and walkthroughs:

- 6 to 8 users
- 2 circles
- 4 to 5 tag definitions per circle
- 3 to 4 teams
- invitations across `pending`, `accepted`, `rejected`
- examples of both `required_tags` and `required_tag_rules`

### Stress Dataset

Larger and more irregular for manual testing:

- 15 to 20 users
- 3 to 4 circles
- 5 to 6 tag definitions per circle
- 8 to 12 teams
- overlapping memberships across circles
- mixed single-select and multi-select values
- invitations across all statuses
- teams with varied capacities and requirement rules

## Verification Requirements

- Seeding creates the expected entities and relationships.
- Re-running a dataset remains deterministic.
- `demo --reset` and `stress --reset` remove only the corresponding seed data.
- Non-seed data remains untouched after reset.

## Risks

- `Circle.name` is globally unique, so seed names must remain dataset-specific.
- Cleanup queries that rely on names alone are too fragile; user and circle ownership markers should drive selection.
- Direct inserts must still respect current domain constraints such as valid password hashing and team capacity semantics.

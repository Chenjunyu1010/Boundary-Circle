# SQLite Schema Upgrade Design

## Summary

This design adds a minimal SQLite-only schema upgrade path to keep an existing local
database compatible with the current SQLModel definitions.

The problem is not new table creation. The problem is that
`SQLModel.metadata.create_all()` does not add newly introduced columns to tables that
already exist. In this repository, older `data/boundary_circle.db` files can therefore
miss:

- `tagdefinition.max_selections`
- `team.required_tag_rules_json`

That mismatch causes runtime query failures because SQLModel selects all mapped columns.

## Goals

- Keep existing local SQLite databases usable after model changes that add columns.
- Fix the known compatibility gap for `TagDefinition.max_selections` and
  `Team.required_tag_rules_json`.
- Avoid introducing a full migration framework for this course project.

## Non-Goals

- Full migration history or versioned rollback support.
- Complex schema rewrites such as renames, type changes, or data backfills.
- General support for non-SQLite databases.

## Recommended Approach

Add a lightweight startup upgrade step in `src/db/database.py`.

Startup flow:

1. Run `SQLModel.metadata.create_all(engine)` to create any missing tables.
2. If the active engine is SQLite, inspect the live schema with `PRAGMA table_info`.
3. If required columns are missing, add them with `ALTER TABLE ... ADD COLUMN ...`.

Initial required upgrades:

- `tagdefinition.max_selections INTEGER`
- `team.required_tag_rules_json VARCHAR NOT NULL DEFAULT '[]'`

## Why This Approach

This is the smallest change that fixes the current root cause.

- It repairs old local databases without asking contributors to delete their data.
- It keeps the logic close to the existing database bootstrap path.
- It matches the backlog item, which explicitly asks for minimal startup upgrade
  handling rather than immediate Alembic adoption.

## Data Compatibility

The added column defaults are chosen to match current application behavior.

### `tagdefinition.max_selections`

- Add as nullable integer.
- Existing rows become `NULL`.
- Current tag validation already treats `None` as "no extra selection cap".

### `team.required_tag_rules_json`

- Add as `NOT NULL DEFAULT '[]'`.
- Existing rows become the empty rules list.
- `decode_required_tag_rules()` already interprets `'[]'` as no structured rules,
  preserving compatibility for legacy teams.

## Error Handling

The upgrade function should:

- Do nothing for non-SQLite engines.
- Be idempotent by checking column existence before altering a table.
- Fail loudly on SQL errors rather than silently swallowing upgrade failures.

This keeps startup behavior predictable. If the schema cannot be upgraded, the app
should not continue under the false assumption that the database is compatible.

## Testing Strategy

Existing tests only use a fresh in-memory SQLite database, so they do not exercise
old-schema upgrade behavior.

Add focused tests that:

1. Create a SQLite database with the old `tagdefinition` schema.
2. Create a SQLite database with the old `team` schema.
3. Run the new upgrade function.
4. Assert with `PRAGMA table_info` that the missing columns now exist.
5. Optionally verify that selecting through the current SQLModel mappings no longer
   fails after the upgrade.

## Alternatives Considered

### Keep current behavior

Rejected because the issue is already reproducible against the local repository
database and causes real runtime failures.

### Adopt Alembic now

Reasonable long term, but heavy for the immediate problem. It adds migration tooling,
workflow changes, and more surface area than this repository currently needs.

## Follow-Up

If schema changes become more frequent or start requiring data transformations, the
project should revisit a proper migration tool. This lightweight upgrade path is meant
to solve the current local SQLite compatibility gap, not replace a real migration
system forever.

# SQLite Schema Upgrade Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a lightweight SQLite startup upgrade path that patches missing columns in old local databases so the current SQLModel mappings work without deleting existing data.

**Architecture:** Keep the change inside the existing database bootstrap layer. After `create_all()`, run a SQLite-only schema inspection and add known missing columns with idempotent `ALTER TABLE` statements. Cover the behavior with targeted old-schema upgrade tests instead of only relying on fresh-database tests.

**Tech Stack:** Python, FastAPI, SQLModel, SQLAlchemy, SQLite, pytest

---

### Task 1: Add failing upgrade coverage for old SQLite schemas

**Files:**
- Create: `tests/test_db_schema_upgrade.py`
- Reference: `src/db/database.py`

**Step 1: Write the failing test**

Create a test file that:

- builds a temporary SQLite engine
- creates an old `tagdefinition` table without `max_selections`
- creates an old `team` table without `required_tag_rules_json`
- calls the new upgrade function
- asserts through `PRAGMA table_info(...)` that both columns exist afterward

Include two focused tests:

```python
def test_upgrade_adds_missing_tagdefinition_max_selections_column():
    ...


def test_upgrade_adds_missing_team_required_tag_rules_json_column():
    ...
```

**Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/test_db_schema_upgrade.py -v
```

Expected: FAIL because the upgrade function does not exist yet.

**Step 3: Write minimal implementation hooks**

In the test, import the future function from `src.db.database`, for example:

```python
from src.db.database import run_sqlite_schema_upgrades
```

This keeps the failure anchored to the intended API surface.

**Step 4: Run test again to verify the missing symbol failure is clear**

Run:

```bash
pytest tests/test_db_schema_upgrade.py -v
```

Expected: FAIL with import or attribute error for `run_sqlite_schema_upgrades`.

**Step 5: Commit**

```bash
git add tests/test_db_schema_upgrade.py
git commit -m "test: add sqlite schema upgrade coverage"
```

### Task 2: Implement SQLite schema inspection and upgrade helpers

**Files:**
- Modify: `src/db/database.py`
- Reference: `src/models/tags.py`
- Reference: `src/models/teams.py`

**Step 1: Write the minimal implementation**

Add helpers in `src/db/database.py` for:

- checking whether the engine dialect is SQLite
- reading existing column names from `PRAGMA table_info(table_name)`
- conditionally applying `ALTER TABLE ... ADD COLUMN ...`
- running all known SQLite upgrades from one public function

The public shape should be simple:

```python
def run_sqlite_schema_upgrades(engine) -> None:
    ...
```

Known upgrades to encode:

```sql
ALTER TABLE tagdefinition ADD COLUMN max_selections INTEGER
ALTER TABLE team ADD COLUMN required_tag_rules_json VARCHAR NOT NULL DEFAULT '[]'
```

**Step 2: Keep it idempotent**

Before each `ALTER TABLE`, check existing columns and skip the statement if the column
already exists.

**Step 3: Wire it into startup**

Update `create_db_and_tables()` so it runs:

```python
SQLModel.metadata.create_all(engine)
run_sqlite_schema_upgrades(engine)
```

**Step 4: Run the focused test**

Run:

```bash
pytest tests/test_db_schema_upgrade.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/db/database.py tests/test_db_schema_upgrade.py
git commit -m "feat: add lightweight sqlite schema upgrades"
```

### Task 3: Verify application compatibility against the upgraded schema

**Files:**
- Modify: `tests/test_db_schema_upgrade.py`
- Reference: `src/models/tags.py`
- Reference: `src/models/teams.py`

**Step 1: Extend tests with mapped-model verification**

After upgrade, add a small assertion that current mapped queries no longer fail:

```python
with Session(engine) as session:
    session.exec(select(TagDefinition)).all()
    session.exec(select(Team)).all()
```

Use empty tables if possible. The point is column compatibility, not business data.

**Step 2: Run the targeted test file**

Run:

```bash
pytest tests/test_db_schema_upgrade.py -v
```

Expected: PASS

**Step 3: Run adjacent regression coverage**

Run:

```bash
pytest tests/test_tags_api.py tests/test_teams_api.py -v
```

Expected: PASS

**Step 4: Commit**

```bash
git add tests/test_db_schema_upgrade.py
git commit -m "test: verify upgraded sqlite schema works with current models"
```

### Task 4: Update project docs to describe the lightweight upgrade behavior

**Files:**
- Modify: `README.md`
- Modify: `docs/2026-04-15-project-backlog.md`

**Step 1: Update README**

Add a short note in local development or database sections explaining:

- the app uses SQLite locally
- startup now patches known missing columns in older local database files
- this is a lightweight compatibility layer, not a full migration framework

**Step 2: Update backlog status**

Mark item `6a` as completed if the implementation and tests are done.

**Step 3: Run quick verification**

Run:

```bash
pytest tests/test_db_schema_upgrade.py tests/test_tags_api.py tests/test_teams_api.py -v
```

Expected: PASS

**Step 4: Commit**

```bash
git add README.md docs/2026-04-15-project-backlog.md
git commit -m "docs: document sqlite schema upgrade handling"
```

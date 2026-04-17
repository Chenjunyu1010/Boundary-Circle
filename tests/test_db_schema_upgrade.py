from pathlib import Path

from sqlalchemy import create_engine, text
from sqlmodel import Session, select

from src.db.database import run_sqlite_schema_upgrades
from src.models.tags import TagDefinition
from src.models.teams import Team


def _create_old_schema(engine) -> None:
    statements = [
        """
        CREATE TABLE tagdefinition (
            id INTEGER NOT NULL PRIMARY KEY,
            circle_id INTEGER NOT NULL,
            name VARCHAR NOT NULL,
            data_type VARCHAR(7) NOT NULL,
            required BOOLEAN NOT NULL,
            options VARCHAR,
            description VARCHAR
        )
        """,
        """
        CREATE TABLE team (
            id INTEGER NOT NULL PRIMARY KEY,
            name VARCHAR NOT NULL,
            description VARCHAR NOT NULL,
            circle_id INTEGER NOT NULL,
            creator_id INTEGER NOT NULL,
            max_members INTEGER NOT NULL,
            status VARCHAR(10) NOT NULL,
            required_tags_json VARCHAR NOT NULL
        )
        """,
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _column_names(engine, table_name: str) -> set[str]:
    with engine.connect() as connection:
        rows = connection.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return {row[1] for row in rows}


def test_upgrade_adds_missing_tagdefinition_max_selections_column(tmp_path: Path):
    db_path = tmp_path / "old-schema.db"
    engine = create_engine(f"sqlite:///{db_path}")
    _create_old_schema(engine)

    run_sqlite_schema_upgrades(engine)

    assert "max_selections" in _column_names(engine, "tagdefinition")


def test_upgrade_adds_missing_team_required_tag_rules_json_column(tmp_path: Path):
    db_path = tmp_path / "old-schema.db"
    engine = create_engine(f"sqlite:///{db_path}")
    _create_old_schema(engine)

    run_sqlite_schema_upgrades(engine)

    assert "required_tag_rules_json" in _column_names(engine, "team")


def test_upgrade_backfills_required_tag_rules_json_for_existing_team_rows(tmp_path: Path):
    db_path = tmp_path / "old-schema.db"
    engine = create_engine(f"sqlite:///{db_path}")
    _create_old_schema(engine)

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO team (
                    id,
                    name,
                    description,
                    circle_id,
                    creator_id,
                    max_members,
                    status,
                    required_tags_json
                ) VALUES (
                    1,
                    'Existing Team',
                    'Created before upgrade',
                    1,
                    1,
                    4,
                    'Recruiting',
                    '[]'
                )
                """
            )
        )

    run_sqlite_schema_upgrades(engine)

    with engine.connect() as connection:
        required_tag_rules_json = connection.execute(
            text("SELECT required_tag_rules_json FROM team WHERE id = 1")
        ).scalar_one()

    assert required_tag_rules_json == "[]"


def test_upgraded_schema_supports_current_sqlmodel_queries(tmp_path: Path):
    db_path = tmp_path / "old-schema.db"
    engine = create_engine(f"sqlite:///{db_path}")
    _create_old_schema(engine)

    run_sqlite_schema_upgrades(engine)

    with Session(engine) as session:
        assert session.exec(select(TagDefinition)).all() == []
        assert session.exec(select(Team)).all() == []


def test_running_sqlite_schema_upgrades_twice_is_safe(tmp_path: Path):
    db_path = tmp_path / "old-schema.db"
    engine = create_engine(f"sqlite:///{db_path}")
    _create_old_schema(engine)

    run_sqlite_schema_upgrades(engine)
    run_sqlite_schema_upgrades(engine)

    with Session(engine) as session:
        assert session.exec(select(TagDefinition)).all() == []
        assert session.exec(select(Team)).all() == []

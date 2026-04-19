from pathlib import Path

from sqlalchemy import create_engine, text
from sqlmodel import Session, select

from src.db.database import run_sqlite_schema_upgrades
from src.models.tags import TagDefinition
from src.models.teams import Team


def _create_old_schema(engine) -> None:
    statements = [
        """
        CREATE TABLE circlemember (
            id INTEGER NOT NULL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            circle_id INTEGER NOT NULL,
            joined_at TIMESTAMP NOT NULL,
            role VARCHAR(6) NOT NULL,
            FOREIGN KEY(user_id) REFERENCES user(id),
            FOREIGN KEY(circle_id) REFERENCES circle(id),
            UNIQUE(user_id, circle_id)
        )
        """,
        """
        CREATE TABLE circle (
            id INTEGER NOT NULL PRIMARY KEY,
            name VARCHAR NOT NULL,
            description VARCHAR NOT NULL,
            creator_id INTEGER NOT NULL,
            FOREIGN KEY(creator_id) REFERENCES user(id)
        )
        """,
        """
        CREATE TABLE user (
            id INTEGER NOT NULL PRIMARY KEY,
            username VARCHAR NOT NULL,
            email VARCHAR NOT NULL,
            hashed_password VARCHAR NOT NULL
        )
        """,
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
        """
        CREATE TABLE userprofile (
            id INTEGER NOT NULL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            gender VARCHAR,
            birthday DATE,
            bio VARCHAR,
            show_full_name BOOLEAN NOT NULL,
            show_gender BOOLEAN NOT NULL,
            show_birthday BOOLEAN NOT NULL,
            show_email BOOLEAN NOT NULL,
            show_bio BOOLEAN NOT NULL
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


def test_upgrade_adds_missing_userprofile_prompt_column(tmp_path: Path):
    db_path = tmp_path / "old-schema.db"
    engine = create_engine(f"sqlite:///{db_path}")
    _create_old_schema(engine)

    run_sqlite_schema_upgrades(engine)

    assert "profile_prompt_dismissed" in _column_names(engine, "userprofile")


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


def test_upgrade_adds_freedom_tag_columns_to_circle_member_and_team(tmp_path: Path):
    # Use the existing old schema that doesn't have freedom tag columns
    db_path = tmp_path / "old-schema.db"
    engine = create_engine(f"sqlite:///{db_path}")
    _create_old_schema(engine)

    # Verify freedom columns don't exist before upgrade
    assert "freedom_tag_text" not in _column_names(engine, "circlemember")
    assert "freedom_tag_profile_json" not in _column_names(engine, "circlemember")
    assert "freedom_requirement_text" not in _column_names(engine, "team")
    assert "freedom_requirement_profile_json" not in _column_names(engine, "team")

    run_sqlite_schema_upgrades(engine)

    assert "freedom_tag_text" in _column_names(engine, "circlemember")
    assert "freedom_tag_profile_json" in _column_names(engine, "circlemember")
    assert "freedom_requirement_text" in _column_names(engine, "team")
    assert "freedom_requirement_profile_json" in _column_names(engine, "team")


import os
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, Session, create_engine

# Use a local SQLite database file outside the repo root clutter.
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
sqlite_file_name = data_dir / "boundary_circle.db"
sqlite_url = f"sqlite:///{sqlite_file_name.as_posix()}"

SQL_ECHO = os.environ.get("SQL_ECHO", "false").strip().lower() == "true"

# Keep SQL echo opt-in so production logs stay readable.
engine = create_engine(sqlite_url, echo=SQL_ECHO)


def _is_sqlite_engine(db_engine: Engine) -> bool:
    return db_engine.dialect.name == "sqlite"


def _get_existing_columns(db_engine: Engine, table_name: str) -> set[str]:
    with db_engine.connect() as connection:
        rows = connection.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return {row[1] for row in rows}


def _add_column_if_missing(db_engine: Engine, table_name: str, column_name: str, ddl: str) -> None:
    existing_columns = _get_existing_columns(db_engine, table_name)
    if column_name in existing_columns:
        return

    with db_engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))


def run_sqlite_schema_upgrades(db_engine: Engine) -> None:
    if not _is_sqlite_engine(db_engine):
        return

    _add_column_if_missing(
        db_engine,
        "tagdefinition",
        "max_selections",
        "max_selections INTEGER",
    )
    _add_column_if_missing(
        db_engine,
        "team",
        "required_tag_rules_json",
        "required_tag_rules_json VARCHAR NOT NULL DEFAULT '[]'",
    )
    _add_column_if_missing(
        db_engine,
        "userprofile",
        "profile_prompt_dismissed",
        "profile_prompt_dismissed BOOLEAN NOT NULL DEFAULT 0",
    )
    # Freedom tag columns for circlemember
    _add_column_if_missing(
        db_engine,
        "circlemember",
        "freedom_tag_text",
        "freedom_tag_text VARCHAR NOT NULL DEFAULT ''",
    )
    _add_column_if_missing(
        db_engine,
        "circlemember",
        "freedom_tag_profile_json",
        "freedom_tag_profile_json VARCHAR NOT NULL DEFAULT '{\"keywords\": []}'",
    )
    # Freedom tag columns for team
    _add_column_if_missing(
        db_engine,
        "team",
        "freedom_requirement_text",
        "freedom_requirement_text VARCHAR NOT NULL DEFAULT ''",
    )
    _add_column_if_missing(
        db_engine,
        "team",
        "freedom_requirement_profile_json",
        "freedom_requirement_profile_json VARCHAR NOT NULL DEFAULT '{\"keywords\": []}'",
    )


def create_db_and_tables():
    # This will create all tables defined using SQLModel
    SQLModel.metadata.create_all(engine)
    run_sqlite_schema_upgrades(engine)

def get_session():
    # Dependency to get a database session for each request
    with Session(engine) as session:
        yield session

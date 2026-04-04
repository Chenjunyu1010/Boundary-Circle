from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine

# Use a local SQLite database file outside the repo root clutter.
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
sqlite_file_name = data_dir / "boundary_circle.db"
sqlite_url = f"sqlite:///{sqlite_file_name.as_posix()}"

# echo=True will print all SQL queries to the console, helpful for debugging
engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    # This will create all tables defined using SQLModel
    SQLModel.metadata.create_all(engine)

def get_session():
    # Dependency to get a database session for each request
    with Session(engine) as session:
        yield session

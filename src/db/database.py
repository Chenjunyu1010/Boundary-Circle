from sqlmodel import SQLModel, create_engine, Session

# Use local SQLite database file
sqlite_file_name = "boundary_circle.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# echo=True will print all SQL queries to the console, helpful for debugging
engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    # This will create all tables defined using SQLModel
    SQLModel.metadata.create_all(engine)

def get_session():
    # Dependency to get a database session for each request
    with Session(engine) as session:
        yield session

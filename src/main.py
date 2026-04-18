from fastapi import FastAPI
from contextlib import asynccontextmanager

# Import database and models
from src.db.database import create_db_and_tables
from src.models.core import Circle, User  # Keep this to ensure models are registered
from src.models.profile import UserProfile
from src.models.tags import CircleMember, TagDefinition, UserTag
from src.models.teams import Invitation, Team, TeamMember

# Import routers
from src.api import auth, circles, matching, profile, tags, teams, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Ensures database tables are created on startup.
    """
    print("Creating database tables...")
    create_db_and_tables()
    yield
    print("Shutting down...")


app = FastAPI(
    title="Boundary Circle API",
    description="Backend API for Team 12 Software Engineering Project",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
def read_root() -> dict[str, str]:
    """Root endpoint providing a simple welcome payload."""
    return {
        "message": "Welcome to Boundary Circle API",
        "status": "active",
        "docs_url": "/docs",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy"}


# Include routers
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(circles.router)
app.include_router(tags.router)
app.include_router(teams.router)
app.include_router(matching.router)

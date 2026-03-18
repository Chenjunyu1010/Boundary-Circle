from fastapi import FastAPI
from contextlib import asynccontextmanager

# Import database and models
from src.db.database import create_db_and_tables
from src.models.core import User, Circle  # Keep this to ensure models are registered
from src.models.tags import TagDefinition, UserTag, CircleMember # <--- 新增这行

# Import routers (we will create these next)
from src.api import auth, users, circles, tags  # <--- 修改这行

# This runs when the app starts
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if they don't exist
    print("Creating database tables...")
    create_db_and_tables()
    yield
    print("Shutting down...")

# Initialize APP
app = FastAPI(
    title="Boundary Circle API",
    description="Backend API for Team 12 Software Engineering Project",
    version="0.1.0",
    lifespan=lifespan
)

# 1. Root Endpoint
@app.get("/")
def read_root():
    return {
        "message": "Welcome to Boundary Circle API", 
        "status": "active",
        "docs_url": "/docs"
    }

# 2. Health Check
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Include routers
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(circles.router)
app.include_router(tags.router)           # <--- 新增这行

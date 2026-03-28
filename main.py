from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app import models
from app.routers import teams, circles, auth_router # Assuming you have an auth router

# Initialize database tables based on models.py
# This creates boundary_circles.db with all required schemas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Boundary Circles API",
    description="Integrated Backend: Auth + Circle Gating + Team Management",
    version="1.1.0"
)

# Enable CORS for frontend integration (e.g., Streamlit or React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers with versioning prefix
app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(circles.router, prefix="/api/v1/circles", tags=["Circles & Gating"])
app.include_router(teams.router, prefix="/api/v1/teams", tags=["Team Management"])

@app.get("/")
def health_check():
    """Verify if the server is running and database is connected."""
    return {
        "status": "online",
        "database": "connected",
        "documentation": "/docs"
    }
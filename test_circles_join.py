import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_all
from app.main import app
from app.database import Base, engine, SessionLocal
from app import models

client = TestClient(app)

# Test Data Constants
TEST_CIRCLE_NAME = "EECS Career Fair"
VALID_TAGS = {"Major": "CS", "GPA": 3.8, "Skills": ["Python"]}
INVALID_TYPE_TAGS = {"Major": "CS", "GPA": "High", "Skills": ["Python"]} # GPA should be float
MISSING_TAGS = {"Major": "CS"} # Missing GPA and Skills

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # Setup: Create tables and a seed circle for testing
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Create a circle with strict tag schema
    test_circle = models.Circle(
        name=TEST_CIRCLE_NAME,
        tag_schema={"required": {"Major": "str", "GPA": "float", "Skills": "list"}}
    )
    db.add(test_circle)
    db.commit()
    circle_id = test_circle.id
    db.close()
    
    yield circle_id
    
    # Teardown: Clean up after tests
    Base.metadata.drop_all(bind=engine)

def test_join_circle_success(setup_db):
    """
    Test Case: Join a circle with valid tags (Acceptance Criterion 1)
    """
    circle_id = setup_db
    # Note: Assume we have a helper to get a valid token for 'current_user'
    # For simplicity, we bypass auth or use a test token
    response = client.post(
        f"/api/v1/circles/{circle_id}/join",
        json={"user_tags": VALID_TAGS},
        headers={"Authorization": "Bearer test-token"} 
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully joined the circle"

def test_join_circle_missing_tags(setup_db):
    """
    Test Case: Reject joining when mandatory tags are missing (Error 400)
    """
    circle_id = setup_db
    response = client.post(
        f"/api/v1/circles/{circle_id}/join",
        json={"user_tags": MISSING_TAGS},
        headers={"Authorization": "Bearer test-token"}
    )
    assert response.status_code == 400
    assert "Missing required tag" in response.json()["detail"]

def test_join_circle_wrong_type(setup_db):
    """
    Test Case: Reject joining when tag types are incorrect (Error 400)
    """
    circle_id = setup_db
    response = client.post(
        f"/api/v1/circles/{circle_id}/join",
        json={"user_tags": INVALID_TYPE_TAGS},
        headers={"Authorization": "Bearer test-token"}
    )
    assert response.status_code == 400
    assert "must be a number" in response.json()["detail"]

def test_join_circle_duplicate(setup_db):
    """
    Test Case: Return 409 when user is already a member (Error 409)
    """
    circle_id = setup_db
    # First join (Success)
    client.post(f"/api/v1/circles/{circle_id}/join", json={"user_tags": VALID_TAGS}, headers={"Authorization": "Bearer test-token"})
    
    # Second join (Conflict)
    response = client.post(
        f"/api/v1/circles/{circle_id}/join",
        json={"user_tags": VALID_TAGS},
        headers={"Authorization": "Bearer test-token"}
    )
    assert response.status_code == 409
    assert "already a member" in response.json()["detail"]

def test_get_circle_members(setup_db):
    """
    Test Case: Verify member list retrieval (Acceptance Criterion 4)
    """
    circle_id = setup_db
    response = client.get(f"/api/v1/circles/{circle_id}/members")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1

def test_leave_circle(setup_db):
    """
    Test Case: Successfully leave the circle (Acceptance Criterion 5)
    """
    circle_id = setup_db
    response = client.delete(
        f"/api/v1/circles/{circle_id}/leave",
        headers={"Authorization": "Bearer test-token"}
    )
    assert response.status_code == 200
    assert "Successfully left" in response.json()["message"]
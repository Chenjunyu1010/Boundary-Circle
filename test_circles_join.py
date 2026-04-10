import pytest
from fastapi.testclient import TestClient
from src.app.main import app

client = TestClient(app)

def test_circle_membership_lifecycle(auth_headers, test_circle):
    """
    Comprehensive test for joining, listing, and leaving a circle.
    """
    circle_id = test_circle.id
    payload = {"user_tags": {"Major": "CS", "GPA": 3.9}}

    # 1. Test: Successful Join
    response = client.post(f"/circles/{circle_id}/join", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully joined the circle"

    # 2. Test: Duplicate Join (Should return 409 Conflict)
    response = client.post(f"/circles/{circle_id}/join", json=payload, headers=auth_headers)
    assert response.status_code == 409

    # 3. Test: Fetch Member List
    response = client.get(f"/circles/{circle_id}/members")
    assert response.status_code == 200
    members = response.json()
    assert len(members) > 0
    assert "username" in members[0]

    # 4. Test: Successful Leave
    response = client.delete(f"/circles/{circle_id}/leave", headers=auth_headers)
    assert response.status_code == 200

    # 5. Test: Leave when not a member (Should return 404)
    response = client.delete(f"/circles/{circle_id}/leave", headers=auth_headers)
    assert response.status_code == 404
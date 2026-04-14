import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from src.db.database import get_session
from src.main import app
from src.models.tags import CircleMember, CircleRole, UserTag


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def override_get_session():
    with Session(engine) as session:
        yield session

@pytest.fixture(scope="function", autouse=True)
def setup_db():
    previous_override = app.dependency_overrides.get(get_session)
    app.dependency_overrides[get_session] = override_get_session
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)
    if previous_override is not None:
        app.dependency_overrides[get_session] = previous_override
    else:
        app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def db_session():
    with Session(engine) as session:
        yield session


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def creator(client):
    response = client.post(
        "/users/",
        json={
            "username": "circle_creator",
            "email": "creator@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def joiner(client):
    response = client.post(
        "/users/",
        json={
            "username": "circle_joiner",
            "email": "joiner@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def circle(client, creator):
    response = client.post(
        f"/circles/?creator_id={creator['id']}",
        json={
            "name": "EECS Career Fair",
            "description": "Circle for matching teammates",
            "category": "Course",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_tag_definition(client, circle_id, current_user_id, name, data_type, required=False):
    response = client.post(
        f"/circles/{circle_id}/tags?current_user_id={current_user_id}",
        json={"name": name, "data_type": data_type, "required": required},
    )
    assert response.status_code == 201
    return response.json()


def test_join_workflow_submits_required_tags(client, circle, creator, joiner):
    major_tag = create_tag_definition(client, circle["id"], creator["id"], "Major", "string", required=True)
    gpa_tag = create_tag_definition(client, circle["id"], creator["id"], "GPA", "float", required=True)

    major_response = client.post(
        f"/circles/{circle['id']}/tags/submit?current_user_id={joiner['id']}",
        json={"tag_definition_id": major_tag["id"], "value": "CS"},
    )
    gpa_response = client.post(
        f"/circles/{circle['id']}/tags/submit?current_user_id={joiner['id']}",
        json={"tag_definition_id": gpa_tag["id"], "value": "3.8"},
    )

    assert major_response.status_code == 200
    assert gpa_response.status_code == 200

    tags_response = client.get(f"/circles/{circle['id']}/tags/my?current_user_id={joiner['id']}")

    assert tags_response.status_code == 200
    payload = tags_response.json()
    assert len(payload) == 2
    assert {tag["value"] for tag in payload} == {"CS", "3.8"}


def test_join_workflow_rejects_invalid_tag_type(client, circle, creator, joiner):
    gpa_tag = create_tag_definition(client, circle["id"], creator["id"], "GPA", "float", required=True)

    response = client.post(
        f"/circles/{circle['id']}/tags/submit?current_user_id={joiner['id']}",
        json={"tag_definition_id": gpa_tag["id"], "value": "High"},
    )

    assert response.status_code == 400
    assert "Invalid value" in response.json()["detail"]


def test_join_workflow_resubmits_tag_updates_existing_value(client, circle, creator, joiner):
    skill_tag = create_tag_definition(client, circle["id"], creator["id"], "Skill", "string")

    first_response = client.post(
        f"/circles/{circle['id']}/tags/submit?current_user_id={joiner['id']}",
        json={"tag_definition_id": skill_tag["id"], "value": "Python"},
    )
    second_response = client.post(
        f"/circles/{circle['id']}/tags/submit?current_user_id={joiner['id']}",
        json={"tag_definition_id": skill_tag["id"], "value": "Rust"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["value"] == "Rust"

    tags_response = client.get(f"/circles/{circle['id']}/tags/my?current_user_id={joiner['id']}")
    payload = tags_response.json()

    assert len(payload) == 1
    assert payload[0]["value"] == "Rust"


def test_circle_member_record_can_be_created(db_session, circle, joiner):
    membership = CircleMember(user_id=joiner["id"], circle_id=circle["id"], role=CircleRole.MEMBER)
    db_session.add(membership)
    db_session.commit()

    stored_membership = db_session.exec(
        select(CircleMember).where(
            CircleMember.user_id == joiner["id"],
            CircleMember.circle_id == circle["id"],
        )
    ).first()

    assert stored_membership is not None
    assert stored_membership.role == CircleRole.MEMBER


def test_circle_member_record_can_be_removed_to_leave_circle(db_session, circle, joiner):
    membership = CircleMember(user_id=joiner["id"], circle_id=circle["id"], role=CircleRole.MEMBER)
    db_session.add(membership)
    db_session.commit()

    stored_membership = db_session.exec(
        select(CircleMember).where(
            CircleMember.user_id == joiner["id"],
            CircleMember.circle_id == circle["id"],
        )
    ).first()
    db_session.delete(stored_membership)
    db_session.commit()

    remaining_membership = db_session.exec(
        select(CircleMember).where(
            CircleMember.user_id == joiner["id"],
            CircleMember.circle_id == circle["id"],
        )
    ).first()
    remaining_tags = db_session.exec(
        select(UserTag).where(
            UserTag.user_id == joiner["id"],
            UserTag.circle_id == circle["id"],
        )
    ).all()

    assert remaining_membership is None
    assert remaining_tags == []



def register_and_login(client: TestClient, username: str, email: str) -> tuple[dict, dict]:
    register_response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "secret123",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": "secret123"},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return register_response.json(), headers


@pytest.fixture
def authenticated_joiner(client):
    return register_and_login(client, "api_joiner", "api_joiner@example.com")


def test_join_circle_creates_membership(client, db_session, circle, authenticated_joiner):
    joiner, headers = authenticated_joiner

    response = client.post(f"/circles/{circle['id']}/join", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Successfully joined the circle",
        "circle_id": circle["id"],
    }

    membership = db_session.exec(
        select(CircleMember).where(
            CircleMember.user_id == joiner["id"],
            CircleMember.circle_id == circle["id"],
        )
    ).first()
    assert membership is not None
    assert membership.role == CircleRole.MEMBER


def test_join_circle_rejects_duplicate_membership(client, db_session, circle, authenticated_joiner):
    joiner, headers = authenticated_joiner

    first_response = client.post(f"/circles/{circle['id']}/join", headers=headers)
    second_response = client.post(f"/circles/{circle['id']}/join", headers=headers)

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Already a member"

    memberships = db_session.exec(
        select(CircleMember).where(
            CircleMember.user_id == joiner["id"],
            CircleMember.circle_id == circle["id"],
        )
    ).all()
    assert len(memberships) == 1


def test_leave_circle_removes_membership_and_circle_tags(client, db_session, circle, creator, authenticated_joiner):
    joiner, headers = authenticated_joiner

    join_response = client.post(f"/circles/{circle['id']}/join", headers=headers)
    assert join_response.status_code == 200

    skill_tag = create_tag_definition(client, circle["id"], creator["id"], "Skill", "string")
    submit_response = client.post(
        f"/circles/{circle['id']}/tags/submit?current_user_id={joiner['id']}",
        json={"tag_definition_id": skill_tag["id"], "value": "Python"},
    )
    assert submit_response.status_code == 200

    leave_response = client.delete(f"/circles/{circle['id']}/leave", headers=headers)

    assert leave_response.status_code == 200
    assert leave_response.json() == {
        "success": True,
        "message": "Successfully left the circle",
        "circle_id": circle["id"],
    }

    membership = db_session.exec(
        select(CircleMember).where(
            CircleMember.user_id == joiner["id"],
            CircleMember.circle_id == circle["id"],
        )
    ).first()
    tags = db_session.exec(
        select(UserTag).where(
            UserTag.user_id == joiner["id"],
            UserTag.circle_id == circle["id"],
        )
    ).all()

    assert membership is None
    assert tags == []


def test_leave_circle_without_membership_returns_not_found(client, circle, authenticated_joiner):
    _, headers = authenticated_joiner

    response = client.delete(f"/circles/{circle['id']}/leave", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Membership not found"


def test_list_circle_members_returns_joined_user(client, circle, authenticated_joiner):
    joiner, headers = authenticated_joiner

    join_response = client.post(f"/circles/{circle['id']}/join", headers=headers)
    assert join_response.status_code == 200

    members_response = client.get(f"/circles/{circle['id']}/members", headers=headers)

    assert members_response.status_code == 200
    members = members_response.json()
    assert any(
        member["id"] == joiner["id"]
        and member["username"] == joiner["username"]
        and member["email"] == joiner["email"]
        and member["circle_id"] == circle["id"]
        for member in members
    )

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

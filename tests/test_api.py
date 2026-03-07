import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from typing import Generator
from sqlalchemy.pool import StaticPool

from src.main import app
from src.db.database import get_session
from src.models.core import User, Circle

# ============ 测试数据库隔离设置 ============
# 使用纯内存模式的 SQLite，这意味着每次测试运行都在内存中，不会影响物理文件
sqlite_url = "sqlite://"
engine = create_engine(
    sqlite_url, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

def override_get_session() -> Generator:
    """覆盖 FastAPI 的 get_session 依赖，指向我们的内存数据库连接"""
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

client = TestClient(app)

@pytest.fixture(scope="function")
def setup_db():
    """每个测试用例前会初始化全新的数据库表结构"""
    SQLModel.metadata.create_all(engine)
    yield
    # 测试后清空所有表，确保完全隔离
    SQLModel.metadata.drop_all(engine)

@pytest.fixture
def test_user(setup_db):
    """创建测试用户"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "测试用户",
        "password": "password123"
    }
    response = client.post("/users/", json=user_data)
    return response.json()

@pytest.fixture
def test_circle(test_user):
    """创建测试圈子"""
    circle_data = {
        "name": "测试圈子",
        "description": "这是一个测试圈子",
        "category": "Test"
    }
    response = client.post(
        f"/circles/?creator_id={test_user['id']}", 
        json=circle_data
    )
    return response.json()

# ============ 用户接口测试 ============

def test_create_user(setup_db):
    """测试创建用户"""
    user_data = {
        "username": "newuser",
        "email": "new@example.com",
        "full_name": "新用户",
        "password": "password123"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "id" in data

def test_create_user_duplicate_email(setup_db, test_user):
    """测试邮箱重复"""
    user_data = {
        "username": "anotheruser",
        "email": test_user["email"],  # 相同邮箱
        "password": "password123"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_get_users(setup_db, test_user):
    """测试获取用户列表"""
    response = client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(u["username"] == "testuser" for u in data)

def test_get_user(setup_db, test_user):
    """测试获取单个用户"""
    response = client.get(f"/users/{test_user['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"

def test_get_user_not_found(setup_db):
    """测试用户不存在"""
    response = client.get("/users/999")
    assert response.status_code == 404

# ============ 圈子接口测试 ============

def test_create_circle(setup_db, test_user):
    """测试创建圈子"""
    circle_data = {
        "name": "新圈子",
        "description": "描述",
        "category": "Course"
    }
    response = client.post(
        f"/circles/?creator_id={test_user['id']}", 
        json=circle_data
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "新圈子"
    assert data["creator_id"] == test_user["id"]

def test_create_circle_invalid_creator(setup_db):
    """测试创建者不存在"""
    circle_data = {
        "name": "无效圈子",
        "description": "描述"
    }
    response = client.post(
        "/circles/?creator_id=999",  # 不存在的用户
        json=circle_data
    )
    assert response.status_code == 404
    assert "Creator user not found" in response.json()["detail"]

def test_get_circles(setup_db, test_circle):
    """测试获取圈子列表"""
    response = client.get("/circles/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

def test_get_circle(setup_db, test_circle):
    """测试获取单个圈子"""
    response = client.get(f"/circles/{test_circle['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试圈子"

def test_get_circle_not_found(setup_db):
    """测试圈子不存在"""
    response = client.get("/circles/999")
    assert response.status_code == 404

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

@pytest.fixture
def test_user():
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

def test_create_user():
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

def test_create_user_duplicate_email(test_user):
    """测试邮箱重复"""
    user_data = {
        "username": "anotheruser",
        "email": test_user["email"],
        "password": "password123"
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_get_users(test_user):
    """测试获取用户列表"""
    response = client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(u["username"] == "testuser" for u in data)

def test_get_user(test_user):
    """测试获取单个用户"""
    response = client.get(f"/users/{test_user['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"

def test_get_user_not_found():
    """测试用户不存在"""
    response = client.get("/users/999")
    assert response.status_code == 404

# ============ 圈子接口测试 ============

def test_create_circle(test_user):
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

def test_create_circle_invalid_creator():
    """测试创建者不存在"""
    circle_data = {
        "name": "无效圈子",
        "description": "描述"
    }
    response = client.post(
        "/circles/?creator_id=999",
        json=circle_data
    )
    assert response.status_code == 404
    assert "Creator user not found" in response.json()["detail"]

def test_get_circles(test_circle):
    """测试获取圈子列表"""
    response = client.get("/circles/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

def test_get_circle(test_circle):
    """测试获取单个圈子"""
    response = client.get(f"/circles/{test_circle['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试圈子"

def test_get_circle_not_found():
    """测试圈子不存在"""
    response = client.get("/circles/999")
    assert response.status_code == 404

import sys
import os
# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_register_normal():
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "secret123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["msg"] == "用户创建成功"
    assert "user_id" in data

def test_register_duplicate_email():
    client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "password": "pass"
    })
    response = client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "password": "anotherpass"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "该邮箱已被注册"

def test_login_success():
    client.post("/auth/register", json={
        "email": "login@example.com",
        "password": "correctpass"
    })
    response = client.post("/auth/login", json={
        "email": "login@example.com",
        "password": "correctpass"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token is not None

def test_login_wrong_password():
    client.post("/auth/register", json={
        "email": "wrongpass@example.com",
        "password": "rightpass"
    })
    response = client.post("/auth/login", json={
        "email": "wrongpass@example.com",
        "password": "wrong"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "邮箱或密码错误"

def test_protected_route_valid_token():
    client.post("/auth/register", json={
        "email": "protected@example.com",
        "password": "pass"
    })
    login_resp = client.post("/auth/login", json={
        "email": "protected@example.com",
        "password": "pass"
    })
    token = login_resp.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "protected@example.com"

def test_protected_route_invalid_token():
    response = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401
    assert response.json()["detail"] == "无效的认证凭据"

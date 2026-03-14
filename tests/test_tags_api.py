import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

# ============ 测试用假数据准备 (Fixtures) ============
@pytest.fixture
def creator():
    """圈子创建者（管理员）"""
    res = client.post("/users/", json={"username": "creator", "email": "c@test.com", "password": "123"})
    return res.json()

@pytest.fixture
def normal_user():
    """普通成员"""
    res = client.post("/users/", json={"username": "normal", "email": "n@test.com", "password": "123"})
    return res.json()

@pytest.fixture
def circle(creator):
    """测试圈子"""
    res = client.post(f"/circles/?creator_id={creator['id']}", json={"name": "AI Circle", "description": "Test"})
    return res.json()

# ============ 核心 API 测试 ============

def test_create_tag_def_as_creator(creator, circle):
    """测试创建标签定义（管理员权限验证通过）"""
    tag_data = {"name": "Tech Stack", "data_type": "string"}
    res = client.post(f"/circles/{circle['id']}/tags?current_user_id={creator['id']}", json=tag_data)
    assert res.status_code == 201
    assert res.json()["name"] == "Tech Stack"

def test_create_tag_def_as_normal_user(normal_user, circle):
    """测试创建标签定义（普通成员权限验证，应被拒绝）"""
    tag_data = {"name": "Role", "data_type": "enum", "options": '["Backend"]'}
    res = client.post(f"/circles/{circle['id']}/tags?current_user_id={normal_user['id']}", json=tag_data)
    assert res.status_code == 403
    assert "Only circle creator can define tags" in res.json()["detail"]

def test_submit_user_tag_valid(creator, normal_user, circle):
    """测试提交标签（正常提交）"""
    tag_res = client.post(
        f"/circles/{circle['id']}/tags?current_user_id={creator['id']}", 
        json={"name": "GPA", "data_type": "float"}
    )
    tag_id = tag_res.json()["id"]

    res = client.post(
        f"/circles/{circle['id']}/tags/submit?current_user_id={normal_user['id']}", 
        json={"tag_definition_id": tag_id, "value": "3.8"}
    )
    assert res.status_code == 200
    assert res.json()["value"] == "3.8"

def test_submit_user_tag_invalid_type(creator, normal_user, circle):
    """测试标签类型验证（传入非法数据）"""
    tag_res = client.post(
        f"/circles/{circle['id']}/tags?current_user_id={creator['id']}", 
        json={"name": "Years of Exp", "data_type": "integer"}
    )
    tag_id = tag_res.json()["id"]

    res = client.post(
        f"/circles/{circle['id']}/tags/submit?current_user_id={normal_user['id']}", 
        json={"tag_definition_id": tag_id, "value": "Two Years"}
    )
    assert res.status_code == 400
    assert "Invalid value" in res.json()["detail"]

def test_submit_user_tag_enum(creator, normal_user, circle):
    """测试枚举(Enum)类型选项的验证"""
    tag_res = client.post(
        f"/circles/{circle['id']}/tags?current_user_id={creator['id']}", 
        json={"name": "Role", "data_type": "enum", "options": '["Frontend", "Backend"]'}
    )
    tag_id = tag_res.json()["id"]

    res1 = client.post(
        f"/circles/{circle['id']}/tags/submit?current_user_id={normal_user['id']}", 
        json={"tag_definition_id": tag_id, "value": "Designer"}
    )
    assert res1.status_code == 400

    res2 = client.post(
        f"/circles/{circle['id']}/tags/submit?current_user_id={normal_user['id']}", 
        json={"tag_definition_id": tag_id, "value": "Backend"}
    )
    assert res2.status_code == 200

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

# ============ 针对 Issue #20 与完整 CRUD 的补充测试 ============

def test_create_tag_def_enum_invalid(creator, circle):
    """测试创建 ENUM 标签时缺少 options 或 JSON 格式错误"""
    # 缺少 options
    res1 = client.post(
        f"/circles/{circle['id']}/tags?current_user_id={creator['id']}", 
        json={"name": "Role1", "data_type": "enum"}
    )
    assert res1.status_code == 400
    
    # 非法 JSON 格式
    res2 = client.post(
        f"/circles/{circle['id']}/tags?current_user_id={creator['id']}", 
        json={"name": "Role2", "data_type": "enum", "options": "not-a-list"}
    )
    assert res2.status_code == 400

def test_submit_tag_user_not_found(creator, circle):
    """测试提交标签时伪造不存在的 current_user_id"""
    tag_res = client.post(
        f"/circles/{circle['id']}/tags?current_user_id={creator['id']}", 
        json={"name": "Test", "data_type": "string"}
    )
    tag_id = tag_res.json()["id"]

    res = client.post(
        f"/circles/{circle['id']}/tags/submit?current_user_id=9999", # 伪造的用户ID
        json={"tag_definition_id": tag_id, "value": "test"}
    )
    assert res.status_code == 404
    assert "User not found" in res.json()["detail"]

def test_get_my_tags_and_delete(creator, normal_user, circle):
    """测试完整流程：提交 -> 获取我的标签 -> 删除我的标签"""
    tag_res = client.post(
        f"/circles/{circle['id']}/tags?current_user_id={creator['id']}", 
        json={"name": "Test", "data_type": "string"}
    )
    tag_id = tag_res.json()["id"]

    # 1. 提交标签
    client.post(
        f"/circles/{circle['id']}/tags/submit?current_user_id={normal_user['id']}", 
        json={"tag_definition_id": tag_id, "value": "my_value"}
    )
    
    # 2. 获取我的标签
    res_get = client.get(f"/circles/{circle['id']}/tags/my?current_user_id={normal_user['id']}")
    assert res_get.status_code == 200
    assert len(res_get.json()) == 1
    user_tag_id = res_get.json()[0]["id"]
    
    # 3. 删除标签
    res_del = client.delete(f"/tags/{user_tag_id}?current_user_id={normal_user['id']}")
    assert res_del.status_code == 204
    
    # 4. 再次获取应为空
    res_get_after = client.get(f"/circles/{circle['id']}/tags/my?current_user_id={normal_user['id']}")
    assert len(res_get_after.json()) == 0
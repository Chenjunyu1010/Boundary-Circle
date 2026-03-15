import pytest
from src.models.core import User, Circle
from src.models.tags import TagDefinition, UserTag, CircleMember, TagDataType, CircleRole
from src.api.tags import validate_tag_value

# db_session fixture 由 conftest.py 提供（使用隔离的内存数据库）

@pytest.fixture
def db_user(db_session):
    """底层生成测试用户"""
    user = User(username="model_user", email="model@test.com", hashed_password="123")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def db_circle(db_session, db_user):
    """底层生成测试圈子"""
    circle = Circle(name="Model Circle", description="Testing models", category="Test", creator_id=db_user.id)
    db_session.add(circle)
    db_session.commit()
    db_session.refresh(circle)
    return circle

# ============ Issue #11 要求的 5 个具体测试 ============

def test_create_tag_definition(db_session, db_circle):
    """1. 测试创建标签定义"""
    tag_def = TagDefinition(
        circle_id=db_circle.id, 
        name="GPA", 
        data_type=TagDataType.FLOAT, 
        required=True,
        description="User's GPA"
    )
    db_session.add(tag_def)
    db_session.commit()
    
    fetched = db_session.get(TagDefinition, tag_def.id)
    assert fetched is not None
    assert fetched.name == "GPA"
    assert fetched.required is True
    assert fetched.data_type == TagDataType.FLOAT

def test_create_enum_tag_definition(db_session, db_circle):
    """2. 测试创建枚举类型标签（带 options）"""
    tag_def = TagDefinition(
        circle_id=db_circle.id, 
        name="Role", 
        data_type=TagDataType.ENUM, 
        options='["Frontend", "Backend", "AI"]' # 存储为 JSON 字符串
    )
    db_session.add(tag_def)
    db_session.commit()
    
    fetched = db_session.get(TagDefinition, tag_def.id)
    assert 'Backend' in fetched.options

def test_user_fill_tag(db_session, db_user, db_circle):
    """3. 测试用户填写标签"""
    # 先定义一个标签
    tag_def = TagDefinition(circle_id=db_circle.id, name="Age", data_type=TagDataType.INTEGER)
    db_session.add(tag_def)
    db_session.commit()
    
    # 存入用户标签值
    user_tag = UserTag(
        user_id=db_user.id, 
        circle_id=db_circle.id, 
        tag_definition_id=tag_def.id, 
        value="21"
    )
    db_session.add(user_tag)
    db_session.commit()
    
    fetched = db_session.get(UserTag, user_tag.id)
    assert fetched.value == "21"
    assert fetched.user_id == db_user.id

def test_tag_value_validation():
    """4. 测试标签值验证（类型检查）"""
    # 测试我们写在 src.api.tags 里的核心验证逻辑
    assert validate_tag_value("25", TagDataType.INTEGER) is True
    assert validate_tag_value("abc", TagDataType.INTEGER) is False
    assert validate_tag_value("3.14", TagDataType.FLOAT) is True
    assert validate_tag_value("true", TagDataType.BOOLEAN) is True
    assert validate_tag_value("Frontend", TagDataType.ENUM, '["Frontend", "Backend"]') is True
    assert validate_tag_value("PM", TagDataType.ENUM, '["Frontend", "Backend"]') is False

def test_create_circle_member(db_session, db_user, db_circle):
    """5. 测试圈子成员关系创建"""
    member = CircleMember(
        user_id=db_user.id, 
        circle_id=db_circle.id, 
        role=CircleRole.ADMIN
    )
    db_session.add(member)
    db_session.commit()
    
    fetched = db_session.get(CircleMember, member.id)
    assert fetched is not None
    assert fetched.role == CircleRole.ADMIN
    assert fetched.joined_at is not None # 验证时间戳是否自动生成
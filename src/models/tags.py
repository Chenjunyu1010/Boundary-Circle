from typing import Optional
from enum import Enum
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel
from datetime import datetime, timezone

# 1. 支持的标签数据类型
class TagDataType(str, Enum):
    INTEGER = "integer"
    BOOLEAN = "boolean"
    STRING = "string"
    ENUM = "enum"
    FLOAT = "float"

# 定义圈子角色
class CircleRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"

# 2. TagDefinition - 圈子定义的标签模式
class TagDefinition(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    circle_id: int = Field(foreign_key="circle.id", index=True)
    name: str
    data_type: TagDataType
    required: bool = Field(default=False)
    options: Optional[str] = Field(default=None) # 如果是 ENUM，这里存 JSON 字符串，如 '["A", "B"]'
    description: Optional[str] = Field(default=None)

# 3. UserTag - 用户填写的标签值
class UserTag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    circle_id: int = Field(foreign_key="circle.id", index=True)
    tag_definition_id: int = Field(foreign_key="tagdefinition.id")
    value: str # 统一存为字符串，读取时根据 TagDefinition 的 data_type 转换

# 4. CircleMember - 圈子成员关系
class CircleMember(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "circle_id", name="uq_circle_member_user_circle"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    circle_id: int = Field(foreign_key="circle.id", index=True)
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    role: CircleRole = Field(default=CircleRole.MEMBER)

# ==========================================
# 用于 API 交互的 Pydantic Schema
# ==========================================
class TagDefinitionCreate(SQLModel):
    name: str
    data_type: TagDataType
    required: bool = False
    options: Optional[str] = None
    description: Optional[str] = None

class UserTagSubmit(SQLModel):
    tag_definition_id: int
    value: str
# Force Commit ID: 04/14/2026 14:01:50

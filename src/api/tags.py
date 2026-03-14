import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from src.db.database import get_session
from src.models.core import Circle
from src.models.tags import (
    TagDefinition, TagDefinitionCreate, 
    UserTag, UserTagSubmit, 
    CircleMember, TagDataType, CircleRole
)

router = APIRouter(tags=["Tags"])

# ==========================================
# 辅助函数：验证标签值类型
# ==========================================
def validate_tag_value(value: str, data_type: TagDataType, options: str = None) -> bool:
    try:
        if data_type == TagDataType.INTEGER:
            int(value)
        elif data_type == TagDataType.FLOAT:
            float(value)
        elif data_type == TagDataType.BOOLEAN:
            if value.lower() not in["true", "false", "1", "0"]:
                raise ValueError
        elif data_type == TagDataType.ENUM:
            if not options:
                raise ValueError("Enum options missing")
            opts_list = json.loads(options)
            if value not in opts_list:
                raise ValueError(f"Value must be one of {opts_list}")
        return True
    except Exception:
        return False

# ==========================================
# API 1: 创建标签定义 (仅限管理员/创建者)
# ==========================================
@router.post("/circles/{circle_id}/tags", response_model=TagDefinition, status_code=status.HTTP_201_CREATED)
def create_tag_definition(
    circle_id: int, 
    tag_in: TagDefinitionCreate, 
    current_user_id: int, # 模拟身份认证
    session: Session = Depends(get_session)
):
    # 验证圈子是否存在
    circle = session.get(Circle, circle_id)
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")
        
    # 权限验证：必须是圈子创建者（后续可以加入 CircleMember Admin 判断）
    if circle.creator_id != current_user_id:
        raise HTTPException(status_code=403, detail="Only circle creator can define tags")
        
    db_tag_def = TagDefinition.model_validate(tag_in, update={"circle_id": circle_id})
    session.add(db_tag_def)
    session.commit()
    session.refresh(db_tag_def)
    return db_tag_def

# ==========================================
# API 2: 获取圈子的标签定义列表
# ==========================================
@router.get("/circles/{circle_id}/tags", response_model=List[TagDefinition])
def get_circle_tags(circle_id: int, session: Session = Depends(get_session)):
    statement = select(TagDefinition).where(TagDefinition.circle_id == circle_id)
    tags = session.exec(statement).all()
    return tags

# ==========================================
# API 3: 用户提交/更新个人标签
# ==========================================
@router.post("/circles/{circle_id}/tags/submit", response_model=UserTag)
def submit_user_tag(
    circle_id: int,
    tag_submit: UserTagSubmit,
    current_user_id: int, # 模拟身份认证
    session: Session = Depends(get_session)
):
    # 1. 查找标签定义
    tag_def = session.get(TagDefinition, tag_submit.tag_definition_id)
    if not tag_def or tag_def.circle_id != circle_id:
        raise HTTPException(status_code=404, detail="Tag definition not found in this circle")
        
    # 2. 类型验证 (核心业务逻辑)
    if not validate_tag_value(tag_submit.value, tag_def.data_type, tag_def.options):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid value '{tag_submit.value}' for type {tag_def.data_type}"
        )
        
    # 3. 检查是否已经填过，如果有则更新，没有则创建
    statement = select(UserTag).where(
        UserTag.user_id == current_user_id,
        UserTag.tag_definition_id == tag_submit.tag_definition_id
    )
    existing_tag = session.exec(statement).first()
    
    if existing_tag:
        existing_tag.value = tag_submit.value
        db_user_tag = existing_tag
    else:
        db_user_tag = UserTag(
            user_id=current_user_id,
            circle_id=circle_id,
            tag_definition_id=tag_submit.tag_definition_id,
            value=tag_submit.value
        )
        session.add(db_user_tag)
        
    session.commit()
    session.refresh(db_user_tag)
    return db_user_tag
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from src.db.database import get_session
from src.models.core import Circle, User
from src.models.tags import (
    TagDefinition, TagDefinitionCreate, 
    UserTag, UserTagSubmit, 
    TagDataType
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
            if value.lower() not in ["true", "false", "1", "0"]:
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
# API 1: 创建标签定义 (Issue #20: 增加 ENUM 校验)
# ==========================================
@router.post("/circles/{circle_id}/tags", response_model=TagDefinition, status_code=status.HTTP_201_CREATED)
def create_tag_definition(
    circle_id: int, 
    tag_in: TagDefinitionCreate, 
    current_user_id: int, 
    session: Session = Depends(get_session)
):
    circle = session.get(Circle, circle_id)
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")
        
    if circle.creator_id != current_user_id:
        raise HTTPException(status_code=403, detail="Only circle creator can define tags")
    
    # 【修复 Issue #20】如果类型是 ENUM，必须有合法的 options JSON 数组
    if tag_in.data_type == TagDataType.ENUM:
        if not tag_in.options:
            raise HTTPException(status_code=400, detail="ENUM type must provide 'options'")
        try:
            opts = json.loads(tag_in.options)
            if not isinstance(opts, list) or len(opts) == 0:
                raise ValueError
        except Exception:
            raise HTTPException(status_code=400, detail="'options' must be a valid JSON list of strings")

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
    return session.exec(statement).all()

# ==========================================
# API 3: 删除标签定义 (新增 CRUD)
# ==========================================
@router.delete("/tags/definitions/{tag_def_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag_definition(tag_def_id: int, current_user_id: int, session: Session = Depends(get_session)):
    tag_def = session.get(TagDefinition, tag_def_id)
    if not tag_def:
        raise HTTPException(status_code=404, detail="Tag definition not found")
    
    circle = session.get(Circle, tag_def.circle_id)
    if circle.creator_id != current_user_id:
        raise HTTPException(status_code=403, detail="Only circle creator can delete tags")
        
    session.delete(tag_def)
    session.commit()
    return None

# ==========================================
# API 4: 用户提交/更新个人标签 (Issue #20: 增加用户存在性校验)
# ==========================================
@router.post("/circles/{circle_id}/tags/submit", response_model=UserTag)
def submit_user_tag(
    circle_id: int,
    tag_submit: UserTagSubmit,
    current_user_id: int, 
    session: Session = Depends(get_session)
):
    # 【修复 Issue #20】校验用户是否存在，避免产生孤儿记录
    user = session.get(User, current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    tag_def = session.get(TagDefinition, tag_submit.tag_definition_id)
    if not tag_def or tag_def.circle_id != circle_id:
        raise HTTPException(status_code=404, detail="Tag definition not found in this circle")
        
    if not validate_tag_value(tag_submit.value, tag_def.data_type, tag_def.options):
        raise HTTPException(status_code=400, detail=f"Invalid value for type {tag_def.data_type}")
        
    # Upsert 逻辑 (存在则更新，不存在则创建。相当于同时实现了 POST 和 PUT)
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

# ==========================================
# API 5: 获取我的标签 (新增 CRUD)
# ==========================================
@router.get("/circles/{circle_id}/tags/my", response_model=List[UserTag])
def get_my_tags(circle_id: int, current_user_id: int, session: Session = Depends(get_session)):
    statement = select(UserTag).where(
        UserTag.circle_id == circle_id, 
        UserTag.user_id == current_user_id
    )
    return session.exec(statement).all()

# ==========================================
# API 6: 删除我的标签 (新增 CRUD)
# ==========================================
@router.delete("/tags/{user_tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_tag(user_tag_id: int, current_user_id: int, session: Session = Depends(get_session)):
    user_tag = session.get(UserTag, user_tag_id)
    if not user_tag:
        raise HTTPException(status_code=404, detail="User tag not found")
        
    if user_tag.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this tag")
        
    session.delete(user_tag)
    session.commit()
    return None

# ==========================================
# API 7: 更新标签定义 (补齐 CRUD 拼图)
# ==========================================
@router.put("/tags/definitions/{tag_def_id}", response_model=TagDefinition)
def update_tag_definition(
    tag_def_id: int,
    tag_update: TagDefinitionCreate,
    current_user_id: int,
    session: Session = Depends(get_session)
):
    tag_def = session.get(TagDefinition, tag_def_id)
    if not tag_def:
        raise HTTPException(status_code=404, detail="Tag definition not found")
    
    circle = session.get(Circle, tag_def.circle_id)
    if circle.creator_id != current_user_id:
        raise HTTPException(status_code=403, detail="Only circle creator can update tags")
        
    # 【校验 ENUM】
    if tag_update.data_type == TagDataType.ENUM:
        if not tag_update.options:
            raise HTTPException(status_code=400, detail="ENUM type must provide 'options'")
        try:
            opts = json.loads(tag_update.options)
            if not isinstance(opts, list) or len(opts) == 0:
                raise ValueError
        except Exception:
            raise HTTPException(status_code=400, detail="'options' must be a valid JSON list of strings")

    # 更新字段
    tag_def.name = tag_update.name
    tag_def.data_type = tag_update.data_type
    tag_def.required = tag_update.required
    tag_def.options = tag_update.options
    tag_def.description = tag_update.description

    session.add(tag_def)
    session.commit()
    session.refresh(tag_def)
    return tag_def
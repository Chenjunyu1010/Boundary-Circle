import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from src.auth.dependencies import get_current_user
from src.db.database import get_session
from src.models.core import Circle, User
from src.models.tags import TagDataType, TagDefinition, TagDefinitionCreate, UserTag, UserTagSubmit


router = APIRouter(tags=["Tags"])


def parse_tag_options(options: Optional[str]) -> list[str]:
    if not options:
        raise ValueError("Options missing")

    parsed_options = json.loads(options)
    if not isinstance(parsed_options, list) or not parsed_options:
        raise ValueError("Options must be a non-empty list")
    if any(not isinstance(option, str) or not option.strip() for option in parsed_options):
        raise ValueError("Each option must be a non-empty string")
    return parsed_options


def validate_tag_definition_payload(tag_in: TagDefinitionCreate) -> None:
    selection_types = {
        TagDataType.ENUM,
        TagDataType.SINGLE_SELECT,
        TagDataType.MULTI_SELECT,
    }
    if tag_in.data_type not in selection_types:
        return

    if not tag_in.options:
        raise HTTPException(status_code=400, detail="Selection types must provide 'options'")

    try:
        options = parse_tag_options(tag_in.options)
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="'options' must be a valid JSON list of strings",
        ) from None

    if tag_in.data_type == TagDataType.MULTI_SELECT and tag_in.max_selections is not None:
        if tag_in.max_selections > len(options):
            raise HTTPException(
                status_code=400,
                detail="'max_selections' cannot exceed the number of options",
            )


def validate_tag_value(
    value: str,
    data_type: TagDataType,
    options: Optional[str] = None,
    max_selections: Optional[int] = None,
) -> bool:
    """Validate a tag value against its declared type."""
    try:
        if data_type == TagDataType.INTEGER:
            int(value)
        elif data_type == TagDataType.FLOAT:
            float(value)
        elif data_type == TagDataType.BOOLEAN:
            if value.lower() not in ["true", "false", "1", "0"]:
                raise ValueError
        elif data_type in {TagDataType.ENUM, TagDataType.SINGLE_SELECT}:
            if value not in parse_tag_options(options):
                raise ValueError
        elif data_type == TagDataType.MULTI_SELECT:
            selected_values = json.loads(value)
            if not isinstance(selected_values, list) or not selected_values:
                raise ValueError

            valid_options = parse_tag_options(options)
            if any(not isinstance(item, str) or item not in valid_options for item in selected_values):
                raise ValueError

            if max_selections is not None and len(selected_values) > max_selections:
                raise ValueError
        return True
    except Exception:
        return False


def require_user_id(current_user: User) -> int:
    """Return the authenticated user id or fail fast if it is missing."""
    if current_user.id is None:
        raise HTTPException(status_code=500, detail="Current user ID missing")
    return current_user.id


@router.post("/circles/{circle_id}/tags", response_model=TagDefinition, status_code=status.HTTP_201_CREATED)
def create_tag_definition(
    circle_id: int,
    tag_in: TagDefinitionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    current_user_id = require_user_id(current_user)

    circle = session.get(Circle, circle_id)
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")
    if circle.creator_id != current_user_id:
        raise HTTPException(status_code=403, detail="Only circle creator can define tags")

    validate_tag_definition_payload(tag_in)

    db_tag_def = TagDefinition.model_validate(tag_in, update={"circle_id": circle_id})
    session.add(db_tag_def)
    session.commit()
    session.refresh(db_tag_def)
    return db_tag_def


@router.get("/circles/{circle_id}/tags", response_model=list[TagDefinition])
def get_circle_tags(circle_id: int, session: Session = Depends(get_session)):
    return session.exec(select(TagDefinition).where(TagDefinition.circle_id == circle_id)).all()


@router.delete("/tags/definitions/{tag_def_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag_definition(
    tag_def_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    current_user_id = require_user_id(current_user)

    tag_def = session.get(TagDefinition, tag_def_id)
    if not tag_def:
        raise HTTPException(status_code=404, detail="Tag definition not found")

    circle = session.get(Circle, tag_def.circle_id)
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")
    if circle.creator_id != current_user_id:
        raise HTTPException(status_code=403, detail="Only circle creator can delete tags")

    session.delete(tag_def)
    session.commit()
    return None


@router.post("/circles/{circle_id}/tags/submit", response_model=UserTag)
def submit_user_tag(
    circle_id: int,
    tag_submit: UserTagSubmit,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    current_user_id = require_user_id(current_user)

    user = session.get(User, current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    tag_def = session.get(TagDefinition, tag_submit.tag_definition_id)
    if not tag_def or tag_def.circle_id != circle_id:
        raise HTTPException(status_code=404, detail="Tag definition not found in this circle")

    if not validate_tag_value(
        tag_submit.value,
        tag_def.data_type,
        tag_def.options,
        tag_def.max_selections,
    ):
        raise HTTPException(status_code=400, detail=f"Invalid value for type {tag_def.data_type}")

    existing_tag = session.exec(
        select(UserTag).where(
            UserTag.user_id == current_user_id,
            UserTag.tag_definition_id == tag_submit.tag_definition_id,
        )
    ).first()

    if existing_tag:
        existing_tag.value = tag_submit.value
        db_user_tag = existing_tag
    else:
        db_user_tag = UserTag(
            user_id=current_user_id,
            circle_id=circle_id,
            tag_definition_id=tag_submit.tag_definition_id,
            value=tag_submit.value,
        )
        session.add(db_user_tag)

    session.commit()
    session.refresh(db_user_tag)
    return db_user_tag


@router.get("/circles/{circle_id}/tags/my", response_model=list[UserTag])
def get_my_tags(
    circle_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    current_user_id = require_user_id(current_user)
    return session.exec(
        select(UserTag).where(
            UserTag.circle_id == circle_id,
            UserTag.user_id == current_user_id,
        )
    ).all()


@router.delete("/tags/{user_tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_tag(
    user_tag_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    current_user_id = require_user_id(current_user)

    user_tag = session.get(UserTag, user_tag_id)
    if not user_tag:
        raise HTTPException(status_code=404, detail="User tag not found")
    if user_tag.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this tag")

    session.delete(user_tag)
    session.commit()
    return None


@router.put("/tags/definitions/{tag_def_id}", response_model=TagDefinition)
def update_tag_definition(
    tag_def_id: int,
    tag_update: TagDefinitionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    current_user_id = require_user_id(current_user)

    tag_def = session.get(TagDefinition, tag_def_id)
    if not tag_def:
        raise HTTPException(status_code=404, detail="Tag definition not found")

    circle = session.get(Circle, tag_def.circle_id)
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")
    if circle.creator_id != current_user_id:
        raise HTTPException(status_code=403, detail="Only circle creator can update tags")

    validate_tag_definition_payload(tag_update)

    tag_def.name = tag_update.name
    tag_def.data_type = tag_update.data_type
    tag_def.required = tag_update.required
    tag_def.options = tag_update.options
    tag_def.max_selections = tag_update.max_selections
    tag_def.description = tag_update.description

    session.add(tag_def)
    session.commit()
    session.refresh(tag_def)
    return tag_def

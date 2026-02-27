from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from src.db.database import get_session
from src.models.core import Circle, CircleCreate, CircleRead, User

router = APIRouter(
    prefix="/circles",
    tags=["Circles"],
)

@router.post("/", response_model=CircleRead, status_code=status.HTTP_201_CREATED)
def create_circle(circle_in: CircleCreate, creator_id: int, session: Session = Depends(get_session)):
    # 验证创建者是否存在
    user = session.get(User, creator_id)
    if not user:
        raise HTTPException(status_code=404, detail="Creator user not found")
        
    # 检查圈子名称是否已存在
    statement = select(Circle).where(Circle.name == circle_in.name)
    existing_circle = session.exec(statement).first()
    if existing_circle:
        raise HTTPException(status_code=400, detail="Circle name already taken")

    # 创建圈子
    db_circle = Circle.model_validate(circle_in, update={"creator_id": creator_id})
    session.add(db_circle)
    session.commit()
    session.refresh(db_circle)
    return db_circle

@router.get("/", response_model=List[CircleRead])
def read_circles(skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    circles = session.exec(select(Circle).offset(skip).limit(limit)).all()
    return circles

@router.get("/{circle_id}", response_model=CircleRead)
def read_circle(circle_id: int, session: Session = Depends(get_session)):
    circle = session.get(Circle, circle_id)
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")
    return circle

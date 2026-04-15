from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from src.auth.dependencies import get_current_user
from src.db.database import get_session
from src.models.core import Circle, CircleCreate, CircleRead, User
from src.models.tags import CircleMember, CircleRole, UserTag


router = APIRouter(prefix="/circles", tags=["Circles"])


@router.post("/", response_model=CircleRead, status_code=status.HTTP_201_CREATED)
def create_circle(
    circle_in: CircleCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create a circle for the authenticated user."""
    if current_user.id is None:
        raise HTTPException(status_code=500, detail="Current user ID missing")

    existing_circle = session.exec(
        select(Circle).where(Circle.name == circle_in.name)
    ).first()
    if existing_circle:
        raise HTTPException(status_code=400, detail="Circle name already taken")

    db_circle = Circle.model_validate(
        circle_in,
        update={"creator_id": current_user.id},
    )
    session.add(db_circle)
    session.flush()

    if db_circle.id is None:
        raise HTTPException(status_code=500, detail="Circle ID missing after creation")

    session.add(
        CircleMember(
            user_id=current_user.id,
            circle_id=db_circle.id,
            role=CircleRole.ADMIN,
        )
    )
    session.commit()
    session.refresh(db_circle)
    return db_circle


@router.get("/", response_model=list[CircleRead])
def read_circles(skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    return session.exec(select(Circle).offset(skip).limit(limit)).all()


@router.get("/{circle_id}", response_model=CircleRead)
def read_circle(circle_id: int, session: Session = Depends(get_session)):
    circle = session.get(Circle, circle_id)
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")
    return circle


@router.post("/{circle_id}/join", status_code=status.HTTP_200_OK)
def join_circle(
    circle_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Join a circle as a member for the authenticated user."""
    if current_user.id is None:
        raise HTTPException(status_code=500, detail="Current user ID missing")

    circle = session.get(Circle, circle_id)
    if circle is None:
        raise HTTPException(status_code=404, detail="Circle not found")

    existing_membership = session.exec(
        select(CircleMember).where(
            CircleMember.circle_id == circle_id,
            CircleMember.user_id == current_user.id,
        )
    ).first()
    if existing_membership is not None:
        raise HTTPException(status_code=409, detail="Already a member")

    session.add(
        CircleMember(
            user_id=current_user.id,
            circle_id=circle_id,
            role=CircleRole.MEMBER,
        )
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Already a member") from None

    return {
        "success": True,
        "message": "Successfully joined the circle",
        "circle_id": circle_id,
    }


@router.delete("/{circle_id}/leave", status_code=status.HTTP_200_OK)
def leave_circle(
    circle_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Leave a circle and remove this user's tag records in the circle."""
    if current_user.id is None:
        raise HTTPException(status_code=500, detail="Current user ID missing")

    membership = session.exec(
        select(CircleMember).where(
            CircleMember.circle_id == circle_id,
            CircleMember.user_id == current_user.id,
        )
    ).first()
    if membership is None:
        raise HTTPException(status_code=404, detail="Membership not found")

    user_tags = session.exec(
        select(UserTag).where(
            UserTag.circle_id == circle_id,
            UserTag.user_id == current_user.id,
        )
    ).all()
    for user_tag in user_tags:
        session.delete(user_tag)

    session.delete(membership)
    session.commit()

    return {
        "success": True,
        "message": "Successfully left the circle",
        "circle_id": circle_id,
    }

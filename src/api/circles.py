from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Field, SQLModel, Session, select

from src.auth.dependencies import get_current_user, get_optional_current_user
from src.db.database import get_session
from src.models.core import Circle, CircleCreate, CircleRead, User
from src.models.tags import CircleMember, CircleRole, UserTag
from src.services.extraction import build_freedom_profile_extractor, extract_freedom_profile
from src.models.teams import encode_freedom_profile, decode_freedom_profile


router = APIRouter(prefix="/circles", tags=["Circles"])


class CircleProfileUpdate(SQLModel):
    """Request model for updating a user's freedom tag in a circle."""
    freedom_tag_text: str = Field(default="", max_length=2000)


class CircleProfileRead(SQLModel):
    """Response model for a user's freedom tag profile in a circle."""
    freedom_tag_text: str
    freedom_tag_profile: dict[str, list[str]]


def build_circle_read(
    circle: Circle,
    session: Session,
    current_user: Optional[User] = None,
) -> CircleRead:
    """Build a circle read payload enriched with creator identity."""
    if circle.id is None or circle.creator_id is None:
        raise HTTPException(status_code=500, detail="Circle ID or creator_id missing")
    
    creator = session.get(User, circle.creator_id)
    current_user_id = current_user.id if current_user is not None else None
    is_creator = current_user_id is not None and circle.creator_id == current_user_id
    is_member = is_creator
    if current_user_id is not None and not is_member:
        membership = session.exec(
            select(CircleMember).where(
                CircleMember.circle_id == circle.id,
                CircleMember.user_id == current_user_id,
            )
        ).first()
        is_member = membership is not None

    return CircleRead(
        id=circle.id,
        name=circle.name,
        description=circle.description,
        category=circle.category,
        creator_id=circle.creator_id,
        creator_username=creator.username if creator is not None else None,
        creator_full_name=creator.full_name if creator is not None else None,
        is_member=is_member,
        is_creator=is_creator,
    )


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
    return build_circle_read(db_circle, session, current_user)


@router.get("/", response_model=list[CircleRead])
def read_circles(
    skip: int = 0,
    limit: int = 100,
    current_user: Optional[User] = Depends(get_optional_current_user),
    session: Session = Depends(get_session),
):
    circles = session.exec(select(Circle).offset(skip).limit(limit)).all()
    return [build_circle_read(circle, session, current_user) for circle in circles]


@router.get("/{circle_id}", response_model=CircleRead)
def read_circle(
    circle_id: int,
    current_user: Optional[User] = Depends(get_optional_current_user),
    session: Session = Depends(get_session),
):
    circle = session.get(Circle, circle_id)
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")
    return build_circle_read(circle, session, current_user)


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


@router.put("/{circle_id}/profile", response_model=CircleProfileRead, status_code=status.HTTP_200_OK)
def update_circle_profile(
    circle_id: int,
    profile_in: CircleProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Update the authenticated user's freedom tag text in the specified circle."""
    if current_user.id is None:
        raise HTTPException(status_code=500, detail="Current user ID missing")

    # Check if the user is a member of the circle
    membership = session.exec(
        select(CircleMember).where(
            CircleMember.circle_id == circle_id,
            CircleMember.user_id == current_user.id,
        )
    ).first()
    if membership is None:
        raise HTTPException(status_code=403, detail="User must join the circle first")

    # Update the freedom tag text
    membership.freedom_tag_text = profile_in.freedom_tag_text

    # Extract freedom profile
    # Note: extract_freedom_profile returns empty keywords if extractor is None
    freedom_profile = extract_freedom_profile(
        profile_in.freedom_tag_text,
        extractor=build_freedom_profile_extractor(),
    )

    # Encode and store the profile
    membership.freedom_tag_profile_json = encode_freedom_profile(freedom_profile)

    session.add(membership)
    session.commit()
    session.refresh(membership)

    # Decode profile for response
    decoded_profile = decode_freedom_profile(membership.freedom_tag_profile_json)

    return CircleProfileRead(
        freedom_tag_text=membership.freedom_tag_text,
        freedom_tag_profile=decoded_profile,
    )

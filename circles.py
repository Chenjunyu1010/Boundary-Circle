from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, database, auth
from typing import List

router = APIRouter(prefix="/circles", tags=["Circles & Tags"])

@router.post("/{circle_id}/join")
def join_circle(
    circle_id: int, 
    data: schemas.CircleJoin, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    FR-2: Join a circle by submitting required tags.
    Validates tags against the circle's predefined schema.
    """
    # 1. Check if the circle exists
    circle = db.query(models.Circle).filter(models.Circle.id == circle_id).first()
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")

    # 2. Basic Validation: Check if submitted tags match circle's requirements
    # Logic: Ensure all keys in circle.tag_schema exist in user_tags
    required_tags = circle.tag_schema.keys()
    for tag in required_tags:
        if tag not in data.user_tags:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required tag: {tag}"
            )

    # 3. Privacy & Isolation (NFR-1): Check if user is already a member
    existing_membership = db.query(models.UserCircleTag).filter(
        models.UserCircleTag.user_id == current_user.id,
        models.UserCircleTag.circle_id == circle_id
    ).first()

    if existing_membership:
        # Update existing tags if already joined
        existing_membership.tags = data.user_tags
    else:
        # Create new relationship (The "Gate" is passed)
        new_membership = models.UserCircleTag(
            user_id=current_user.id,
            circle_id=circle_id,
            tags=data.user_tags
        )
        db.add(new_membership)
    
    db.commit()
    return {"message": "Successfully joined the circle and saved tags"}
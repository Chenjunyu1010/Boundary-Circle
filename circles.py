from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.app import models, schemas, database, auth
from typing import List

router = APIRouter(prefix="/circles", tags=["Circles Workflow"])

@router.post("/{circle_id}/join", response_model=schemas.MessageResponse)
def join_circle(
    circle_id: int, 
    request: schemas.CircleJoinRequest, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    FR-2: Join a circle. 
    Validates circle existence, prevents duplicate membership, and stores user tags.
    """
    # 1. Check if the target circle exists
    circle = db.query(models.Circle).filter(models.Circle.id == circle_id).first()
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")

    # 2. Business Rule: Prevent duplicate joins (Error 409 Conflict)
    existing_membership = db.query(models.UserCircleTag).filter(
        models.UserCircleTag.user_id == current_user.id,
        models.UserCircleTag.circle_id == circle_id
    ).first()
    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="User is already a member of this circle"
        )

    # 3. Create membership record and persist tags
    new_membership = models.UserCircleTag(
        user_id=current_user.id,
        circle_id=circle_id,
        tags=request.user_tags
    )
    db.add(new_membership)
    db.commit()
    return {"message": "Successfully joined the circle"}

@router.delete("/{circle_id}/leave")
def leave_circle(
    circle_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Remove user membership and clean up associated tag data from the circle.
    """
    membership = db.query(models.UserCircleTag).filter(
        models.UserCircleTag.user_id == current_user.id,
        models.UserCircleTag.circle_id == circle_id
    ).first()
    
    # Business Rule: User must be a member to leave
    if not membership:
        raise HTTPException(status_code=404, detail="Membership record not found")
    
    db.delete(membership)
    db.commit()
    return {"message": "Successfully left the circle and cleared tags"}

@router.get("/{circle_id}/members", response_model=List[schemas.MemberOut])
def get_circle_members(circle_id: int, db: Session = Depends(database.get_db)):
    """
    Retrieve the list of all members and their respective tags within a specific circle.
    """
    memberships = db.query(models.UserCircleTag).filter(
        models.UserCircleTag.circle_id == circle_id
    ).all()
    
    # Map database records to the format required by the frontend
    return [
        {
            "user_id": m.user_id,
            "username": m.user.username,
            "tags": m.tags
        } for m in memberships
    ]
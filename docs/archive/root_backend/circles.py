from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, database, auth
from typing import List

router = APIRouter(prefix="/circles", tags=["Circles Workflow"])

# POST /circles/{circle_id}/join - Full Workflow for joining a circle
@router.post("/{circle_id}/join", response_model=schemas.MessageResponse)
def join_circle(
    circle_id: int, 
    request: schemas.CircleJoinRequest, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    FR-2: Join Circle Workflow.
    Includes: Existence check, mandatory tag validation, type checking, 
    and membership creation.
    """
    
    # 1. Verify if user exists (Handled by auth.get_current_user)
    # 2. Verify if circle exists (Error 404)
    circle = db.query(models.Circle).filter(models.Circle.id == circle_id).first()
    if not circle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Circle not found"
        )

    # 3. Check if already a member (Error 409: Conflict)
    existing_membership = db.query(models.UserCircleTag).filter(
        models.UserCircleTag.user_id == current_user.id,
        models.UserCircleTag.circle_id == circle_id
    ).first()
    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="User is already a member of this circle"
        )

    # 4. Get mandatory tag definitions and Validate (Error 400)
    # circle.tag_schema structure example: {"required": {"Major": "str", "GPA": "float"}}
    if circle.tag_schema and "required" in circle.tag_schema:
        required_definitions = circle.tag_schema["required"]
        
        for tag_name, expected_type in required_definitions.items():
            # Check if mandatory tag is missing
            if tag_name not in request.user_tags:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"Missing required tag: {tag_name}"
                )
            
            # 5. Validate tag value type (Error 400)
            val = request.user_tags[tag_name]
            if expected_type == "str" and not isinstance(val, str):
                raise HTTPException(status_code=400, detail=f"Tag '{tag_name}' must be a string")
            elif expected_type == "float" and not isinstance(val, (int, float)):
                raise HTTPException(status_code=400, detail=f"Tag '{tag_name}' must be a number")
            elif expected_type == "list" and not isinstance(val, list):
                raise HTTPException(status_code=400, detail=f"Tag '{tag_name}' must be a list")

    # 6. Create CircleMember & UserTag records (Acceptance Criterion 3)
    # In our simplified schema, these are stored in UserCircleTag
    new_membership = models.UserCircleTag(
        user_id=current_user.id, 
        circle_id=circle_id, 
        tags=request.user_tags
    )
    
    try:
        db.add(new_membership)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database insertion failed")

    # 7. Return success response
    return {"message": "Successfully joined the circle"}

# GET /circles/{circle_id}/members - Retrieve circle members
@router.get("/{circle_id}/members", response_model=List[schemas.MemberOut])
def get_circle_members(circle_id: int, db: Session = Depends(database.get_db)):
    """
    Retrieve list of all members and their tags in a circle.
    """
    memberships = db.query(models.UserCircleTag).filter(
        models.UserCircleTag.circle_id == circle_id
    ).all()
    return [
        {"user_id": m.user_id, "username": m.user.username, "tags": m.tags} 
        for m in memberships
    ]

# DELETE /circles/{circle_id}/leave - Exit the circle
@router.delete("/{circle_id}/leave")
def leave_circle(
    circle_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Remove user membership and tags from the circle.
    """
    membership = db.query(models.UserCircleTag).filter(
        models.UserCircleTag.user_id == current_user.id,
        models.UserCircleTag.circle_id == circle_id
    ).first()
    
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    
    db.delete(membership)
    db.commit()
    return {"message": "Successfully left the circle"}

# Advanced Logic: Partial Match Ranking
@router.post("/{circle_id}/recommend/smart")
def smart_recommend(circle_id: int, criteria: schemas.TagFilterRequest, db: Session = Depends(database.get_db)):
    """
    Ranks members by how many tags match the criteria.
    """
    all_members = db.query(models.UserCircleTag).filter(models.UserCircleTag.circle_id == circle_id).all()
    
    scored_results = []
    filter_items = criteria.filters.items()
    total_criteria = len(filter_items)

    for m in all_members:
        matches = 0
        for key, val in filter_items:
            # Check if tag exists and matches value
            if m.tags.get(key) == val:
                matches += 1
        
        if matches > 0: # Only return people with at least one match
            scored_results.append({
                "user_id": m.user_id,
                "username": m.user.username,
                "match_score": matches / total_criteria if total_criteria > 0 else 0,
                "tags": m.tags
            })

    # Sort by score descending
    scored_results.sort(key=lambda x: x["match_score"], reverse=True)
    return scored_results[:criteria.limit]
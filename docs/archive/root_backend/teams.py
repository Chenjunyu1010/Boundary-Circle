from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, database, auth
from typing import List

router = APIRouter(tags=["Team Management"])

# ==========================================
# 1. Team Management (團隊管理)
# ==========================================

# POST /teams - Create a team
@router.post("/teams", status_code=status.HTTP_201_CREATED)
def create_team(
    name: str, 
    circle_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Check if user joined the circle first (Gating Logic)
    membership = db.query(models.UserCircleTag).filter(
        models.UserCircleTag.user_id == current_user.id,
        models.UserCircleTag.circle_id == circle_id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Must join circle first")

    new_team = models.Team(name=name, circle_id=circle_id, leader_id=current_user.id)
    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    return new_team

# GET /circles/{circle_id}/teams - Get all teams in a circle
@router.get("/circles/{circle_id}/teams")
def get_circle_teams(circle_id: int, db: Session = Depends(database.get_db)):
    return db.query(models.Team).filter(models.Team.circle_id == circle_id).all()

# GET /teams/{team_id} - Get team details
@router.get("/teams/{team_id}")
def get_team_detail(team_id: int, db: Session = Depends(database.get_db)):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

# DELETE /teams/{team_id} - Delete team (Leader only)
@router.delete("/teams/{team_id}")
def delete_team(
    team_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team or team.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only leader can delete")
    db.delete(team)
    db.commit()
    return {"message": "Team deleted"}

# ==========================================
# 2. Invitation Management (邀請管理)
# ==========================================

# POST /teams/{team_id}/invite - Send invitation
@router.post("/teams/{team_id}/invite")
def send_invite(
    team_id: int, 
    invitee_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team or team.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only leader can invite")
    
    new_invitation = models.Invitation(team_id=team_id, invitee_id=invitee_id, status="pending")
    db.add(new_invitation)
    db.commit()
    return {"message": "Invitation sent"}

# POST /invitations/{invite_id}/respond - Accept/Reject invitation
@router.post("/invitations/{invite_id}/respond")
def respond_invite(
    invite_id: int, 
    accept: bool, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    invite = db.query(models.Invitation).filter(models.Invitation.id == invite_id).first()
    if not invite or invite.invitee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your invitation")
    
    invite.status = "accepted" if accept else "rejected"
    if accept:
        # Logic to add user to team_members table
        # team.members.append(current_user)
        pass
    db.commit()
    return {"message": f"Invitation {invite.status}"}

# ==========================================
# 3. Member Management (成員管理)
# ==========================================

# POST /teams/{team_id}/leave - Leave team
@router.post("/teams/{team_id}/leave")
def leave_team(team_id: int, current_user: models.User = Depends(auth.get_current_user)):
    # Logic to remove current_user from team_members
    return {"message": "Left team"}

# POST /teams/{team_id}/members/{user_id}/kick - Kick member (Leader only)
@router.post("/teams/{team_id}/members/{user_id}/kick")
def kick_member(
    team_id: int, 
    user_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team or team.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only leader can kick members")
    # Logic to remove user_id from team_members
    return {"message": f"User {user_id} removed"}
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Table
from sqlalchemy.orm import relationship
from app.database import Base
import enum

# Define Team Status options as per FR-4
class TeamStatus(enum.Enum):
    RECRUITING = "recruiting"
    LOCKED = "locked"

# Many-to-Many relationship table for Team Members
team_members = Table(
    "team_members",
    Base.metadata,
    Column("team_id", Integer, ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
)

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    circle_id = Column(Integer, nullable=False)
    leader_id = Column(Integer, nullable=False) # The user who created the team
    name = Column(String, nullable=False)
    description = Column(String)
    status = Column(Enum(TeamStatus), default=TeamStatus.RECRUITING)
    max_members = Column(Integer, default=4)

    # Relationships
    members = relationship("User", secondary=team_members)
    invitations = relationship("Invitation", back_populates="team")

class Invitation(Base):
    __tablename__ = "invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    invitee_id = Column(Integer, nullable=False)
    status = Column(String, default="pending") # pending, accepted, rejected

    team = relationship("Team", back_populates="invitations")
from sqlalchemy import Column, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from src.app.database import Base

class UserCircleTag(Base):
    """
    Represents the membership relationship between a User and a Circle.
    This model acts as an association table that stores circle-specific user metadata.
    """
    __tablename__ = "user_circle_tags"

    # Primary key for the membership record
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key linking to the User model
    # ondelete="CASCADE" ensures membership is removed if the user is deleted
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Foreign key linking to the Circle model
    # ondelete="CASCADE" ensures membership is removed if the circle is deleted
    circle_id = Column(Integer, ForeignKey("circles.id", ondelete="CASCADE"), nullable=False)
    
    # Stores user-submitted tags specifically for this circle in JSON format
    # Example: {"Major": "Computer Science", "GPA": 3.8, "Skills": ["Python", "FastAPI"]}
    tags = Column(JSON, nullable=True)

    # Relationship to access User object details (e.g., username)
    user = relationship("User", back_populates="circle_memberships")

    # Relationship to access Circle object details (e.g., circle name, tag_schema)
    circle = relationship("Circle", back_populates="members")

# Note: Ensure that the User and Circle models have the corresponding 
# 'circle_memberships' and 'members' relationships defined with back_populates.
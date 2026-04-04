from pydantic import BaseModel
from typing import Dict, Any, List

# Request schema for joining a circle and submitting tags
class CircleJoinRequest(BaseModel):
    # e.g., {"Major": "CS", "GPA": 3.8, "Skills": ["Python"]}
    user_tags: Dict[str, Any]

# Output schema for a single circle member
class MemberOut(BaseModel):
    user_id: int
    username: str
    tags: Dict[str, Any]

    class Config:
        from_attributes = True

# Standard response for successful actions
class MessageResponse(BaseModel):
    message: str
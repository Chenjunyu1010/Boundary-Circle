from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

# Schema for joining a circle
class CircleJoin(BaseModel):
    # Flexible dictionary to store tags like {"GPA": 3.8, "Skills": ["Python", "Java"]}
    user_tags: Dict[str, Any] 

class CircleRead(BaseModel):
    id: int
    name: str
    tag_schema: Dict[str, Any] # Defines what tags are required

    class Config:
        from_attributes = True
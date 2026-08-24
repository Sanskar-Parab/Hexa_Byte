from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class SkillCreate(BaseModel):
    name: str
    category: str
    description: Optional[str] = None


class SkillResponse(BaseModel):
    id: UUID
    name: str
    category: str
    description: Optional[str] = None
    beginner_definition: Optional[str] = None
    intermediate_definition: Optional[str] = None
    advanced_definition: Optional[str] = None

    class Config:
        from_attributes = True


class UserSkillCreate(BaseModel):
    skill_id: UUID
    proficiency: int  # 1-5


class UserSkillResponse(BaseModel):
    id: UUID
    skill_id: UUID
    skill_name: Optional[str] = None
    proficiency: int
    created_at: datetime

    class Config:
        from_attributes = True

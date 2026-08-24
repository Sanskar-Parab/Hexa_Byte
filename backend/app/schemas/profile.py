from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class ProfileCreate(BaseModel):
    age_group: Optional[str] = None
    education_level: Optional[str] = None
    degree: Optional[str] = None
    branch: Optional[str] = None
    current_year: Optional[str] = None
    internship_experience: Optional[str] = None
    work_experience: Optional[str] = None
    projects_count: int = 0


class ProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    age_group: Optional[str] = None
    education_level: Optional[str] = None
    degree: Optional[str] = None
    branch: Optional[str] = None
    current_year: Optional[str] = None
    internship_experience: Optional[str] = None
    work_experience: Optional[str] = None
    projects_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OnboardingData(BaseModel):
    profile: ProfileCreate
    skills: list[dict] = []
    interests: list[str] = []

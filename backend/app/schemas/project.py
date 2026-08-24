from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class ProjectResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    difficulty: Optional[str] = None
    skills_developed: Optional[list] = None
    expected_outcome: Optional[str] = None
    estimated_duration_weeks: Optional[int] = None
    portfolio_value: Optional[str] = None

    class Config:
        from_attributes = True


class RecommendedProjectResponse(BaseModel):
    id: UUID
    project: ProjectResponse
    career_id: UUID
    status: str = "recommended"
    created_at: datetime

    class Config:
        from_attributes = True

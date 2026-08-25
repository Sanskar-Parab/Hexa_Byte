from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class RoadmapPhaseResponse(BaseModel):
    id: UUID
    phase_number: int
    title: str
    objective: Optional[str] = None
    skills: Optional[list] = None
    activities: Optional[list] = None
    project: Optional[str] = None
    duration_weeks: Optional[int] = None
    completion_criteria: Optional[list] = None
    status: str = "not_started"
    adaptation_mode: str = "full"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RoadmapResponse(BaseModel):
    id: UUID
    career_id: UUID
    career_name: Optional[str] = None
    summary: Optional[str] = None
    phases: list[RoadmapPhaseResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RoadmapCreate(BaseModel):
    career_id: UUID

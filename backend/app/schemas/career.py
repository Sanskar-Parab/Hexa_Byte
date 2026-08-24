from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class CareerResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    required_skills: Optional[list] = None
    optional_skills: Optional[list] = None
    skill_importance: Optional[dict] = None
    recommended_projects: Optional[list] = None
    learning_sequence: Optional[list] = None
    related_careers: Optional[list] = None

    class Config:
        from_attributes = True


class CareerRecommendationResponse(BaseModel):
    id: UUID
    career_id: UUID
    career_name: Optional[str] = None
    match_score: float
    confidence: Optional[str] = None
    why_it_matches: Optional[list] = None
    strengths: Optional[list] = None
    skill_gaps: Optional[list] = None
    created_at: datetime

    class Config:
        from_attributes = True

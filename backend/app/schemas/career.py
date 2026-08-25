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
    biggest_blocker: Optional[str] = None
    recommended_action: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SkillDetailResponse(BaseModel):
    skill_name: str
    importance: float
    user_proficiency: int
    evidence_confidence: str
    gap: int
    status: str


class UserSkillBrief(BaseModel):
    name: str
    proficiency: str
    confidence: str


class CareerIntelligenceResponse(BaseModel):
    career_id: UUID
    career_name: str
    match_score: float
    confidence: Optional[str] = None
    why_matches: Optional[list] = None
    strengths: Optional[list] = None
    skill_gaps: Optional[list] = None
    biggest_blocker: Optional[str] = None
    recommended_action: Optional[str] = None
    skill_details: Optional[list] = None
    user_current_skills: Optional[list] = None
    learning_sequence: Optional[list] = None
    description: Optional[str] = None
    required_skills: Optional[list] = None
    optional_skills: Optional[list] = None

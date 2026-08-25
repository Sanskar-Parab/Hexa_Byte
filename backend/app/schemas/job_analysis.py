from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class JobAnalysisRequest(BaseModel):
    job_description: str


class JobSkillMatch(BaseModel):
    skill_name: str
    status: str  # strong, developing, missing, not_demonstrated
    user_proficiency: int = 0
    confidence: Optional[str] = None
    evidence_count: int = 0
    is_required: bool = True


class JobAnalysisResponse(BaseModel):
    job_title: str
    required_skills: list[str]
    preferred_skills: list[str]
    experience_required: Optional[str] = None
    education_required: Optional[str] = None
    responsibilities: list[str]
    technologies: list[str]


class JobMatchResponse(BaseModel):
    analysis_id: str
    job_title: str
    alignment_percentage: float
    strong_skills: list[JobSkillMatch]
    developing_skills: list[JobSkillMatch]
    missing_skills: list[JobSkillMatch]
    not_demonstrated: list[JobSkillMatch]
    top_gap: Optional[str] = None
    next_action: Optional[str] = None
    evidence_created: int
    required_skills_count: int
    matched_count: int


class JobAnalysisDetailResponse(BaseModel):
    id: str
    job_title: str
    raw_text: str
    required_skills: list[str]
    preferred_skills: list[str]
    experience_required: Optional[str] = None
    education_required: Optional[str] = None
    responsibilities: list[str]
    technologies: list[str]
    match_result: Optional[JobMatchResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True

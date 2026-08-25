from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class ResumeSkillItem(BaseModel):
    skill_name: str
    skill_id: Optional[str] = None
    context: str


class ResumeExtraction(BaseModel):
    skills: list[str]
    projects: list[str]
    experience: list[str]
    education: list[str]
    certifications: list[str]
    technologies: list[str]
    tools: list[str]


class ResumeUploadResponse(BaseModel):
    resume_id: str
    filename: str
    extraction: ResumeExtraction
    matched_skills: list[ResumeSkillItem]
    evidence_created: int
    message: str


class ResumeDetailResponse(BaseModel):
    id: str
    filename: str
    extraction: ResumeExtraction
    matched_skills: list[ResumeSkillItem]
    extracted_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class EvidenceResponse(BaseModel):
    id: UUID
    source_type: str
    source_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    score: Optional[float] = None
    confidence: str
    metadata: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SkillEvidenceResponse(BaseModel):
    skill_id: UUID
    skill_name: str
    proficiency: int
    level_name: Optional[str] = None
    confidence: str
    evidence: list[EvidenceResponse]

from pydantic import BaseModel
from typing import Literal, Optional
from uuid import UUID


class SkillBreakdownItem(BaseModel):
    skill: str
    user_proficiency: int
    status: Literal["strong", "developing", "gap"]


class TrainingSkillMatchResponse(BaseModel):
    training_program_id: UUID
    training_program_name: str
    skills_taught: list[str]
    coverage_score: int
    strong_skills: list[str]
    developing_skills: list[str]
    gap_skills: list[str]
    skill_breakdown: list[SkillBreakdownItem]


class TrainingRelevanceResponse(BaseModel):
    level: Literal["high", "medium", "low", "unknown"]
    reason: str
    overlap_skills: list[str]
    coverage_ratio: float

from uuid import UUID
from pydantic import BaseModel
from typing import Optional
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


class SkillAwareProjectResponse(BaseModel):
    id: str
    project: ProjectResponse
    career_id: str
    composite_score: float
    career_relevance: float
    gap_relevance: float
    roadmap_relevance: float
    difficulty_fit: float
    covers_skills: list[str]
    gap_skills_covered: list[str]
    project_difficulty: str
    user_difficulty: str
    status: str
    is_ai_generated: bool = False


class AIGeneratedProjectResponse(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    difficulty: str
    why_this_project: str
    skills_practiced: list[str]
    skills_targeted: list[str]
    duration: str
    learning_objectives: list[str]
    deliverables: list[str]
    completion_criteria: list[str]
    status: str = "recommended"
    created_at: Optional[datetime] = None


class GenerateProjectsRequest(BaseModel):
    career_id: UUID
    count: int = 3


class PreferredDifficultyRequest(BaseModel):
    difficulty: str  # AUTO, BEGINNER, INTERMEDIATE, ADVANCED, INDUSTRY

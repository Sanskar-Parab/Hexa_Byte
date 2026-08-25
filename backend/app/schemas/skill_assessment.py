from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class AssessmentStartRequest(BaseModel):
    skill_id: UUID


class AssessmentQuestionOut(BaseModel):
    id: int
    difficulty: str
    type: str
    question: str
    options: list[str]


class AssessmentSkillInfo(BaseModel):
    id: UUID
    name: str


class AssessmentStartResponse(BaseModel):
    assessment_id: UUID
    skill: AssessmentSkillInfo
    questions: list[AssessmentQuestionOut]


class AIAvailabilityResponse(BaseModel):
    available: bool
    error: Optional[str] = None


class AnswerItem(BaseModel):
    question_id: int
    answer: str


class AssessmentSubmitRequest(BaseModel):
    assessment_id: UUID
    answers: list[AnswerItem]


class AssessmentResultResponse(BaseModel):
    assessment_id: UUID
    skill: AssessmentSkillInfo
    proficiency: int
    level_name: str
    score_percentage: float
    strengths: list[str]
    weaknesses: list[str]
    recommended_topics: list[str]
    summary: str
    confidence: str

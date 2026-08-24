from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class AssessmentQuestionResponse(BaseModel):
    id: UUID
    question_text: str
    category: str
    options: list

    class Config:
        from_attributes = True


class AssessmentSubmit(BaseModel):
    answers: dict  # question_id -> selected_option_index


class AssessmentResult(BaseModel):
    scores: dict
    interpretation: dict
    top_interests: list[str]

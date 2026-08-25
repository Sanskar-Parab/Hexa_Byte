from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.schemas.skill_assessment import (
    AssessmentStartRequest,
    AssessmentStartResponse,
    AssessmentSubmitRequest,
    AssessmentResultResponse,
    AIAvailabilityResponse,
)
from app.services.skill_assessment_service import start_assessment, submit_assessment, check_ai_availability
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/skill-assessment", tags=["skill-assessment"])


@router.get("/ai-status", response_model=AIAvailabilityResponse)
def get_ai_status():
    """Check if AI service is available for assessments."""
    status = check_ai_availability()
    return AIAvailabilityResponse(**status)


@router.post("/start", response_model=AssessmentStartResponse)
def start_skill_assessment(
    request: AssessmentStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = start_assessment(db, current_user.id, request.skill_id)
        return AssessmentStartResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to start assessment")


@router.post("/submit", response_model=AssessmentResultResponse)
def submit_skill_assessment(
    request: AssessmentSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        answers = [{"question_id": a.question_id, "answer": a.answer} for a in request.answers]
        result = submit_assessment(db, current_user.id, request.assessment_id, answers)
        return AssessmentResultResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to submit assessment")

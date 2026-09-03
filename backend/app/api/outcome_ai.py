from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.schemas.outcome_ai import (
    NonPlacementAnalysisResponse,
    AttritionAnalysisResponse,
    TrainingRelevanceExplanationResponse,
)
from app.services import outcome_ai_analysis, outcome_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/outcomes/analysis", tags=["outcome-ai-analysis"])


@router.get("/non-placement", response_model=NonPlacementAnalysisResponse)
def get_non_placement_analysis(
    career_id: UUID | None = Query(default=None),
    training_enrollment_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Why the authenticated user hasn't been placed yet — grounded only in
    their own stored, deterministically-computed evidence."""
    result = outcome_ai_analysis.analyze_non_placement(
        db, current_user.id, career_id=career_id, training_enrollment_id=training_enrollment_id,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Training enrollment not found")
    return result


@router.get("/attrition", response_model=AttritionAnalysisResponse)
def get_attrition_analysis(
    employment_outcome_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Why the authenticated user's employment ended — grounded only in
    their own stored evidence (check-in reasons, notes, salary, relevance)."""
    result = outcome_ai_analysis.analyze_attrition(db, current_user.id, employment_outcome_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Employment outcome not found")
    return result


@router.get("/relevance-explanation", response_model=TrainingRelevanceExplanationResponse)
def get_relevance_explanation(
    training_program_id: UUID = Query(...),
    employment_outcome_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Plain-language explanation of the deterministic training-relevance
    score — the AI narrates the level, it never sets or changes it."""
    employment_job_title = None
    if employment_outcome_id:
        outcome = outcome_service.get_employment_outcome(db, current_user.id, employment_outcome_id)
        if not outcome:
            raise HTTPException(status_code=404, detail="Employment outcome not found")
        employment_job_title = outcome.job_title

    result = outcome_ai_analysis.explain_training_relevance(
        db, current_user.id, training_program_id, employment_job_title=employment_job_title,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Training program not found")
    return result

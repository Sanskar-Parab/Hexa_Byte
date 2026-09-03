from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.schemas.training_intelligence import (
    TrainingSkillMatchResponse,
    TrainingRelevanceResponse,
)
from app.services import outcome_service, training_intelligence
from app.services.opportunity_recommendation import get_user_skill_map
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/outcomes", tags=["training-intelligence"])


# ---------------------------------------------------------------------------
# Training <-> student skill comparison
# ---------------------------------------------------------------------------

@router.get("/training/{training_program_id}/skill-match", response_model=TrainingSkillMatchResponse)
def get_training_skill_match(
    training_program_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compares the training program's taught skills against the authenticated
    user's own demonstrated skills — never a client-supplied user."""
    result = training_intelligence.compare_training_to_student_skills(db, current_user.id, training_program_id)
    if not result:
        raise HTTPException(status_code=404, detail="Training program not found")
    return result


# ---------------------------------------------------------------------------
# Training relevance
# ---------------------------------------------------------------------------

@router.get("/training/{training_program_id}/relevance", response_model=TrainingRelevanceResponse)
def get_training_relevance(
    training_program_id: UUID,
    employment_outcome_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deterministic training-relevance calculation against either a specific
    employment outcome (must belong to the caller) or, with no outcome given,
    against the caller's demonstrated skills alone."""
    program = outcome_service.get_training_program(db, training_program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Training program not found")

    training_skills = outcome_service.training_program_skill_names(db, program)
    student_skill_map = get_user_skill_map(db, current_user.id)

    employment_job_title = None
    if employment_outcome_id:
        outcome = outcome_service.get_employment_outcome(db, current_user.id, employment_outcome_id)
        if not outcome:
            raise HTTPException(status_code=404, detail="Employment outcome not found")
        employment_job_title = outcome.job_title

    return training_intelligence.calculate_training_relevance(
        db=db,
        training_skills=training_skills,
        student_skill_map=student_skill_map,
        employment_job_title=employment_job_title,
    )


# ---------------------------------------------------------------------------
# Placement readiness
# ---------------------------------------------------------------------------

@router.get("/readiness")
def get_placement_readiness(
    career_id: UUID | None = Query(default=None),
    training_enrollment_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = training_intelligence.calculate_placement_readiness(
        db, current_user.id, career_id=career_id, training_enrollment_id=training_enrollment_id
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Training enrollment not found")
    return result


# ---------------------------------------------------------------------------
# Opportunities, biased by training career domain
# ---------------------------------------------------------------------------

@router.get("/opportunities")
def get_training_opportunities(
    training_enrollment_id: UUID | None = Query(default=None),
    type: str = Query("all", pattern="^(all|internship|job)$"),
    limit: int = Query(10, ge=1, le=50),
    min_match: int = Query(0, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = training_intelligence.get_opportunities_for_training(
        db,
        current_user.id,
        training_enrollment_id=training_enrollment_id,
        opportunity_type=type,
        limit=limit,
        min_match=min_match,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Training enrollment not found")
    return result

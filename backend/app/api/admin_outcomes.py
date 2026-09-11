from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.schemas.outcome import EmploymentOutcomeResponse
from app.services import outcome_service
from app.utils.auth import get_current_user, get_current_admin_user

router = APIRouter(prefix="/api/admin/outcomes", tags=["admin-outcomes"])


def _to_response(outcome) -> EmploymentOutcomeResponse:
    # Ensure evidence_level fallback for old rows
    lvl = getattr(outcome, "evidence_level", None)
    if not lvl:
        lvl = "verified" if getattr(outcome, "verified", False) else "self_reported"
    # Build dict to let Pydantic validator handle coercion as well, but set explicitly
    data = {
        "id": outcome.id,
        "user_id": outcome.user_id,
        "training_enrollment_id": outcome.training_enrollment_id,
        "employment_status": outcome.employment_status,
        "employment_type": outcome.employment_type,
        "company_name": outcome.company_name,
        "job_title": outcome.job_title,
        "industry": outcome.industry,
        "location": outcome.location,
        "country": outcome.country,
        "is_remote": outcome.is_remote,
        "employment_start_date": outcome.employment_start_date,
        "employment_end_date": outcome.employment_end_date,
        "salary": outcome.salary,
        "salary_currency": outcome.salary_currency,
        "salary_period": outcome.salary_period,
        "source": outcome.source,
        "source_opportunity_id": outcome.source_opportunity_id,
        "source_opportunity_title": outcome.source_opportunity_title,
        "verified": outcome.verified,
        "evidence_level": lvl,
        "created_at": outcome.created_at,
        "updated_at": outcome.updated_at,
    }
    return EmploymentOutcomeResponse.model_validate(data)


@router.get("/employment", response_model=list[EmploymentOutcomeResponse])
def admin_list_employment_outcomes(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    employment_status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Admin read-only listing of individual employment outcome records for verification UI."""
    outcomes = outcome_service.list_all_employment_outcomes(db, limit=limit, offset=offset)
    if employment_status:
        outcomes = [o for o in outcomes if o.employment_status == employment_status]
    return [_to_response(o) for o in outcomes]


@router.patch("/{outcome_id}/verify", response_model=EmploymentOutcomeResponse)
def admin_verify_outcome(
    outcome_id: UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Admin-only verification: sets verified=true, source=verified_employer, evidence_level=verified."""
    outcome = outcome_service.get_employment_outcome_by_id(db, outcome_id)
    if not outcome:
        raise HTTPException(status_code=404, detail="Employment outcome not found")
    verified_outcome = outcome_service.verify_employment_outcome(db, outcome)
    return _to_response(verified_outcome)


# Student-owned evidence submission (minimal MVP, no document storage)
student_evidence_router = APIRouter(prefix="/api/outcomes", tags=["outcomes"])


@student_evidence_router.patch("/employment/{outcome_id}/evidence", response_model=EmploymentOutcomeResponse)
def submit_evidence(
    outcome_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Student submits evidence for own outcome (self_employed or any). Moves self_reported -> evidence_submitted."""
    outcome = outcome_service.get_employment_outcome(db, current_user.id, outcome_id)
    if not outcome:
        raise HTTPException(status_code=404, detail="Employment outcome not found")
    if outcome.verified or getattr(outcome, "evidence_level", None) == "verified":
        raise HTTPException(status_code=400, detail="Outcome already verified")
    updated = outcome_service.submit_evidence_for_outcome(db, outcome)
    return _to_response(updated)

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.schemas.outcome import (
    TrainingProgramCreate,
    TrainingProgramResponse,
    TrainingEnrollmentCreate,
    TrainingEnrollmentUpdate,
    TrainingEnrollmentResponse,
    EmploymentOutcomeCreate,
    EmploymentOutcomeResponse,
    OutcomeCheckInCreate,
    OutcomeCheckInResponse,
    OutcomeConsentUpdate,
    OutcomeConsentResponse,
)
from app.services import outcome_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/outcomes", tags=["outcomes"])


# ---------------------------------------------------------------------------
# Training Program (shared catalog; any authenticated user may add/list)
# ---------------------------------------------------------------------------

@router.post("/training", response_model=TrainingProgramResponse)
def create_training_program(
    data: TrainingProgramCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    program = outcome_service.create_training_program(db, data)
    return _program_to_response(db, program)


@router.get("/training", response_model=list[TrainingProgramResponse])
def list_training_programs(
    career_domain: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    programs = outcome_service.list_training_programs(db, career_domain=career_domain, status=status)
    return [_program_to_response(db, p) for p in programs]


def _program_to_response(db: Session, program) -> TrainingProgramResponse:
    return TrainingProgramResponse(
        id=program.id,
        name=program.name,
        provider_name=program.provider_name,
        description=program.description,
        skills=outcome_service.training_program_skill_names(db, program),
        career_domain=program.career_domain,
        location=program.location,
        start_date=program.start_date,
        end_date=program.end_date,
        certification=program.certification,
        status=program.status,
        created_at=program.created_at,
        updated_at=program.updated_at,
    )


# ---------------------------------------------------------------------------
# Training Enrollment (user-scoped)
# ---------------------------------------------------------------------------

@router.post("/enrollment", response_model=TrainingEnrollmentResponse)
def create_enrollment(
    data: TrainingEnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    program = outcome_service.get_training_program(db, data.training_program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Training program not found")

    enrollment = outcome_service.create_enrollment(db, current_user.id, data)
    return enrollment


@router.get("/enrollment", response_model=list[TrainingEnrollmentResponse])
def list_enrollments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return outcome_service.list_enrollments(db, current_user.id)


@router.patch("/enrollment/{enrollment_id}", response_model=TrainingEnrollmentResponse)
def update_enrollment(
    enrollment_id: UUID,
    data: TrainingEnrollmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enrollment = outcome_service.get_enrollment(db, current_user.id, enrollment_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return outcome_service.update_enrollment(db, enrollment, data)


# ---------------------------------------------------------------------------
# Employment Outcome (user-scoped; requires active consent)
# ---------------------------------------------------------------------------

@router.post("/employment", response_model=EmploymentOutcomeResponse)
def create_employment_outcome(
    data: EmploymentOutcomeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not outcome_service.has_active_consent(db, current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Outcome data collection requires active consent. Submit consent via POST /api/outcomes/consent first.",
        )

    if data.training_enrollment_id:
        enrollment = outcome_service.get_enrollment(db, current_user.id, data.training_enrollment_id)
        if not enrollment:
            raise HTTPException(status_code=404, detail="Training enrollment not found")

    return outcome_service.create_employment_outcome(db, current_user.id, data)


@router.get("/employment", response_model=list[EmploymentOutcomeResponse])
def list_employment_outcomes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return outcome_service.list_employment_outcomes(db, current_user.id)


# ---------------------------------------------------------------------------
# Outcome Check-in (user-scoped via owning EmploymentOutcome; requires consent)
# ---------------------------------------------------------------------------

@router.post("/check-in", response_model=OutcomeCheckInResponse)
def create_check_in(
    data: OutcomeCheckInCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not outcome_service.has_active_consent(db, current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Outcome data collection requires active consent. Submit consent via POST /api/outcomes/consent first.",
        )

    outcome = outcome_service.get_employment_outcome(db, current_user.id, data.employment_outcome_id)
    if not outcome:
        raise HTTPException(status_code=404, detail="Employment outcome not found")

    return outcome_service.create_check_in(db, outcome, data)


@router.get("/check-ins", response_model=list[OutcomeCheckInResponse])
def list_check_ins(
    employment_outcome_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return outcome_service.list_check_ins(db, current_user.id, employment_outcome_id=employment_outcome_id)


# ---------------------------------------------------------------------------
# Consent
# ---------------------------------------------------------------------------

@router.post("/consent", response_model=OutcomeConsentResponse)
def submit_consent(
    data: OutcomeConsentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return outcome_service.set_consent(db, current_user.id, data.consented)


@router.get("/consent", response_model=OutcomeConsentResponse)
def get_consent(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    consent = outcome_service.get_consent(db, current_user.id)
    if not consent:
        return OutcomeConsentResponse(
            user_id=current_user.id,
            consented=False,
            consent_date=None,
            revoked_at=None,
        )
    return consent

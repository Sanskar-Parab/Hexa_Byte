from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.outcome import (
    TrainingProgram,
    TrainingProgramSkill,
    TrainingEnrollment,
    EmploymentOutcome,
    OutcomeCheckIn,
    OutcomeConsent,
)
from app.models.skill import Skill
from app.services.skill_normalization import build_alias_index, match_skill_to_known


# ---------------------------------------------------------------------------
# Consent
# ---------------------------------------------------------------------------

def get_consent(db: Session, user_id: UUID) -> OutcomeConsent | None:
    """Get the consent record for a user, if one exists."""
    return db.query(OutcomeConsent).filter(OutcomeConsent.user_id == user_id).first()


def has_active_consent(db: Session, user_id: UUID) -> bool:
    """Whether the user currently consents to employment outcome data collection."""
    consent = get_consent(db, user_id)
    return bool(consent and consent.consented and consent.revoked_at is None)


def set_consent(db: Session, user_id: UUID, consented: bool) -> OutcomeConsent:
    """Create or update a user's outcome-tracking consent."""
    consent = get_consent(db, user_id)
    now = datetime.utcnow()

    if not consent:
        consent = OutcomeConsent(
            user_id=user_id,
            consented=consented,
            consent_date=now if consented else None,
            revoked_at=None if consented else now,
        )
        db.add(consent)
    else:
        if consented and not consent.consented:
            consent.consent_date = now
            consent.revoked_at = None
        elif not consented and consent.consented:
            consent.revoked_at = now
        consent.consented = consented

    db.commit()
    db.refresh(consent)
    return consent


# ---------------------------------------------------------------------------
# Training Program (catalog entity, not user-scoped)
# ---------------------------------------------------------------------------

def create_training_program(db: Session, data) -> TrainingProgram:
    program = TrainingProgram(
        name=data.name,
        provider_name=data.provider_name,
        description=data.description,
        career_domain=data.career_domain,
        location=data.location,
        start_date=data.start_date,
        end_date=data.end_date,
        certification=data.certification,
        status=data.status,
    )
    db.add(program)
    db.flush()

    catalog_skills = db.query(Skill).all()
    catalog_index = build_alias_index([s.name for s in catalog_skills])
    catalog_by_name = {s.name: s for s in catalog_skills}

    for skill_name in data.skill_names:
        resolved_name = match_skill_to_known(skill_name, catalog_index)
        skill = catalog_by_name.get(resolved_name) if resolved_name else None
        if not skill:
            continue
        exists = db.query(TrainingProgramSkill).filter(
            TrainingProgramSkill.training_program_id == program.id,
            TrainingProgramSkill.skill_id == skill.id,
        ).first()
        if not exists:
            db.add(TrainingProgramSkill(training_program_id=program.id, skill_id=skill.id))

    db.commit()
    db.refresh(program)
    return program


def list_training_programs(
    db: Session,
    career_domain: str | None = None,
    status: str | None = None,
) -> list[TrainingProgram]:
    query = db.query(TrainingProgram)
    if career_domain:
        query = query.filter(TrainingProgram.career_domain == career_domain)
    if status:
        query = query.filter(TrainingProgram.status == status)
    return query.order_by(TrainingProgram.created_at.desc()).all()


def get_training_program(db: Session, training_program_id: UUID) -> TrainingProgram | None:
    return db.query(TrainingProgram).filter(TrainingProgram.id == training_program_id).first()


def training_program_skill_names(db: Session, program: TrainingProgram) -> list[str]:
    links = db.query(TrainingProgramSkill).filter(
        TrainingProgramSkill.training_program_id == program.id
    ).all()
    if not links:
        return []
    skill_ids = [link.skill_id for link in links]
    skills = db.query(Skill).filter(Skill.id.in_(skill_ids)).all()
    return [s.name for s in skills]


# ---------------------------------------------------------------------------
# Training Enrollment
# ---------------------------------------------------------------------------

def create_enrollment(db: Session, user_id: UUID, data) -> TrainingEnrollment:
    enrollment = TrainingEnrollment(
        user_id=user_id,
        training_program_id=data.training_program_id,
        enrollment_date=data.enrollment_date or datetime.utcnow().date(),
        status=data.status,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def list_enrollments(db: Session, user_id: UUID) -> list[TrainingEnrollment]:
    return db.query(TrainingEnrollment).filter(
        TrainingEnrollment.user_id == user_id,
    ).order_by(TrainingEnrollment.created_at.desc()).all()


def get_enrollment(db: Session, user_id: UUID, enrollment_id: UUID) -> TrainingEnrollment | None:
    """Fetch an enrollment, scoped to its owner — never resolves another user's record."""
    return db.query(TrainingEnrollment).filter(
        TrainingEnrollment.id == enrollment_id,
        TrainingEnrollment.user_id == user_id,
    ).first()


def update_enrollment(db: Session, enrollment: TrainingEnrollment, data) -> TrainingEnrollment:
    if data.completion_date is not None:
        enrollment.completion_date = data.completion_date
    if data.status is not None:
        enrollment.status = data.status
    if data.attendance_percentage is not None:
        enrollment.attendance_percentage = data.attendance_percentage
    if data.assessment_score is not None:
        enrollment.assessment_score = data.assessment_score
    if data.certificate_status is not None:
        enrollment.certificate_status = data.certificate_status

    db.commit()
    db.refresh(enrollment)
    return enrollment


# ---------------------------------------------------------------------------
# Employment Outcome
# ---------------------------------------------------------------------------

def create_employment_outcome(db: Session, user_id: UUID, data) -> EmploymentOutcome:
    outcome = EmploymentOutcome(
        user_id=user_id,
        training_enrollment_id=data.training_enrollment_id,
        employment_status=data.employment_status,
        employment_type=data.employment_type,
        company_name=data.company_name,
        job_title=data.job_title,
        industry=data.industry,
        location=data.location,
        country=data.country,
        is_remote=data.is_remote,
        employment_start_date=data.employment_start_date,
        employment_end_date=data.employment_end_date,
        salary=data.salary,
        salary_currency=data.salary_currency,
        salary_period=data.salary_period,
        source=data.source,
        source_opportunity_id=data.source_opportunity_id,
        source_opportunity_title=data.source_opportunity_title,
        verified=False,
    )
    db.add(outcome)
    db.commit()
    db.refresh(outcome)
    return outcome


def list_employment_outcomes(db: Session, user_id: UUID) -> list[EmploymentOutcome]:
    return db.query(EmploymentOutcome).filter(
        EmploymentOutcome.user_id == user_id,
    ).order_by(EmploymentOutcome.created_at.desc()).all()


def get_employment_outcome(db: Session, user_id: UUID, outcome_id: UUID) -> EmploymentOutcome | None:
    """Fetch an outcome, scoped to its owner — never resolves another user's record."""
    return db.query(EmploymentOutcome).filter(
        EmploymentOutcome.id == outcome_id,
        EmploymentOutcome.user_id == user_id,
    ).first()


# ---------------------------------------------------------------------------
# Outcome Check-in
# ---------------------------------------------------------------------------

def create_check_in(db: Session, employment_outcome: EmploymentOutcome, data) -> OutcomeCheckIn:
    check_in = OutcomeCheckIn(
        employment_outcome_id=employment_outcome.id,
        check_in_date=data.check_in_date or datetime.utcnow().date(),
        months_since_employment=data.months_since_employment,
        employment_status=data.employment_status,
        company_name=data.company_name,
        job_title=data.job_title,
        salary=data.salary,
        salary_currency=data.salary_currency,
        salary_period=data.salary_period,
        training_relevance=data.training_relevance,
        still_employed=data.still_employed,
        reason_for_leaving=data.reason_for_leaving,
        notes=data.notes,
    )
    db.add(check_in)
    db.commit()
    db.refresh(check_in)
    return check_in


def list_check_ins(db: Session, user_id: UUID, employment_outcome_id: UUID | None = None) -> list[OutcomeCheckIn]:
    """List check-ins for a user, scoped through the owning EmploymentOutcome."""
    query = db.query(OutcomeCheckIn).join(
        EmploymentOutcome, OutcomeCheckIn.employment_outcome_id == EmploymentOutcome.id,
    ).filter(EmploymentOutcome.user_id == user_id)

    if employment_outcome_id:
        query = query.filter(OutcomeCheckIn.employment_outcome_id == employment_outcome_id)

    return query.order_by(OutcomeCheckIn.check_in_date.desc()).all()

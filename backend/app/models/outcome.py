import uuid
from datetime import date, datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.models.types import GUID
from app.database.config import Base


class TrainingProgram(Base):
    """A skilling/training program offered by a provider (catalog entity, not user-owned)."""

    __tablename__ = "training_programs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    provider_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    career_domain = Column(String, nullable=True)
    location = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    certification = Column(String, nullable=True)
    status = Column(String, nullable=False, default="active")  # planned, active, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    skill_links = relationship(
        "TrainingProgramSkill", back_populates="training_program", cascade="all, delete-orphan"
    )
    enrollments = relationship("TrainingEnrollment", back_populates="training_program")


class TrainingProgramSkill(Base):
    """Many-to-many link between a TrainingProgram and the Skill catalog."""

    __tablename__ = "training_program_skills"
    __table_args__ = (
        UniqueConstraint("training_program_id", "skill_id", name="uq_training_program_skill"),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    training_program_id = Column(GUID(), ForeignKey("training_programs.id"), nullable=False, index=True)
    skill_id = Column(GUID(), ForeignKey("skills.id"), nullable=False, index=True)

    training_program = relationship("TrainingProgram", back_populates="skill_links")
    skill = relationship("Skill")


class TrainingEnrollment(Base):
    """A user's enrollment in a TrainingProgram."""

    __tablename__ = "training_enrollments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    training_program_id = Column(GUID(), ForeignKey("training_programs.id"), nullable=False, index=True)
    enrollment_date = Column(Date, nullable=False, default=date.today)
    completion_date = Column(Date, nullable=True)
    status = Column(String, nullable=False, default="enrolled")  # enrolled, in_progress, completed, dropped, withdrawn
    attendance_percentage = Column(Float, nullable=True)
    assessment_score = Column(Float, nullable=True)
    certificate_status = Column(String, nullable=True)  # not_issued, pending, issued
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    training_program = relationship("TrainingProgram", back_populates="enrollments")
    employment_outcomes = relationship("EmploymentOutcome", back_populates="training_enrollment")


class EmploymentOutcome(Base):
    """A user's employment/placement outcome, optionally linked to a training enrollment."""

    __tablename__ = "employment_outcomes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    training_enrollment_id = Column(GUID(), ForeignKey("training_enrollments.id"), nullable=True, index=True)

    employment_status = Column(String, nullable=False, default="not_employed")
    # not_employed, placed, employed, self_employed, looking_for_work
    employment_type = Column(String, nullable=True)  # full_time, part_time, contract, internship, freelance
    company_name = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    location = Column(String, nullable=True)
    country = Column(String, nullable=True)
    is_remote = Column(Boolean, nullable=True)

    employment_start_date = Column(Date, nullable=True)
    employment_end_date = Column(Date, nullable=True)

    salary = Column(Float, nullable=True)
    salary_currency = Column(String, nullable=True)
    salary_period = Column(String, nullable=True)  # hourly, monthly, annual

    source = Column(String, nullable=True)  # self_reported, training_provider, verified_employer
    verified = Column(Boolean, nullable=False, default=False)

    # Links this outcome back to a specific opportunity the student was once
    # recommended (from the live JSearch-backed recommendation pipeline in
    # app.services.opportunity_recommendation), when the student reports that
    # a recommendation is what led to this placement. The opportunity itself
    # is never persisted locally — only this reference, supplied by the
    # client from the recommendation it already has in hand — so no extra
    # provider calls are made to record it.
    source_opportunity_id = Column(String, nullable=True)
    source_opportunity_title = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    training_enrollment = relationship("TrainingEnrollment", back_populates="employment_outcomes")
    check_ins = relationship("OutcomeCheckIn", back_populates="employment_outcome", cascade="all, delete-orphan")


class OutcomeCheckIn(Base):
    """Longitudinal follow-up record for an EmploymentOutcome."""

    __tablename__ = "outcome_check_ins"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    employment_outcome_id = Column(GUID(), ForeignKey("employment_outcomes.id"), nullable=False, index=True)

    check_in_date = Column(Date, nullable=False, default=date.today)
    months_since_employment = Column(Integer, nullable=True)
    employment_status = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    salary = Column(Float, nullable=True)
    salary_currency = Column(String, nullable=True)
    salary_period = Column(String, nullable=True)
    training_relevance = Column(String, nullable=True)  # high, medium, low, unknown
    still_employed = Column(Boolean, nullable=True)
    reason_for_leaving = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    employment_outcome = relationship("EmploymentOutcome", back_populates="check_ins")


class OutcomeConsent(Base):
    """Tracks whether a user has consented to employment outcome data collection."""

    __tablename__ = "outcome_consents"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    consented = Column(Boolean, nullable=False, default=False)
    consent_date = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")

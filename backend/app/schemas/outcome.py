from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal
from uuid import UUID
from datetime import date, datetime

TrainingProgramStatus = Literal["planned", "active", "completed", "cancelled"]
EnrollmentStatus = Literal["enrolled", "in_progress", "completed", "dropped", "withdrawn"]
CertificateStatus = Literal["not_issued", "pending", "issued"]
EmploymentStatus = Literal["not_employed", "placed", "employed", "self_employed", "looking_for_work"]
EmploymentType = Literal["full_time", "part_time", "contract", "internship", "freelance"]
SalaryPeriod = Literal["hourly", "monthly", "annual"]
OutcomeSource = Literal["self_reported", "training_provider", "verified_employer"]
TrainingRelevance = Literal["high", "medium", "low", "unknown"]


# ---------------------------------------------------------------------------
# Training Program
# ---------------------------------------------------------------------------

class TrainingProgramCreate(BaseModel):
    name: str = Field(min_length=1)
    provider_name: str = Field(min_length=1)
    description: Optional[str] = None
    skill_names: list[str] = Field(default_factory=list)
    career_domain: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    certification: Optional[str] = None
    status: TrainingProgramStatus = "active"

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self


class TrainingProgramResponse(BaseModel):
    id: UUID
    name: str
    provider_name: str
    description: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    career_domain: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    certification: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Training Enrollment
# ---------------------------------------------------------------------------

class TrainingEnrollmentCreate(BaseModel):
    training_program_id: UUID
    enrollment_date: Optional[date] = None
    status: EnrollmentStatus = "enrolled"

    @field_validator("enrollment_date")
    @classmethod
    def enrollment_date_not_future(cls, v):
        if v and v > date.today():
            raise ValueError("enrollment_date cannot be in the future")
        return v


class TrainingEnrollmentUpdate(BaseModel):
    completion_date: Optional[date] = None
    status: Optional[EnrollmentStatus] = None
    attendance_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    assessment_score: Optional[float] = Field(default=None, ge=0, le=100)
    certificate_status: Optional[CertificateStatus] = None


class TrainingEnrollmentResponse(BaseModel):
    id: UUID
    user_id: UUID
    training_program_id: UUID
    enrollment_date: date
    completion_date: Optional[date] = None
    status: str
    attendance_percentage: Optional[float] = None
    assessment_score: Optional[float] = None
    certificate_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Employment Outcome
# ---------------------------------------------------------------------------

class EmploymentOutcomeCreate(BaseModel):
    training_enrollment_id: Optional[UUID] = None
    employment_status: EmploymentStatus = "not_employed"
    employment_type: Optional[EmploymentType] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    is_remote: Optional[bool] = None
    employment_start_date: Optional[date] = None
    employment_end_date: Optional[date] = None
    salary: Optional[float] = Field(default=None, ge=0)
    salary_currency: Optional[str] = None
    salary_period: Optional[SalaryPeriod] = None
    source: OutcomeSource = "self_reported"
    source_opportunity_id: Optional[str] = None
    source_opportunity_title: Optional[str] = None

    @model_validator(mode="after")
    def check_dates(self):
        if (
            self.employment_start_date
            and self.employment_end_date
            and self.employment_end_date < self.employment_start_date
        ):
            raise ValueError("employment_end_date cannot be before employment_start_date")
        return self


class EmploymentOutcomeUpdate(BaseModel):
    employment_status: Optional[EmploymentStatus] = None
    employment_type: Optional[EmploymentType] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    is_remote: Optional[bool] = None
    employment_start_date: Optional[date] = None
    employment_end_date: Optional[date] = None
    salary: Optional[float] = Field(default=None, ge=0)
    salary_currency: Optional[str] = None
    salary_period: Optional[SalaryPeriod] = None


class EmploymentOutcomeResponse(BaseModel):
    id: UUID
    user_id: UUID
    training_enrollment_id: Optional[UUID] = None
    employment_status: str
    employment_type: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    is_remote: Optional[bool] = None
    employment_start_date: Optional[date] = None
    employment_end_date: Optional[date] = None
    salary: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_period: Optional[str] = None
    source: Optional[str] = None
    source_opportunity_id: Optional[str] = None
    source_opportunity_title: Optional[str] = None
    verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Outcome Check-in
# ---------------------------------------------------------------------------

class OutcomeCheckInCreate(BaseModel):
    employment_outcome_id: UUID
    check_in_date: Optional[date] = None
    months_since_employment: Optional[int] = Field(default=None, ge=0)
    employment_status: EmploymentStatus
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    salary: Optional[float] = Field(default=None, ge=0)
    salary_currency: Optional[str] = None
    salary_period: Optional[SalaryPeriod] = None
    training_relevance: TrainingRelevance = "unknown"
    still_employed: Optional[bool] = None
    reason_for_leaving: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("check_in_date")
    @classmethod
    def check_in_date_not_future(cls, v):
        if v and v > date.today():
            raise ValueError("check_in_date cannot be in the future")
        return v


class OutcomeCheckInResponse(BaseModel):
    id: UUID
    employment_outcome_id: UUID
    check_in_date: date
    months_since_employment: Optional[int] = None
    employment_status: str
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    salary: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_period: Optional[str] = None
    training_relevance: Optional[str] = None
    still_employed: Optional[bool] = None
    reason_for_leaving: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Outcome Consent
# ---------------------------------------------------------------------------

class OutcomeConsentUpdate(BaseModel):
    consented: bool


class OutcomeConsentResponse(BaseModel):
    user_id: UUID
    consented: bool
    consent_date: Optional[datetime] = None
    revoked_at: Optional[datetime] = None

    class Config:
        from_attributes = True

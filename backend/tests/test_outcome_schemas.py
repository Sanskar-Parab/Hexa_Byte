import pytest
from datetime import date, timedelta
from uuid import uuid4
from pydantic import ValidationError

from app.schemas.outcome import (
    TrainingProgramCreate,
    TrainingEnrollmentCreate,
    EmploymentOutcomeCreate,
    OutcomeCheckInCreate,
)


class TestTrainingProgramValidation:
    def test_valid_minimal_program(self):
        p = TrainingProgramCreate(name="X", provider_name="Y")
        assert p.status == "active"
        assert p.skill_names == []

    def test_end_before_start_rejected(self):
        with pytest.raises(ValidationError):
            TrainingProgramCreate(
                name="X",
                provider_name="Y",
                start_date=date.today(),
                end_date=date.today() - timedelta(days=1),
            )

    def test_missing_name_rejected(self):
        with pytest.raises(ValidationError):
            TrainingProgramCreate(name="", provider_name="Y")

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            TrainingProgramCreate(name="X", provider_name="Y", status="bogus")


class TestEnrollmentValidation:
    def test_future_enrollment_date_rejected(self):
        with pytest.raises(ValidationError):
            TrainingEnrollmentCreate(
                training_program_id=uuid4(),
                enrollment_date=date.today() + timedelta(days=5),
            )

    def test_default_status_enrolled(self):
        e = TrainingEnrollmentCreate(training_program_id=uuid4())
        assert e.status == "enrolled"

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            TrainingEnrollmentCreate(training_program_id=uuid4(), status="bogus")

    def test_missing_training_program_id_rejected(self):
        with pytest.raises(ValidationError):
            TrainingEnrollmentCreate()


class TestEmploymentOutcomeValidation:
    def test_negative_salary_rejected(self):
        with pytest.raises(ValidationError):
            EmploymentOutcomeCreate(salary=-100)

    def test_end_before_start_rejected(self):
        with pytest.raises(ValidationError):
            EmploymentOutcomeCreate(
                employment_start_date=date.today(),
                employment_end_date=date.today() - timedelta(days=10),
            )

    def test_minimal_data_allowed(self):
        """Students may have incomplete outcome data."""
        o = EmploymentOutcomeCreate()
        assert o.employment_status == "not_employed"
        assert o.company_name is None

    def test_invalid_employment_status_rejected(self):
        with pytest.raises(ValidationError):
            EmploymentOutcomeCreate(employment_status="bogus")

    def test_invalid_employment_type_rejected(self):
        with pytest.raises(ValidationError):
            EmploymentOutcomeCreate(employment_type="bogus")

    def test_zero_salary_allowed(self):
        o = EmploymentOutcomeCreate(salary=0)
        assert o.salary == 0


class TestCheckInValidation:
    def test_negative_salary_rejected(self):
        with pytest.raises(ValidationError):
            OutcomeCheckInCreate(employment_outcome_id=uuid4(), employment_status="employed", salary=-1)

    def test_future_check_in_date_rejected(self):
        with pytest.raises(ValidationError):
            OutcomeCheckInCreate(
                employment_outcome_id=uuid4(),
                employment_status="employed",
                check_in_date=date.today() + timedelta(days=1),
            )

    def test_negative_months_rejected(self):
        with pytest.raises(ValidationError):
            OutcomeCheckInCreate(
                employment_outcome_id=uuid4(),
                employment_status="employed",
                months_since_employment=-1,
            )

    def test_default_training_relevance_unknown(self):
        c = OutcomeCheckInCreate(employment_outcome_id=uuid4(), employment_status="employed")
        assert c.training_relevance == "unknown"

    def test_missing_employment_outcome_id_rejected(self):
        with pytest.raises(ValidationError):
            OutcomeCheckInCreate(employment_status="employed")

    def test_missing_employment_status_rejected(self):
        with pytest.raises(ValidationError):
            OutcomeCheckInCreate(employment_outcome_id=uuid4())

import pytest
from datetime import date
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.config import Base
from app.models.user import User
from app.models.skill import Skill
from app.services import outcome_service, outcome_timeline
from app.services.outcome_timeline import _add_months, build_outcome_timeline
from app.schemas.outcome import (
    TrainingProgramCreate,
    TrainingEnrollmentCreate,
    EmploymentOutcomeCreate,
    OutcomeCheckInCreate,
)


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    yield session
    session.close()


def _make_user(db, email="a@test.com"):
    user = User(email=email, name="Test", password_hash="x")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_program(db, skills=None):
    return outcome_service.create_training_program(
        db,
        TrainingProgramCreate(
            name="Full Stack Web Development", provider_name="Acme Skilling",
            skill_names=skills or [],
        ),
    )


def _make_enrollment(db, user, program):
    return outcome_service.create_enrollment(
        db, user.id, TrainingEnrollmentCreate(training_program_id=program.id, status="completed")
    )


def _make_outcome(db, user, enrollment=None, **overrides):
    data = dict(employment_status="employed", job_title="Frontend Developer")
    data.update(overrides)
    outcome = outcome_service.create_employment_outcome(db, user.id, EmploymentOutcomeCreate(**data))
    if enrollment:
        outcome.training_enrollment_id = enrollment.id
        db.commit()
        db.refresh(outcome)
    return outcome


def _make_check_in(db, outcome, **overrides):
    data = dict(employment_outcome_id=outcome.id, employment_status="employed")
    data.update(overrides)
    return outcome_service.create_check_in(db, outcome, OutcomeCheckInCreate(**data))


# ---------------------------------------------------------------------------
# _add_months helper (pure function correctness — everything else depends on it)
# ---------------------------------------------------------------------------

class TestAddMonths:
    def test_simple_forward(self):
        assert _add_months(date(2026, 1, 15), 3) == date(2026, 4, 15)

    def test_rolls_over_year(self):
        assert _add_months(date(2026, 11, 1), 3) == date(2027, 2, 1)

    def test_clamps_day_for_shorter_month(self):
        # Jan 31 + 1 month -> Feb 2026 has 28 days
        assert _add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)

    def test_negative_months_goes_backward(self):
        assert _add_months(date(2026, 1, 15), -6) == date(2025, 7, 15)


# ---------------------------------------------------------------------------
# Retention
# ---------------------------------------------------------------------------

class TestRetention:
    def test_pending_when_milestone_not_reached(self, db):
        user = _make_user(db)
        outcome = _make_outcome(
            db, user, employment_start_date=_add_months(date.today(), -1),
        )
        result = build_outcome_timeline(db, user.id)
        assert result["retention"]["3_month"] == "pending"
        assert result["milestones"]["3_month"]["reached"] is False

    def test_yes_with_check_in_confirming_employment(self, db):
        user = _make_user(db)
        start = _add_months(date.today(), -4)
        outcome = _make_outcome(db, user, employment_start_date=start)
        _make_check_in(
            db, outcome,
            check_in_date=_add_months(start, 3),
            employment_status="employed",
            still_employed=True,
        )
        result = build_outcome_timeline(db, user.id)
        assert result["retention"]["3_month"] == "yes"

    def test_no_with_check_in_confirming_departure(self, db):
        user = _make_user(db)
        start = _add_months(date.today(), -4)
        outcome = _make_outcome(db, user, employment_start_date=start)
        _make_check_in(
            db, outcome,
            check_in_date=_add_months(start, 3),
            employment_status="looking_for_work",
            still_employed=False,
        )
        result = build_outcome_timeline(db, user.id)
        assert result["retention"]["3_month"] == "no"

    def test_no_due_to_employment_end_before_milestone(self, db):
        user = _make_user(db)
        start = _add_months(date.today(), -4)
        outcome = _make_outcome(
            db, user, employment_start_date=start,
            employment_end_date=_add_months(start, 1),
        )
        result = build_outcome_timeline(db, user.id)
        assert result["retention"]["3_month"] == "no"

    def test_unknown_when_milestone_reached_but_no_check_in_data(self, db):
        """Never fabricate — a reached milestone with zero recorded data is 'unknown', not 'yes'."""
        user = _make_user(db)
        start = _add_months(date.today(), -4)
        _make_outcome(db, user, employment_start_date=start)
        result = build_outcome_timeline(db, user.id)
        assert result["retention"]["3_month"] == "unknown"

    def test_still_employed_inferred_from_status_when_field_absent(self, db):
        """A check-in that doesn't set still_employed explicitly falls back to employment_status."""
        user = _make_user(db)
        start = _add_months(date.today(), -4)
        outcome = _make_outcome(db, user, employment_start_date=start)
        _make_check_in(db, outcome, check_in_date=_add_months(start, 3), employment_status="self_employed")
        result = build_outcome_timeline(db, user.id)
        assert result["retention"]["3_month"] == "yes"


# ---------------------------------------------------------------------------
# Salary progression
# ---------------------------------------------------------------------------

class TestSalaryProgression:
    def test_progression_with_full_data(self, db):
        user = _make_user(db)
        start = _add_months(date.today(), -13)
        outcome = _make_outcome(
            db, user, employment_start_date=start, salary=300000, salary_currency="INR", salary_period="annual",
        )
        _make_check_in(
            db, outcome, check_in_date=_add_months(start, 6), employment_status="employed",
            salary=360000, salary_currency="INR", salary_period="annual",
        )
        _make_check_in(
            db, outcome, check_in_date=_add_months(start, 12), employment_status="employed",
            salary=420000, salary_currency="INR", salary_period="annual",
        )

        result = build_outcome_timeline(db, user.id)
        progression = result["salary_progression"]

        assert progression["initial"]["amount"] == 300000
        assert progression["at_6_months"]["amount"] == 360000
        assert progression["at_12_months"]["amount"] == 420000

        # initial -> 6mo: +60000, 20% (spec's worked example)
        first_change = progression["changes"][0]
        assert first_change["absolute_change"] == 60000
        assert first_change["percentage_change"] == 20.0

        # 6mo -> 12mo: +60000, 16.67%
        second_change = progression["changes"][1]
        assert second_change["absolute_change"] == 60000
        assert round(second_change["percentage_change"], 1) == 16.7

    def test_missing_salary_handled_safely(self, db):
        """Never invent salary — a check-in with no salary yields no snapshot, no crash."""
        user = _make_user(db)
        start = _add_months(date.today(), -13)
        outcome = _make_outcome(db, user, employment_start_date=start, salary=300000)
        _make_check_in(db, outcome, check_in_date=_add_months(start, 6), employment_status="employed")  # no salary

        result = build_outcome_timeline(db, user.id)
        progression = result["salary_progression"]
        assert progression["initial"]["amount"] == 300000
        assert progression["at_6_months"] is None
        # no change entries can be computed across a missing point
        assert progression["changes"] == []

    def test_no_initial_salary_at_all(self, db):
        user = _make_user(db)
        start = _add_months(date.today(), -4)
        _make_outcome(db, user, employment_start_date=start)  # salary never provided
        result = build_outcome_timeline(db, user.id)
        assert result["salary_progression"]["initial"] is None

    def test_zero_initial_salary_avoids_division_by_zero(self, db):
        user = _make_user(db)
        start = _add_months(date.today(), -13)
        outcome = _make_outcome(db, user, employment_start_date=start, salary=0)
        _make_check_in(db, outcome, check_in_date=_add_months(start, 6), employment_status="employed", salary=50000)

        result = build_outcome_timeline(db, user.id)
        change = result["salary_progression"]["changes"][0]
        assert change["absolute_change"] == 50000
        assert change["percentage_change"] is None  # can't compute a % change off a zero baseline


# ---------------------------------------------------------------------------
# Employment end / self-employment
# ---------------------------------------------------------------------------

class TestEmploymentEndAndSelfEmployment:
    def test_employment_end_and_reason_surfaced(self, db):
        user = _make_user(db)
        start = _add_months(date.today(), -4)
        outcome = _make_outcome(db, user, employment_start_date=start)
        _make_check_in(
            db, outcome, check_in_date=_add_months(start, 3),
            employment_status="looking_for_work", still_employed=False,
            reason_for_leaving="Contract ended",
        )
        result = build_outcome_timeline(db, user.id)
        assert result["check_ins"][0]["reason_for_leaving"] == "Contract ended"
        assert result["check_ins"][0]["still_employed"] is False

    def test_reason_for_leaving_stays_optional(self, db):
        """Must never force disclosure of a sensitive reason for leaving."""
        user = _make_user(db)
        start = _add_months(date.today(), -4)
        outcome = _make_outcome(db, user, employment_start_date=start)
        _make_check_in(
            db, outcome, check_in_date=_add_months(start, 3),
            employment_status="looking_for_work", still_employed=False,
        )
        result = build_outcome_timeline(db, user.id)
        assert result["check_ins"][0]["reason_for_leaving"] is None

    def test_self_employment_tracked(self, db):
        user = _make_user(db)
        outcome = _make_outcome(
            db, user, employment_status="self_employed", employment_type="freelance",
            company_name="Own Business", job_title=None,
        )
        result = build_outcome_timeline(db, user.id)
        assert result["placement"]["employment_status"] == "self_employed"
        assert result["employment"]["employment_type"] == "freelance"


# ---------------------------------------------------------------------------
# Timeline shape / no fake data
# ---------------------------------------------------------------------------

class TestTimelineShape:
    def test_empty_user_gets_empty_shell_not_fake_data(self, db):
        user = _make_user(db)
        result = build_outcome_timeline(db, user.id)
        assert result["training"] is None
        assert result["placement"] is None
        assert result["employment"] is None
        assert result["check_ins"] == []
        assert all(v == "not_applicable" for v in result["retention"].values())
        assert all(v is None for v in result["milestones"].values())
        assert result["salary_progression"]["initial"] is None
        assert result["training_relevance_over_time"] == []

    def test_full_timeline_includes_training_and_placement(self, db):
        db.add(Skill(name="JavaScript", category="Programming"))
        db.add(Skill(name="React", category="Programming"))
        db.commit()
        user = _make_user(db)
        program = _make_program(db, skills=["JavaScript", "React"])
        enrollment = _make_enrollment(db, user, program)
        outcome = _make_outcome(
            db, user, enrollment=enrollment,
            employment_start_date=_add_months(date.today(), -2),
            job_title="Frontend Developer",
        )

        result = build_outcome_timeline(db, user.id)
        assert result["training"]["training_program_id"] == str(program.id)
        assert result["placement"]["employment_outcome_id"] == str(outcome.id)
        assert result["employment"]["job_title"] == "Frontend Developer"
        # placement-time relevance was computed (job_title + training skills both present)
        assert result["training_relevance_over_time"][0]["job_title"] == "Frontend Developer"

    def test_defaults_to_most_recent_enrollment(self, db):
        user = _make_user(db)
        program = _make_program(db)
        _make_enrollment(db, user, program)
        result = build_outcome_timeline(db, user.id)
        assert result["training"]["training_program_id"] == str(program.id)

    def test_unowned_enrollment_id_returns_none(self, db):
        user_a = _make_user(db, "a@test.com")
        user_b = _make_user(db, "b@test.com")
        program = _make_program(db)
        enrollment = _make_enrollment(db, user_a, program)

        assert build_outcome_timeline(db, user_b.id, training_enrollment_id=enrollment.id) is None


# ---------------------------------------------------------------------------
# Partial check-ins
# ---------------------------------------------------------------------------

class TestPartialCheckIns:
    def test_check_in_without_job_title_skips_relevance_entry(self, db):
        db.add(Skill(name="JavaScript", category="Programming"))
        db.commit()
        user = _make_user(db)
        program = _make_program(db, skills=["JavaScript"])
        enrollment = _make_enrollment(db, user, program)
        start = _add_months(date.today(), -4)
        outcome = _make_outcome(db, user, enrollment=enrollment, employment_start_date=start, job_title=None)
        _make_check_in(db, outcome, check_in_date=_add_months(start, 3), employment_status="employed", job_title=None)

        result = build_outcome_timeline(db, user.id)
        # no job_title anywhere -> no relevance entries fabricated
        assert result["training_relevance_over_time"] == []

    def test_check_in_without_salary_or_status_details(self, db):
        """A minimal check-in (only the required fields) must not crash the timeline build."""
        user = _make_user(db)
        start = _add_months(date.today(), -4)
        outcome = _make_outcome(db, user, employment_start_date=start)
        _make_check_in(db, outcome, check_in_date=_add_months(start, 3), employment_status="employed")

        result = build_outcome_timeline(db, user.id)
        assert result["check_ins"][0]["salary"] is None
        assert result["check_ins"][0]["company_name"] is None
        assert result["milestones"]["3_month"]["retention"] == "yes"  # inferred from employment_status

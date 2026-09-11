"""Tests for unreachable/declined statuses, outreach_result, and consent coverage."""
import pytest
from uuid import uuid4
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.config import Base
from app.models.user import User
from app.services import outcome_service, admin_analytics
from app.services.admin_analytics import AnalyticsFilters
from app.schemas.outcome import EmploymentOutcomeCreate, OutcomeCheckInCreate


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    yield session
    session.close()


def _make_user(db, email):
    user = User(email=email, name="Trainee", password_hash="x")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_program(db):
    from app.schemas.outcome import TrainingProgramCreate
    return outcome_service.create_training_program(
        db, TrainingProgramCreate(name="Full Stack Web Development", provider_name="Provider A")
    )


def _enroll(db, user, program, status="enrolled"):
    from app.schemas.outcome import TrainingEnrollmentCreate, TrainingEnrollmentUpdate
    enrollment = outcome_service.create_enrollment(
        db, user.id, TrainingEnrollmentCreate(training_program_id=program.id)
    )
    if status != "enrolled":
        outcome_service.update_enrollment(db, enrollment, TrainingEnrollmentUpdate(status=status))
    return enrollment


class TestNewEmploymentStatuses:
    def test_outcome_accepts_unreachable(self):
        o = EmploymentOutcomeCreate(employment_status="unreachable")
        assert o.employment_status == "unreachable"

    def test_outcome_accepts_declined_to_respond(self):
        o = EmploymentOutcomeCreate(employment_status="declined_to_respond")
        assert o.employment_status == "declined_to_respond"

    def test_check_in_accepts_new_statuses(self):
        for status in ("unreachable", "declined_to_respond"):
            c = OutcomeCheckInCreate(employment_outcome_id=uuid4(), employment_status=status)
            assert c.employment_status == status

    def test_existing_statuses_still_valid(self):
        for status in ("not_employed", "placed", "employed", "self_employed", "looking_for_work"):
            o = EmploymentOutcomeCreate(employment_status=status)
            assert o.employment_status == status


class TestOutreachResult:
    def test_defaults_to_none(self):
        c = OutcomeCheckInCreate(employment_outcome_id=uuid4(), employment_status="employed")
        assert c.outreach_result is None

    def test_accepts_valid_values(self):
        for value in ("responded", "attempted_no_response", "not_attempted"):
            c = OutcomeCheckInCreate(
                employment_outcome_id=uuid4(), employment_status="employed", outreach_result=value
            )
            assert c.outreach_result == value

    def test_rejects_invalid_value(self):
        with pytest.raises(ValidationError):
            OutcomeCheckInCreate(
                employment_outcome_id=uuid4(), employment_status="employed", outreach_result="bogus"
            )

    def test_create_check_in_persists_outreach_result(self, db):
        user = _make_user(db, "outreach@test.com")
        outcome = outcome_service.create_employment_outcome(
            db, user.id, EmploymentOutcomeCreate(employment_status="employed")
        )
        check_in = outcome_service.create_check_in(
            db, outcome,
            OutcomeCheckInCreate(
                employment_outcome_id=outcome.id,
                employment_status="employed",
                outreach_result="attempted_no_response",
            ),
        )
        assert check_in.outreach_result == "attempted_no_response"
        fetched = outcome_service.list_check_ins(db, user.id)
        assert fetched[0].outreach_result == "attempted_no_response"


class TestUnreachableDeclinedAnalytics:
    def test_overview_shows_distinct_rates(self, db):
        program = _make_program(db)
        # 5 trainees: 1 employed, 1 not_employed, 1 unreachable, 1 declined, 1 no outcome
        statuses = ["employed", "not_employed", "unreachable", "declined_to_respond", None]
        for i, status in enumerate(statuses):
            user = _make_user(db, f"cat{i}@test.com")
            enrollment = _enroll(db, user, program, status="completed")
            if status is not None:
                outcome = outcome_service.create_employment_outcome(
                    db, user.id, EmploymentOutcomeCreate(employment_status=status)
                )
                outcome.training_enrollment_id = enrollment.id
                db.commit()

        result = admin_analytics.get_overview_metrics(db, AnalyticsFilters())
        assert result["trainee_count"] == 5
        assert result["placement_rate"] == 20.0  # 1/5 employed
        assert result["unemployment_rate"] == 20.0  # only not_employed, not the new statuses
        assert result["unreachable_rate"] == 20.0
        assert result["declined_to_respond_rate"] == 20.0
        assert result["non_placement_rate"] == 80.0  # 4/5 not placed

    def test_non_placement_shows_distinct_categories(self, db):
        program = _make_program(db)
        user1 = _make_user(db, "unreach@test.com")
        enrollment1 = _enroll(db, user1, program, status="completed")
        outcome1 = outcome_service.create_employment_outcome(
            db, user1.id, EmploymentOutcomeCreate(employment_status="unreachable")
        )
        outcome1.training_enrollment_id = enrollment1.id
        db.commit()

        user2 = _make_user(db, "declined@test.com")
        enrollment2 = _enroll(db, user2, program, status="completed")
        outcome2 = outcome_service.create_employment_outcome(
            db, user2.id, EmploymentOutcomeCreate(employment_status="declined_to_respond")
        )
        outcome2.training_enrollment_id = enrollment2.id
        db.commit()

        result = admin_analytics.get_non_placement_analytics(db, AnalyticsFilters())
        categories = {r["category"] for r in result}
        assert "unreachable" in categories
        assert "declined_to_respond" in categories
        by_cat = {r["category"]: r for r in result}
        assert by_cat["unreachable"]["trainee_count"] == 1
        assert by_cat["declined_to_respond"]["trainee_count"] == 1

    def test_filter_options_include_new_statuses(self, db):
        options = admin_analytics.get_filter_options(db)
        assert "unreachable" in options["employment_statuses"]
        assert "declined_to_respond" in options["employment_statuses"]
        # existing values unchanged
        assert "not_employed" in options["employment_statuses"]


class TestConsentCoverage:
    def test_consent_coverage_pct(self, db):
        program = _make_program(db)
        users = [_make_user(db, f"consent{i}@test.com") for i in range(5)]
        for user in users:
            _enroll(db, user, program, status="completed")
        # 3 active consents, 1 revoked, 1 no record
        outcome_service.set_consent(db, users[0].id, True)
        outcome_service.set_consent(db, users[1].id, True)
        outcome_service.set_consent(db, users[2].id, True)
        outcome_service.set_consent(db, users[3].id, True)
        outcome_service.set_consent(db, users[3].id, False)  # revoke

        result = admin_analytics.get_overview_metrics(db, AnalyticsFilters())
        assert result["trainee_count"] == 5
        assert result["consent_coverage_pct"] == 60.0  # 3/5

    def test_consent_coverage_suppressed_below_threshold(self, db):
        program = _make_program(db)
        for i in range(3):  # below MIN_COHORT_SIZE(5)
            user = _make_user(db, f"smallconsent{i}@test.com")
            _enroll(db, user, program, status="completed")
            outcome_service.set_consent(db, user.id, True)

        result = admin_analytics.get_overview_metrics(db, AnalyticsFilters())
        assert result["trainee_count"] == 3
        assert result["sample_size_sufficient"] is False
        assert result["consent_coverage_pct"] is None

    def test_consent_coverage_none_when_no_data(self, db):
        result = admin_analytics.get_overview_metrics(db, AnalyticsFilters())
        assert result["consent_coverage_pct"] is None

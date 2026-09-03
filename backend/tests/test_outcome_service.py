import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.config import Base
from app.models.user import User
from app.services import outcome_service
from app.schemas.outcome import (
    TrainingProgramCreate,
    TrainingEnrollmentCreate,
    TrainingEnrollmentUpdate,
    EmploymentOutcomeCreate,
    OutcomeCheckInCreate,
)


@pytest.fixture()
def db():
    """Real in-memory SQLite session so ownership-filtering queries are actually exercised."""
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


def _make_program(db):
    return outcome_service.create_training_program(
        db, TrainingProgramCreate(name="Full Stack Bootcamp", provider_name="Acme Skilling")
    )


class TestConsent:
    def test_no_consent_by_default(self, db):
        user = _make_user(db)
        assert outcome_service.has_active_consent(db, user.id) is False

    def test_set_consent_true(self, db):
        user = _make_user(db)
        consent = outcome_service.set_consent(db, user.id, True)
        assert consent.consented is True
        assert consent.consent_date is not None
        assert outcome_service.has_active_consent(db, user.id) is True

    def test_revoke_consent(self, db):
        user = _make_user(db)
        outcome_service.set_consent(db, user.id, True)
        consent = outcome_service.set_consent(db, user.id, False)
        assert consent.consented is False
        assert consent.revoked_at is not None
        assert outcome_service.has_active_consent(db, user.id) is False

    def test_reconsent_clears_revocation(self, db):
        user = _make_user(db)
        outcome_service.set_consent(db, user.id, True)
        outcome_service.set_consent(db, user.id, False)
        consent = outcome_service.set_consent(db, user.id, True)
        assert consent.consented is True
        assert consent.revoked_at is None


class TestTrainingProgram:
    def test_create_and_list(self, db):
        program = _make_program(db)
        programs = outcome_service.list_training_programs(db)
        assert len(programs) == 1
        assert programs[0].id == program.id

    def test_filters_by_domain(self, db):
        outcome_service.create_training_program(
            db, TrainingProgramCreate(name="Data Science", provider_name="Acme", career_domain="data")
        )
        outcome_service.create_training_program(
            db, TrainingProgramCreate(name="Cloud", provider_name="Acme", career_domain="cloud")
        )
        results = outcome_service.list_training_programs(db, career_domain="data")
        assert len(results) == 1
        assert results[0].name == "Data Science"

    def test_skill_names_linked_when_known(self, db):
        from app.models.skill import Skill
        db.add(Skill(name="Python", category="Programming"))
        db.commit()

        program = outcome_service.create_training_program(
            db, TrainingProgramCreate(name="X", provider_name="Y", skill_names=["Python", "Unknown Skill"])
        )
        names = outcome_service.training_program_skill_names(db, program)
        assert names == ["Python"]


class TestEnrollmentOwnership:
    def test_get_enrollment_scoped_to_owner(self, db):
        user_a = _make_user(db, "a@test.com")
        user_b = _make_user(db, "b@test.com")
        program = _make_program(db)

        enrollment = outcome_service.create_enrollment(
            db, user_a.id, TrainingEnrollmentCreate(training_program_id=program.id)
        )

        assert outcome_service.get_enrollment(db, user_a.id, enrollment.id) is not None
        assert outcome_service.get_enrollment(db, user_b.id, enrollment.id) is None

    def test_list_enrollments_only_returns_own(self, db):
        user_a = _make_user(db, "a@test.com")
        user_b = _make_user(db, "b@test.com")
        program = _make_program(db)

        outcome_service.create_enrollment(db, user_a.id, TrainingEnrollmentCreate(training_program_id=program.id))
        outcome_service.create_enrollment(db, user_b.id, TrainingEnrollmentCreate(training_program_id=program.id))

        a_enrollments = outcome_service.list_enrollments(db, user_a.id)
        assert len(a_enrollments) == 1
        assert a_enrollments[0].user_id == user_a.id

    def test_update_enrollment_to_completed(self, db):
        user = _make_user(db)
        program = _make_program(db)
        enrollment = outcome_service.create_enrollment(
            db, user.id, TrainingEnrollmentCreate(training_program_id=program.id)
        )
        updated = outcome_service.update_enrollment(
            db,
            enrollment,
            TrainingEnrollmentUpdate(
                status="completed",
                attendance_percentage=92.5,
                assessment_score=88.0,
                certificate_status="issued",
            ),
        )
        assert updated.status == "completed"
        assert updated.attendance_percentage == 92.5
        assert updated.certificate_status == "issued"

    def test_dropped_enrollment(self, db):
        user = _make_user(db)
        program = _make_program(db)
        enrollment = outcome_service.create_enrollment(
            db, user.id, TrainingEnrollmentCreate(training_program_id=program.id)
        )
        updated = outcome_service.update_enrollment(db, enrollment, TrainingEnrollmentUpdate(status="dropped"))
        assert updated.status == "dropped"


class TestEmploymentOutcomeOwnership:
    def test_get_outcome_scoped_to_owner(self, db):
        user_a = _make_user(db, "a@test.com")
        user_b = _make_user(db, "b@test.com")

        outcome = outcome_service.create_employment_outcome(
            db, user_a.id, EmploymentOutcomeCreate(employment_status="placed")
        )

        assert outcome_service.get_employment_outcome(db, user_a.id, outcome.id) is not None
        assert outcome_service.get_employment_outcome(db, user_b.id, outcome.id) is None

    def test_list_outcomes_only_returns_own(self, db):
        user_a = _make_user(db, "a@test.com")
        user_b = _make_user(db, "b@test.com")
        outcome_service.create_employment_outcome(db, user_a.id, EmploymentOutcomeCreate(employment_status="employed"))
        outcome_service.create_employment_outcome(db, user_b.id, EmploymentOutcomeCreate(employment_status="employed"))

        assert len(outcome_service.list_employment_outcomes(db, user_a.id)) == 1

    def test_self_employed_outcome(self, db):
        user = _make_user(db)
        outcome = outcome_service.create_employment_outcome(
            db,
            user.id,
            EmploymentOutcomeCreate(
                employment_status="self_employed",
                employment_type="freelance",
                company_name="Own Business",
            ),
        )
        assert outcome.employment_status == "self_employed"
        assert outcome.employment_type == "freelance"
        assert outcome.verified is False

    def test_incomplete_outcome_data_allowed(self, db):
        """Students may have incomplete outcome data — only user_id is required."""
        user = _make_user(db)
        outcome = outcome_service.create_employment_outcome(db, user.id, EmploymentOutcomeCreate())
        assert outcome.employment_status == "not_employed"
        assert outcome.company_name is None
        assert outcome.salary is None


class TestCheckInOwnership:
    def test_check_ins_scoped_through_outcome(self, db):
        user_a = _make_user(db, "a@test.com")
        user_b = _make_user(db, "b@test.com")

        outcome_a = outcome_service.create_employment_outcome(
            db, user_a.id, EmploymentOutcomeCreate(employment_status="employed")
        )
        outcome_service.create_check_in(
            db,
            outcome_a,
            OutcomeCheckInCreate(
                employment_outcome_id=outcome_a.id,
                employment_status="employed",
                months_since_employment=3,
                training_relevance="high",
            ),
        )

        assert len(outcome_service.list_check_ins(db, user_a.id)) == 1
        assert len(outcome_service.list_check_ins(db, user_b.id)) == 0

    def test_check_in_records_leaving_reason(self, db):
        user = _make_user(db)
        outcome = outcome_service.create_employment_outcome(
            db, user.id, EmploymentOutcomeCreate(employment_status="employed")
        )
        check_in = outcome_service.create_check_in(
            db,
            outcome,
            OutcomeCheckInCreate(
                employment_outcome_id=outcome.id,
                employment_status="looking_for_work",
                still_employed=False,
                reason_for_leaving="Contract ended",
            ),
        )
        assert check_in.still_employed is False
        assert check_in.reason_for_leaving == "Contract ended"

    def test_filter_check_ins_by_outcome(self, db):
        user = _make_user(db)
        outcome_1 = outcome_service.create_employment_outcome(
            db, user.id, EmploymentOutcomeCreate(employment_status="employed")
        )
        outcome_2 = outcome_service.create_employment_outcome(
            db, user.id, EmploymentOutcomeCreate(employment_status="employed")
        )
        outcome_service.create_check_in(
            db, outcome_1, OutcomeCheckInCreate(employment_outcome_id=outcome_1.id, employment_status="employed")
        )
        outcome_service.create_check_in(
            db, outcome_2, OutcomeCheckInCreate(employment_outcome_id=outcome_2.id, employment_status="employed")
        )

        filtered = outcome_service.list_check_ins(db, user.id, employment_outcome_id=outcome_1.id)
        assert len(filtered) == 1
        assert filtered[0].employment_outcome_id == outcome_1.id

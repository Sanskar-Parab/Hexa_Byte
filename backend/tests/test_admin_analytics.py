import pytest
from datetime import date
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.config import Base
from app.models.user import User
from app.models.skill import Skill, UserSkill
from app.services import outcome_service, admin_analytics
from app.services.admin_analytics import AnalyticsFilters
from app.services.outcome_timeline import _add_months
from app.schemas.outcome import (
    TrainingProgramCreate,
    TrainingEnrollmentCreate,
    TrainingEnrollmentUpdate,
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


def _make_user(db, email):
    user = User(email=email, name="Trainee", password_hash="x")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_program(db, provider_name="Provider A", **overrides):
    data = dict(name="Full Stack Web Development", provider_name=provider_name)
    data.update(overrides)
    return outcome_service.create_training_program(db, TrainingProgramCreate(**data))


def _enroll(db, user, program, status="enrolled"):
    enrollment = outcome_service.create_enrollment(
        db, user.id, TrainingEnrollmentCreate(training_program_id=program.id)
    )
    if status != "enrolled":
        outcome_service.update_enrollment(db, enrollment, TrainingEnrollmentUpdate(status=status))
    return enrollment


class TestSection9WorkedExample:
    """100 trainees, 80 completed, 50 placed, 40 employed, 32 retained at 6 months."""

    def test_exact_percentages(self, db):
        program = _make_program(db)
        eight_months_ago = _add_months(date.today(), -8)

        trainees = []
        for i in range(100):
            user = _make_user(db, f"trainee{i}@test.com")
            status = "completed" if i < 80 else "enrolled"
            enrollment = _enroll(db, user, program, status=status)
            trainees.append((user, enrollment))

        # 40 traditionally employed, all started 8 months ago (past the 6-month mark)
        for i in range(40):
            user, enrollment = trainees[i]
            outcome = outcome_service.create_employment_outcome(
                db, user.id,
                EmploymentOutcomeCreate(
                    employment_status="employed",
                    employment_start_date=eight_months_ago,
                    job_title=None,
                ),
            )
            outcome.training_enrollment_id = enrollment.id
            db.commit()
            db.refresh(outcome)

            still_employed = i < 32  # first 32 retained, last 8 not
            outcome_service.create_check_in(
                db, outcome,
                OutcomeCheckInCreate(
                    employment_outcome_id=outcome.id,
                    check_in_date=_add_months(eight_months_ago, 6),
                    employment_status="employed" if still_employed else "looking_for_work",
                    still_employed=still_employed,
                ),
            )

        # 10 more placed via self-employment (no employment_start_date -> excluded from retention calc)
        for i in range(40, 50):
            user, enrollment = trainees[i]
            outcome = outcome_service.create_employment_outcome(
                db, user.id, EmploymentOutcomeCreate(employment_status="self_employed"),
            )
            outcome.training_enrollment_id = enrollment.id
            db.commit()

        # remaining 50 trainees: no employment outcome recorded at all

        result = admin_analytics.get_overview_metrics(db, AnalyticsFilters())

        assert result["trainee_count"] == 100
        assert result["sample_size_sufficient"] is True
        assert result["training_completion_rate"] == 80.0
        assert result["placement_rate"] == 50.0
        assert result["employment_rate"] == 40.0
        assert result["self_employment_rate"] == 10.0
        assert result["non_placement_rate"] == 50.0
        assert result["retention_6_month_rate"] == 80.0  # 32/40


class TestOverviewMetrics:
    def test_no_data_returns_none_not_zero(self, db):
        """An empty system must report 'no data', never a fabricated 0%."""
        result = admin_analytics.get_overview_metrics(db, AnalyticsFilters())
        assert result["trainee_count"] == 0
        assert result["placement_rate"] is None
        assert result["average_starting_salary"] is None

    def test_wage_growth_computed_from_paired_data_only(self, db):
        program = _make_program(db)
        start = _add_months(date.today(), -13)
        # Need MIN_COHORT_SIZE (5) trainees for rates to not be suppressed.
        for i in range(5):
            user = _make_user(db, f"wage{i}@test.com")
            enrollment = _enroll(db, user, program, status="completed")
            outcome = outcome_service.create_employment_outcome(
                db, user.id,
                EmploymentOutcomeCreate(
                    employment_status="employed", employment_start_date=start,
                    salary=300000, salary_currency="INR", salary_period="annual",
                ),
            )
            outcome.training_enrollment_id = enrollment.id
            db.commit()
            db.refresh(outcome)
            outcome_service.create_check_in(
                db, outcome,
                OutcomeCheckInCreate(
                    employment_outcome_id=outcome.id, check_in_date=_add_months(start, 12),
                    employment_status="employed", salary=360000,
                ),
            )

        result = admin_analytics.get_overview_metrics(db, AnalyticsFilters())
        assert result["average_starting_salary"] == 300000.0
        assert result["average_current_salary"] == 360000.0
        assert result["wage_growth_percentage"] == 20.0

    def test_never_invents_salary_for_trainees_without_it(self, db):
        program = _make_program(db)
        for i in range(5):
            user = _make_user(db, f"nosalary{i}@test.com")
            enrollment = _enroll(db, user, program, status="completed")
            outcome = outcome_service.create_employment_outcome(
                db, user.id, EmploymentOutcomeCreate(employment_status="employed"),  # no salary given
            )
            outcome.training_enrollment_id = enrollment.id
            db.commit()

        result = admin_analytics.get_overview_metrics(db, AnalyticsFilters())
        assert result["average_starting_salary"] is None
        assert result["wage_growth_percentage"] is None


class TestSmallCohortSuppression:
    def test_below_min_cohort_size_suppresses_rates(self, db):
        program = _make_program(db)
        for i in range(3):  # below MIN_COHORT_SIZE(5)
            user = _make_user(db, f"small{i}@test.com")
            _enroll(db, user, program, status="completed")

        result = admin_analytics.get_overview_metrics(db, AnalyticsFilters())
        assert result["trainee_count"] == 3
        assert result["sample_size_sufficient"] is False
        assert result["training_completion_rate"] is None
        assert result["placement_rate"] is None

    def test_at_or_above_min_cohort_size_shows_rates(self, db):
        program = _make_program(db)
        for i in range(5):
            user = _make_user(db, f"atmin{i}@test.com")
            _enroll(db, user, program, status="completed")

        result = admin_analytics.get_overview_metrics(db, AnalyticsFilters())
        assert result["sample_size_sufficient"] is True
        assert result["training_completion_rate"] == 100.0


class TestProviderComparison:
    def test_compares_two_providers_independently(self, db):
        program_a = _make_program(db, provider_name="Provider A")
        program_b = _make_program(db, provider_name="Provider B")

        # Provider A: 5 trainees, 4 placed (80%)
        for i in range(5):
            user = _make_user(db, f"a{i}@test.com")
            enrollment = _enroll(db, user, program_a, status="completed")
            if i < 4:
                outcome = outcome_service.create_employment_outcome(
                    db, user.id, EmploymentOutcomeCreate(employment_status="employed"),
                )
                outcome.training_enrollment_id = enrollment.id
                db.commit()

        # Provider B: 5 trainees, 2 placed (40%)
        for i in range(5):
            user = _make_user(db, f"b{i}@test.com")
            enrollment = _enroll(db, user, program_b, status="completed")
            if i < 2:
                outcome = outcome_service.create_employment_outcome(
                    db, user.id, EmploymentOutcomeCreate(employment_status="employed"),
                )
                outcome.training_enrollment_id = enrollment.id
                db.commit()

        results = admin_analytics.get_provider_comparison(db, AnalyticsFilters())
        by_name = {r["provider_name"]: r for r in results}

        assert by_name["Provider A"]["placement_rate"] == 80.0
        assert by_name["Provider B"]["placement_rate"] == 40.0
        # Sorted by placement rate descending among sufficient-sample providers
        assert results[0]["provider_name"] == "Provider A"

    def test_small_provider_not_ranked_unfairly(self, db):
        program_big = _make_program(db, provider_name="Big Provider")
        program_tiny = _make_program(db, provider_name="Tiny Provider")

        for i in range(5):
            user = _make_user(db, f"big{i}@test.com")
            enrollment = _enroll(db, user, program_big, status="completed")
            outcome = outcome_service.create_employment_outcome(
                db, user.id, EmploymentOutcomeCreate(employment_status="employed"),
            )
            outcome.training_enrollment_id = enrollment.id
            db.commit()

        # Tiny provider: 1 trainee, 100% placement -- must not out-rank a real sample.
        user = _make_user(db, "tiny@test.com")
        enrollment = _enroll(db, user, program_tiny, status="completed")
        outcome = outcome_service.create_employment_outcome(
            db, user.id, EmploymentOutcomeCreate(employment_status="employed"),
        )
        outcome.training_enrollment_id = enrollment.id
        db.commit()

        results = admin_analytics.get_provider_comparison(db, AnalyticsFilters())
        by_name = {r["provider_name"]: r for r in results}

        assert by_name["Tiny Provider"]["sample_size_sufficient"] is False
        assert by_name["Tiny Provider"]["placement_rate"] is None
        assert by_name["Tiny Provider"]["trainee_count"] == 1
        # Sufficient-sample provider still ranks first despite a "perfect" tiny sample existing.
        assert results[0]["provider_name"] == "Big Provider"


class TestSkillGapAnalytics:
    def test_aggregates_real_gap_percentages(self, db):
        for name in ["JavaScript", "React", "Node.js"]:
            db.add(Skill(name=name, category="Programming"))
        db.commit()
        program = _make_program(db, skill_names=["JavaScript", "React", "Node.js"])

        # 4 trainees total; 3 lack React, 2 lack Node.js, none lack JavaScript.
        skill_gaps_plan = [
            {"React": True, "Node.js": True},
            {"React": True, "Node.js": True},
            {"React": True, "Node.js": False},
            {"React": False, "Node.js": False},
        ]
        js_skill = db.query(Skill).filter(Skill.name == "JavaScript").first()
        react_skill = db.query(Skill).filter(Skill.name == "React").first()
        node_skill = db.query(Skill).filter(Skill.name == "Node.js").first()
        for i, plan in enumerate(skill_gaps_plan):
            user = _make_user(db, f"gap{i}@test.com")
            _enroll(db, user, program, status="completed")
            db.add(UserSkill(user_id=user.id, skill_id=js_skill.id, proficiency=5))
            if not plan["React"]:
                db.add(UserSkill(user_id=user.id, skill_id=react_skill.id, proficiency=5))
            if not plan["Node.js"]:
                db.add(UserSkill(user_id=user.id, skill_id=node_skill.id, proficiency=5))
            db.commit()

        result = admin_analytics.get_skill_gap_analytics(db, AnalyticsFilters())
        by_skill = {r["skill"]: r for r in result}

        assert by_skill["React"]["trainee_count"] == 3
        assert by_skill["React"]["percentage"] == 75.0
        assert by_skill["Node.js"]["trainee_count"] == 2
        assert by_skill["Node.js"]["percentage"] == 50.0
        assert "JavaScript" not in by_skill  # everyone has it -> never a gap


class TestNonPlacementAnalytics:
    def test_only_creates_categories_supported_by_data(self, db):
        program = _make_program(db)

        # Trainee 1: not placed, low technical skill proficiency -> skill_gap
        user1 = _make_user(db, "np1@test.com")
        _enroll(db, user1, program, status="completed")
        db.add(Skill(name="Python", category="Programming"))
        db.commit()
        python = db.query(Skill).filter(Skill.name == "Python").first()
        db.add(UserSkill(user_id=user1.id, skill_id=python.id, proficiency=1))
        db.commit()

        # Trainee 2: not placed, nothing measurable stands out -> unknown
        user2 = _make_user(db, "np2@test.com")
        _enroll(db, user2, program, status="completed")

        result = admin_analytics.get_non_placement_analytics(db, AnalyticsFilters())
        categories = {r["category"] for r in result}

        # Categories this system cannot support with stored data must never appear.
        assert "location_mismatch" not in categories
        assert "insufficient_opportunities" not in categories
        assert categories.issubset({"skill_gap", "profile_incomplete", "unknown"})
        assert sum(r["trainee_count"] for r in result) == 2

    def test_empty_when_everyone_is_placed(self, db):
        program = _make_program(db)
        user = _make_user(db, "placed@test.com")
        enrollment = _enroll(db, user, program, status="completed")
        outcome = outcome_service.create_employment_outcome(
            db, user.id, EmploymentOutcomeCreate(employment_status="employed"),
        )
        outcome.training_enrollment_id = enrollment.id
        db.commit()

        result = admin_analytics.get_non_placement_analytics(db, AnalyticsFilters())
        assert result == []


class TestFilters:
    def test_provider_filter_narrows_cohort(self, db):
        program_a = _make_program(db, provider_name="Provider A")
        program_b = _make_program(db, provider_name="Provider B")
        for i in range(3):
            user = _make_user(db, f"pa{i}@test.com")
            _enroll(db, user, program_a, status="completed")
        for i in range(2):
            user = _make_user(db, f"pb{i}@test.com")
            _enroll(db, user, program_b, status="completed")

        result = admin_analytics.get_overview_metrics(
            db, AnalyticsFilters(provider_name="Provider A"),
        )
        assert result["trainee_count"] == 3

    def test_date_filter_excludes_out_of_range_enrollments(self, db):
        program = _make_program(db)
        old_user = _make_user(db, "old@test.com")
        outcome_service.create_enrollment(
            db, old_user.id,
            TrainingEnrollmentCreate(training_program_id=program.id, enrollment_date=_add_months(date.today(), -24)),
        )
        recent_user = _make_user(db, "recent@test.com")
        outcome_service.create_enrollment(
            db, recent_user.id,
            TrainingEnrollmentCreate(training_program_id=program.id, enrollment_date=_add_months(date.today(), -1)),
        )

        result = admin_analytics.get_overview_metrics(
            db, AnalyticsFilters(start_date=_add_months(date.today(), -6)),
        )
        assert result["trainee_count"] == 1

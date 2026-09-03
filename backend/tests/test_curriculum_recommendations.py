import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.config import Base
from app.models.user import User
from app.models.skill import Skill, UserSkill
from app.services import outcome_service, admin_analytics
from app.services.admin_analytics import AnalyticsFilters
from app.schemas.outcome import (
    TrainingProgramCreate,
    TrainingEnrollmentCreate,
    TrainingEnrollmentUpdate,
    EmploymentOutcomeCreate,
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


def _make_program(db, provider_name, skill_names):
    for name in skill_names:
        if not db.query(Skill).filter(Skill.name == name).first():
            db.add(Skill(name=name, category="Programming"))
    db.commit()
    return outcome_service.create_training_program(
        db, TrainingProgramCreate(name=f"{provider_name} Program", provider_name=provider_name, skill_names=skill_names)
    )


def _enroll_and_complete(db, user, program):
    enrollment = outcome_service.create_enrollment(db, user.id, TrainingEnrollmentCreate(training_program_id=program.id))
    outcome_service.update_enrollment(db, enrollment, TrainingEnrollmentUpdate(status="completed"))
    return enrollment


def _place(db, user, enrollment, **overrides):
    """Creates an EmploymentOutcome AND links it to the enrollment — easy to
    forget the link, and _build_trainee_records silently treats an unlinked
    outcome as if the trainee were never placed at all."""
    data = dict(employment_status="employed")
    data.update(overrides)
    outcome = outcome_service.create_employment_outcome(db, user.id, EmploymentOutcomeCreate(**data))
    outcome.training_enrollment_id = enrollment.id
    db.commit()
    db.refresh(outcome)
    return outcome


class TestCurriculumRecommendations:
    def test_detects_recurring_gap_with_below_average_placement(self, db):
        """Spec's worked example: many trainees from a program have a React
        gap + that program's placement is below average -> flagged."""
        program_a = _make_program(db, "Provider A", ["JavaScript", "React", "Node.js"])
        program_b = _make_program(db, "Provider B", ["Python", "SQL"])

        js_skill = db.query(Skill).filter(Skill.name == "JavaScript").first()

        # Program A: 5 trainees, all lack React, only 1 placed (20% placement).
        for i in range(5):
            user = _make_user(db, f"a{i}@test.com")
            enrollment = _enroll_and_complete(db, user, program_a)
            db.add(UserSkill(user_id=user.id, skill_id=js_skill.id, proficiency=5))
            db.commit()
            if i == 0:
                _place(db, user, enrollment)

        # Program B: 5 trainees, all skills covered, 5/5 placed (100% placement) -> pulls the average up.
        py_skill = db.query(Skill).filter(Skill.name == "Python").first()
        sql_skill = db.query(Skill).filter(Skill.name == "SQL").first()
        for i in range(5):
            user = _make_user(db, f"b{i}@test.com")
            enrollment = _enroll_and_complete(db, user, program_b)
            db.add(UserSkill(user_id=user.id, skill_id=py_skill.id, proficiency=5))
            db.add(UserSkill(user_id=user.id, skill_id=sql_skill.id, proficiency=5))
            db.commit()
            _place(db, user, enrollment)

        recommendations = admin_analytics.get_curriculum_recommendations(db, AnalyticsFilters())

        assert len(recommendations) >= 1
        rec = next(r for r in recommendations if r["skill"] == "React")
        assert rec["training_program_name"] == "Provider A Program"
        assert rec["affected_trainee_percentage"] == 100.0
        assert "React" in rec["recommendation"]
        assert "curriculum" in rec["recommendation"].lower()
        # Node.js is also 100% gapped in program A -> also flagged
        node_rec = next((r for r in recommendations if r["skill"] == "Node.js"), None)
        assert node_rec is not None

    def test_no_recommendation_when_placement_is_average_or_above(self, db):
        program = _make_program(db, "Provider A", ["JavaScript", "React"])
        js_skill = db.query(Skill).filter(Skill.name == "JavaScript").first()
        for i in range(5):
            user = _make_user(db, f"a{i}@test.com")
            enrollment = _enroll_and_complete(db, user, program)
            db.add(UserSkill(user_id=user.id, skill_id=js_skill.id, proficiency=5))
            db.commit()
            _place(db, user, enrollment)
        # Only one program -> its placement rate equals the overall average -> never "below" average.
        recommendations = admin_analytics.get_curriculum_recommendations(db, AnalyticsFilters())
        assert recommendations == []

    def test_small_sample_programs_excluded(self, db):
        program = _make_program(db, "Tiny Provider", ["React"])
        for i in range(2):  # below MIN_COHORT_SIZE
            user = _make_user(db, f"t{i}@test.com")
            _enroll_and_complete(db, user, program)

        recommendations = admin_analytics.get_curriculum_recommendations(db, AnalyticsFilters())
        assert recommendations == []

    def test_no_data_returns_empty_list(self, db):
        assert admin_analytics.get_curriculum_recommendations(db, AnalyticsFilters()) == []


class TestDemoOutcomeSeed:
    def test_seeds_clearly_labelled_synthetic_trainees(self, db):
        from app.services import demo_outcome_seed

        result = demo_outcome_seed.seed_demo_outcome_data(db)
        assert result["created"] is True
        assert result["trainees_created"] > 0

        demo_users = db.query(User).filter(User.is_demo.is_(True)).all()
        assert len(demo_users) == result["trainees_created"]
        for user in demo_users:
            assert user.email.endswith(f"@{demo_outcome_seed.DEMO_EMAIL_DOMAIN}")

    def test_idempotent_second_call_does_nothing(self, db):
        from app.services import demo_outcome_seed

        first = demo_outcome_seed.seed_demo_outcome_data(db)
        assert first["created"] is True
        count_after_first = db.query(User).filter(User.is_demo.is_(True)).count()

        second = demo_outcome_seed.seed_demo_outcome_data(db)
        assert second["created"] is False
        count_after_second = db.query(User).filter(User.is_demo.is_(True)).count()
        assert count_after_first == count_after_second

    def test_demo_trainees_surfaced_in_overview_metrics(self, db):
        from app.services import demo_outcome_seed

        demo_outcome_seed.seed_demo_outcome_data(db)
        overview = admin_analytics.get_overview_metrics(db, AnalyticsFilters())
        assert overview["demo_trainee_count"] > 0
        assert overview["demo_trainee_count"] == overview["trainee_count"]  # everything seeded is demo data

    def test_real_trainee_not_counted_as_demo(self, db):
        program = _make_program(db, "Real Provider", ["JavaScript"])
        real_user = _make_user(db, "real@test.com")
        _enroll_and_complete(db, real_user, program)

        overview = admin_analytics.get_overview_metrics(db, AnalyticsFilters())
        assert overview["demo_trainee_count"] == 0
        assert overview["trainee_count"] == 1

import pytest
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.config import Base
from app.models.user import User
from app.models.skill import Skill, UserSkill
from app.models.career import Career
from app.services import outcome_service, training_intelligence
from app.schemas.outcome import TrainingProgramCreate, EmploymentOutcomeCreate


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


def _seed_skills(db, names):
    for name in names:
        db.add(Skill(name=name, category="Programming"))
    db.commit()


def _give_user_skill(db, user, skill_name, proficiency):
    skill = db.query(Skill).filter(Skill.name == skill_name).first()
    db.add(UserSkill(user_id=user.id, skill_id=skill.id, proficiency=proficiency))
    db.commit()


def _make_fullstack_program(db):
    """Training: JavaScript, React, Node.js — the example from the spec."""
    return outcome_service.create_training_program(
        db,
        TrainingProgramCreate(
            name="Full Stack Web Development",
            provider_name="Acme Skilling",
            skill_names=["JavaScript", "React", "Node.js"],
        ),
    )


def _make_frontend_career(db):
    career = Career(
        name="Frontend Developer",
        description="Builds UIs",
        category="Software Development",
        required_skills=["JavaScript", "React", "HTML/CSS", "Git"],
        optional_skills=["TypeScript", "Next.js"],
        skill_importance={},
    )
    db.add(career)
    db.commit()
    db.refresh(career)
    return career


# ---------------------------------------------------------------------------
# 1. Training -> Skills
# ---------------------------------------------------------------------------

class TestTrainingSkillMapping:
    def test_maps_to_existing_skill_records_not_duplicates(self, db):
        _seed_skills(db, ["JavaScript", "React", "Node.js", "SQL", "Git"])
        before_count = db.query(Skill).count()

        program = outcome_service.create_training_program(
            db,
            TrainingProgramCreate(
                name="Full Stack Web Development",
                provider_name="Acme",
                skill_names=["JavaScript", "React", "Node.js", "SQL", "Git"],
            ),
        )

        after_count = db.query(Skill).count()
        assert after_count == before_count  # no duplicate Skill rows created

        names = outcome_service.training_program_skill_names(db, program)
        assert set(names) == {"JavaScript", "React", "Node.js", "SQL", "Git"}

    def test_alias_resolution_matches_known_skill(self, db):
        """'Node' should resolve to the existing 'Node.js' skill, not be skipped."""
        _seed_skills(db, ["Node.js"])
        program = outcome_service.create_training_program(
            db, TrainingProgramCreate(name="X", provider_name="Y", skill_names=["Node"])
        )
        names = outcome_service.training_program_skill_names(db, program)
        assert names == ["Node.js"]

    def test_unknown_skill_name_skipped_not_created(self, db):
        program = outcome_service.create_training_program(
            db, TrainingProgramCreate(name="X", provider_name="Y", skill_names=["Quantum Basket Weaving"])
        )
        assert db.query(Skill).count() == 0
        assert outcome_service.training_program_skill_names(db, program) == []


# ---------------------------------------------------------------------------
# 2. Training vs student skills -> Skill Gap
# ---------------------------------------------------------------------------

class TestTrainingVsStudentSkills:
    def test_matches_spec_example(self, db):
        """Training requires JS/React/Node. Student: JS 4/5, React 2/5, Node 1/5.
        Expected: JavaScript -> strong, React -> developing, Node.js -> gap."""
        _seed_skills(db, ["JavaScript", "React", "Node.js"])
        user = _make_user(db)
        _give_user_skill(db, user, "JavaScript", 4)
        _give_user_skill(db, user, "React", 2)
        # Node.js intentionally left undeclared -> proficiency 0 -> a true gap.

        program = _make_fullstack_program(db)

        result = training_intelligence.compare_training_to_student_skills(db, user.id, program.id)

        status_by_skill = {item["skill"]: item["status"] for item in result["skill_breakdown"]}
        assert status_by_skill["JavaScript"] == "strong"
        assert status_by_skill["React"] == "developing"
        assert status_by_skill["Node.js"] == "gap"
        assert result["strong_skills"] == ["JavaScript"]
        assert result["developing_skills"] == ["React"]
        assert result["gap_skills"] == ["Node.js"]

    def test_returns_none_for_unknown_program(self, db):
        user = _make_user(db)
        assert training_intelligence.compare_training_to_student_skills(db, user.id, uuid4()) is None

    def test_no_skills_yields_all_gaps(self, db):
        _seed_skills(db, ["JavaScript", "React", "Node.js"])
        user = _make_user(db)
        program = _make_fullstack_program(db)

        result = training_intelligence.compare_training_to_student_skills(db, user.id, program.id)
        assert set(result["gap_skills"]) == {"JavaScript", "React", "Node.js"}
        assert result["coverage_score"] == 0


# ---------------------------------------------------------------------------
# 3. Training relevance (Training -> Employment)
# ---------------------------------------------------------------------------

class TestTrainingRelevance:
    def test_frontend_developer_is_high_relevance(self, db):
        """Spec example: JS/React/Node training vs 'Frontend Developer' -> HIGH."""
        _make_frontend_career(db)
        result = training_intelligence.calculate_training_relevance(
            db,
            training_skills=["JavaScript", "React", "Node.js"],
            student_skill_map={},
            employment_job_title="Frontend Developer",
        )
        assert result["level"] == "high"
        assert "JavaScript" in result["overlap_skills"]
        assert "React" in result["overlap_skills"]

    def test_sales_executive_is_low_relevance(self, db):
        """Spec example: JS/React/Node training vs 'Sales Executive' -> LOW."""
        _make_frontend_career(db)  # unrelated career present; shouldn't match "Sales Executive"
        result = training_intelligence.calculate_training_relevance(
            db,
            training_skills=["JavaScript", "React", "Node.js"],
            student_skill_map={},
            employment_job_title="Sales Executive",
        )
        assert result["level"] == "low"
        assert result["overlap_skills"] == []

    def test_no_job_information_is_unknown(self, db):
        result = training_intelligence.calculate_training_relevance(
            db,
            training_skills=["JavaScript", "React", "Node.js"],
            student_skill_map={},
        )
        assert result["level"] == "unknown"

    def test_no_training_skills_is_unknown(self, db):
        result = training_intelligence.calculate_training_relevance(
            db, training_skills=[], student_skill_map={}, employment_job_title="Frontend Developer",
        )
        assert result["level"] == "unknown"

    def test_explicit_employment_skills_take_priority_over_title(self, db):
        """A job title that would otherwise infer nothing should still score
        high relevance when employment_skills are given explicitly."""
        result = training_intelligence.calculate_training_relevance(
            db,
            training_skills=["JavaScript", "React", "Node.js"],
            student_skill_map={},
            employment_job_title="Mystery Role",
            employment_skills=["JavaScript", "React", "Node.js"],
        )
        assert result["level"] == "high"

    def test_demonstrated_proficiency_never_downgrades(self, db):
        """Adding real student proficiency on top of a HIGH match must not
        push it below HIGH (bonus-only, never punitive)."""
        _make_frontend_career(db)
        without_student_data = training_intelligence.calculate_training_relevance(
            db, training_skills=["JavaScript", "React", "Node.js"], student_skill_map={},
            employment_job_title="Frontend Developer",
        )
        with_student_data = training_intelligence.calculate_training_relevance(
            db, training_skills=["JavaScript", "React", "Node.js"],
            student_skill_map={"JavaScript": 5, "React": 4},
            employment_job_title="Frontend Developer",
        )
        assert with_student_data["level"] == without_student_data["level"] == "high"

    def test_deterministic_no_ai_dependency(self, db):
        """Calling twice with identical inputs gives identical output — pure function, no AI/randomness."""
        args = dict(
            training_skills=["JavaScript", "React", "Node.js"],
            student_skill_map={"JavaScript": 3},
            employment_job_title="Frontend Developer",
        )
        r1 = training_intelligence.calculate_training_relevance(db, **args)
        r2 = training_intelligence.calculate_training_relevance(db, **args)
        assert r1 == r2


# ---------------------------------------------------------------------------
# 4. Placement readiness (reuses existing engines)
# ---------------------------------------------------------------------------

class TestPlacementReadiness:
    def test_readiness_without_career_or_training(self, db):
        user = _make_user(db)
        result = training_intelligence.calculate_placement_readiness(db, user.id)
        assert result is not None
        assert "readiness_score" in result
        assert isinstance(result["why_ready"], list)
        assert isinstance(result["what_is_missing"], list)
        assert result["recommended_action"]

    def test_readiness_with_unowned_enrollment_returns_none(self, db):
        user_a = _make_user(db, "a@test.com")
        user_b = _make_user(db, "b@test.com")
        _seed_skills(db, ["JavaScript", "React", "Node.js"])
        program = _make_fullstack_program(db)
        from app.schemas.outcome import TrainingEnrollmentCreate
        enrollment = outcome_service.create_enrollment(
            db, user_a.id, TrainingEnrollmentCreate(training_program_id=program.id)
        )
        assert training_intelligence.calculate_placement_readiness(
            db, user_b.id, training_enrollment_id=enrollment.id
        ) is None

    def test_readiness_incorporates_training_context(self, db):
        _seed_skills(db, ["JavaScript", "React", "Node.js"])
        user = _make_user(db)
        _give_user_skill(db, user, "JavaScript", 5)
        program = _make_fullstack_program(db)
        from app.schemas.outcome import TrainingEnrollmentCreate
        enrollment = outcome_service.create_enrollment(
            db, user.id, TrainingEnrollmentCreate(training_program_id=program.id)
        )

        result = training_intelligence.calculate_placement_readiness(
            db, user.id, training_enrollment_id=enrollment.id
        )
        assert result["training"]["training_program_id"] == str(program.id)
        assert result["training"]["skill_coverage"]["strong_skills"] == ["JavaScript"]

    def test_readiness_with_career_uses_career_matching(self, db):
        _seed_skills(db, ["JavaScript", "React", "HTML/CSS", "Git"])
        user = _make_user(db)
        _give_user_skill(db, user, "JavaScript", 5)
        _give_user_skill(db, user, "React", 5)
        career = _make_frontend_career(db)

        result = training_intelligence.calculate_placement_readiness(db, user.id, career_id=career.id)
        assert result["career"] is not None
        assert result["career"]["career_name"] == "Frontend Developer"
        assert result["skill_gap"] is not None


# ---------------------------------------------------------------------------
# 5. Student -> Opportunity (delegates to the existing recommendation engine)
# ---------------------------------------------------------------------------

class TestOpportunitiesForTraining:
    def test_unowned_enrollment_returns_none(self, db):
        user_a = _make_user(db, "a@test.com")
        user_b = _make_user(db, "b@test.com")
        program = _make_fullstack_program(db)
        from app.schemas.outcome import TrainingEnrollmentCreate
        enrollment = outcome_service.create_enrollment(
            db, user_a.id, TrainingEnrollmentCreate(training_program_id=program.id)
        )
        result = training_intelligence.get_opportunities_for_training(
            db, user_b.id, training_enrollment_id=enrollment.id
        )
        assert result is None

    @patch("app.services.training_intelligence.get_recommendations")
    def test_delegates_to_existing_engine_with_training_domain(self, mock_get_recommendations, db):
        """Must call the existing engine exactly once — no second recommendation
        pipeline, no extra provider calls introduced here."""
        mock_get_recommendations.return_value = {"recommendations": [], "user_skill_summary": {}, "source_status": "ok", "message": None}
        user = _make_user(db)
        program = outcome_service.create_training_program(
            db, TrainingProgramCreate(name="X", provider_name="Y", career_domain="Frontend Development")
        )
        from app.schemas.outcome import TrainingEnrollmentCreate
        enrollment = outcome_service.create_enrollment(
            db, user.id, TrainingEnrollmentCreate(training_program_id=program.id)
        )

        result = training_intelligence.get_opportunities_for_training(
            db, user.id, training_enrollment_id=enrollment.id
        )

        assert result is not None
        mock_get_recommendations.assert_called_once()
        _, kwargs = mock_get_recommendations.call_args
        assert kwargs["target_career"] == "Frontend Development"

    @patch("app.services.training_intelligence.get_recommendations")
    def test_no_enrollment_falls_back_to_engine_default(self, mock_get_recommendations, db):
        mock_get_recommendations.return_value = {"recommendations": [], "user_skill_summary": {}, "source_status": "ok", "message": None}
        user = _make_user(db)

        training_intelligence.get_opportunities_for_training(db, user.id)

        mock_get_recommendations.assert_called_once()
        _, kwargs = mock_get_recommendations.call_args
        assert kwargs["target_career"] is None


# ---------------------------------------------------------------------------
# Placement -> Employment: recording a recommended opportunity's outcome
# ---------------------------------------------------------------------------

class TestPlacementLinkedToOpportunity:
    def test_employment_outcome_records_source_opportunity(self, db):
        user = _make_user(db)
        outcome = outcome_service.create_employment_outcome(
            db,
            user.id,
            EmploymentOutcomeCreate(
                employment_status="placed",
                job_title="Frontend Developer",
                source_opportunity_id="jsearch-abc123",
                source_opportunity_title="Frontend Developer at Acme",
            ),
        )
        assert outcome.source_opportunity_id == "jsearch-abc123"
        assert outcome.source_opportunity_title == "Frontend Developer at Acme"

    def test_employment_outcome_without_opportunity_link(self, db):
        """Most outcomes won't trace back to a recommendation — must stay optional."""
        user = _make_user(db)
        outcome = outcome_service.create_employment_outcome(
            db, user.id, EmploymentOutcomeCreate(employment_status="self_employed"),
        )
        assert outcome.source_opportunity_id is None
        assert outcome.source_opportunity_title is None

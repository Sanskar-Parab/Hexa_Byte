import pytest
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.config import Base
from app.models.user import User
from app.models.skill import Skill, UserSkill
from app.models.career import Career
from app.services import outcome_service
from app.services.next_best_action import compute_next_best_action
from app.services.outcome_timeline import _add_months
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


def _make_user(db, email="a@test.com"):
    user = User(email=email, name="Test", password_hash="x")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_program(db, skills):
    for name in skills:
        if not db.query(Skill).filter(Skill.name == name).first():
            db.add(Skill(name=name, category="Programming"))
    db.commit()
    return outcome_service.create_training_program(
        db, TrainingProgramCreate(name="Full Stack", provider_name="Acme", skill_names=skills)
    )


class TestNoOutcomeDataUnaffected:
    def test_user_with_no_training_gets_no_outcome_actions(self, db):
        """A user who has never touched the outcomes system at all must not
        be affected by the new scorers — pure regression guard."""
        user = _make_user(db)
        result = compute_next_best_action(db, user.id)
        assert result["action"] is None or result["action"] not in (
            "IMPROVE_SKILL_FOR_PLACEMENT", "APPLY_OPPORTUNITIES", "EXPLORE_RELEVANT_OPPORTUNITIES",
        )


class TestImproveSkillForPlacement:
    def test_surfaces_top_training_gap_when_not_ready(self, db):
        program = _make_program(db, ["JavaScript", "React", "Node.js"])
        user = _make_user(db)
        outcome_service.create_enrollment(db, user.id, TrainingEnrollmentCreate(training_program_id=program.id))
        # No skills at all -> readiness is low, definitely not "ready".

        result = compute_next_best_action(db, user.id)
        candidate_actions = {c["action"] for c in result["all_candidates"]}
        assert "IMPROVE_SKILL_FOR_PLACEMENT" in candidate_actions

    def test_no_action_when_no_enrollment(self, db):
        user = _make_user(db)
        result = compute_next_best_action(db, user.id)
        candidate_actions = {c["action"] for c in result["all_candidates"]}
        assert "IMPROVE_SKILL_FOR_PLACEMENT" not in candidate_actions


class TestApplyOpportunities:
    def test_completed_training_no_placement_triggers_action(self, db):
        program = _make_program(db, ["JavaScript"])
        user = _make_user(db)
        enrollment = outcome_service.create_enrollment(
            db, user.id, TrainingEnrollmentCreate(training_program_id=program.id)
        )
        outcome_service.update_enrollment(db, enrollment, TrainingEnrollmentUpdate(status="completed"))

        result = compute_next_best_action(db, user.id)
        candidate_actions = {c["action"] for c in result["all_candidates"]}
        assert "APPLY_OPPORTUNITIES" in candidate_actions

    def test_already_placed_does_not_trigger(self, db):
        program = _make_program(db, ["JavaScript"])
        user = _make_user(db)
        enrollment = outcome_service.create_enrollment(
            db, user.id, TrainingEnrollmentCreate(training_program_id=program.id)
        )
        outcome_service.update_enrollment(db, enrollment, TrainingEnrollmentUpdate(status="completed"))
        outcome_service.create_employment_outcome(
            db, user.id, EmploymentOutcomeCreate(employment_status="employed"),
        )

        result = compute_next_best_action(db, user.id)
        candidate_actions = {c["action"] for c in result["all_candidates"]}
        assert "APPLY_OPPORTUNITIES" not in candidate_actions

    def test_incomplete_training_does_not_trigger(self, db):
        program = _make_program(db, ["JavaScript"])
        user = _make_user(db)
        outcome_service.create_enrollment(db, user.id, TrainingEnrollmentCreate(training_program_id=program.id))
        # status stays "enrolled", never completed

        result = compute_next_best_action(db, user.id)
        candidate_actions = {c["action"] for c in result["all_candidates"]}
        assert "APPLY_OPPORTUNITIES" not in candidate_actions


class TestExploreRelevantOpportunities:
    def test_low_relevance_employed_role_triggers_action(self, db):
        program = _make_program(db, ["JavaScript", "React", "Node.js"])
        user = _make_user(db)
        enrollment = outcome_service.create_enrollment(
            db, user.id, TrainingEnrollmentCreate(training_program_id=program.id)
        )
        outcome = outcome_service.create_employment_outcome(
            db, user.id, EmploymentOutcomeCreate(employment_status="employed", job_title="Sales Executive"),
        )
        outcome.training_enrollment_id = enrollment.id
        db.commit()

        result = compute_next_best_action(db, user.id)
        candidate_actions = {c["action"] for c in result["all_candidates"]}
        assert "EXPLORE_RELEVANT_OPPORTUNITIES" in candidate_actions

    def test_high_relevance_role_does_not_trigger(self, db):
        program = _make_program(db, ["JavaScript", "React", "Git"])
        db.add(Career(
            name="Frontend Developer", description="", category="Software",
            required_skills=["JavaScript", "React", "HTML/CSS", "Git"], optional_skills=[],
            skill_importance={},
        ))
        db.commit()
        user = _make_user(db)
        enrollment = outcome_service.create_enrollment(
            db, user.id, TrainingEnrollmentCreate(training_program_id=program.id)
        )
        outcome = outcome_service.create_employment_outcome(
            db, user.id, EmploymentOutcomeCreate(employment_status="employed", job_title="Frontend Developer"),
        )
        outcome.training_enrollment_id = enrollment.id
        db.commit()

        result = compute_next_best_action(db, user.id)
        candidate_actions = {c["action"] for c in result["all_candidates"]}
        assert "EXPLORE_RELEVANT_OPPORTUNITIES" not in candidate_actions

    def test_ended_employment_does_not_trigger(self, db):
        """Only currently-active employment should be evaluated."""
        program = _make_program(db, ["JavaScript"])
        user = _make_user(db)
        enrollment = outcome_service.create_enrollment(
            db, user.id, TrainingEnrollmentCreate(training_program_id=program.id)
        )
        outcome = outcome_service.create_employment_outcome(
            db, user.id,
            EmploymentOutcomeCreate(
                employment_status="employed", job_title="Sales Executive",
                employment_start_date=_add_months(date.today(), -6),
                employment_end_date=_add_months(date.today(), -1),
            ),
        )
        outcome.training_enrollment_id = enrollment.id
        db.commit()

        result = compute_next_best_action(db, user.id)
        candidate_actions = {c["action"] for c in result["all_candidates"]}
        assert "EXPLORE_RELEVANT_OPPORTUNITIES" not in candidate_actions


class TestDeterministicSingleWinner:
    def test_still_returns_exactly_one_action_with_outcome_data_present(self, db):
        """Adding new candidate types must not break the 'exactly one
        primary action' invariant."""
        program = _make_program(db, ["JavaScript", "React"])
        user = _make_user(db)
        enrollment = outcome_service.create_enrollment(
            db, user.id, TrainingEnrollmentCreate(training_program_id=program.id)
        )
        outcome_service.update_enrollment(db, enrollment, TrainingEnrollmentUpdate(status="completed"))

        result = compute_next_best_action(db, user.id)
        assert result["action"] is not None
        assert isinstance(result["title"], str) and result["title"]
        assert len(result["all_candidates"]) >= 1

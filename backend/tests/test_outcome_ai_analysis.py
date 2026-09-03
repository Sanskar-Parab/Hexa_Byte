import pytest
from datetime import date
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.config import Base
from app.models.user import User
from app.models.skill import Skill, UserSkill
from app.models.career import Career
from app.models.progress import UserProgress
from app.models.assessment import UserAssessment
from app.models.resume import Resume
from app.ai.groq_client import NonPlacementAIAnalysis, AttritionAIAnalysis, TrainingRelevanceAIExplanation
from app.services import outcome_service, outcome_ai_analysis
from app.services.outcome_timeline import _add_months
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


# ---------------------------------------------------------------------------
# Non-placement analysis
# ---------------------------------------------------------------------------

class TestNonPlacementAnalysis:
    def test_insufficient_evidence_skips_ai_call(self, db):
        """A well-rounded student we have no negative signal for must come
        back as 'insufficient evidence', not have the AI invent a story.

        Note: a totally empty/fresh user is NOT this case — zero skills,
        zero projects, and zero assessments each read as a below-target
        *signal* in their own right. Insufficient evidence means the
        opposite: everything we can measure looks fine, so we genuinely
        don't know why placement hasn't happened yet.
        """
        db.add(Skill(name="React", category="Programming"))
        db.commit()
        user = _make_user(db)
        db.add(UserSkill(user_id=user.id, skill_id=db.query(Skill).first().id, proficiency=5))
        db.add(UserProgress(user_id=user.id, item_type="project", item_id="p1", status="completed"))
        db.add(UserAssessment(user_id=user.id, answers={}, scores={"technical": 0.8, "analytical": 0.9}))
        db.add(Resume(user_id=user.id, filename="resume.pdf", raw_text="..."))
        db.commit()

        with patch("app.services.outcome_ai_analysis.groq_client") as mock_groq:
            result = outcome_ai_analysis.analyze_non_placement(db, user.id)

        mock_groq.analyze_non_placement.assert_not_called()
        assert result.primary_reason == "Insufficient evidence."
        assert result.confidence == "insufficient"
        assert result.source == "fallback"
        assert result.supporting_evidence == []

    def test_low_confidence_with_single_signal(self, db):
        """Strong on every dimension except one (no resume) -> exactly one
        negative signal -> 'low' confidence, not 'high'."""
        db.add(Skill(name="React", category="Programming"))
        db.commit()
        user = _make_user(db)
        db.add(UserSkill(user_id=user.id, skill_id=db.query(Skill).first().id, proficiency=5))
        db.add(UserProgress(user_id=user.id, item_type="project", item_id="p1", status="completed"))
        db.add(UserAssessment(user_id=user.id, answers={}, scores={"technical": 0.8, "analytical": 0.9}))
        db.commit()
        # (No resume uploaded — the one remaining signal.)

        with patch("app.services.outcome_ai_analysis.groq_client") as mock_groq:
            mock_groq.analyze_non_placement.return_value = (
                NonPlacementAIAnalysis(
                    primary_reason="Missing resume appears to be a barrier.",
                    supporting_evidence_ids=["resume_status"],
                    recommended_intervention="Upload a resume.",
                ),
                None,
            )
            result = outcome_ai_analysis.analyze_non_placement(db, user.id)

        assert result.confidence == "low"
        assert result.source == "ai"

    def test_high_confidence_with_many_signals(self, db):
        """Many distinct negative signals (low skills, low projects, low
        knowledge, no resume) -> high confidence."""
        user = _make_user(db)
        with patch("app.services.outcome_ai_analysis.groq_client") as mock_groq:
            mock_groq.analyze_non_placement.return_value = (
                NonPlacementAIAnalysis(
                    primary_reason="Overall readiness appears low across several dimensions.",
                    supporting_evidence_ids=["technical_skills", "project_completion", "resume_status"],
                    recommended_intervention="Complete the roadmap's next project.",
                ),
                None,
            )
            result = outcome_ai_analysis.analyze_non_placement(db, user.id)

        assert result.confidence == "high"
        assert result.source == "ai"

    def test_hallucinated_evidence_id_is_filtered(self, db):
        """An id the AI invents that isn't in our real evidence set must
        never appear in supporting_evidence."""
        user = _make_user(db)
        with patch("app.services.outcome_ai_analysis.groq_client") as mock_groq:
            mock_groq.analyze_non_placement.return_value = (
                NonPlacementAIAnalysis(
                    primary_reason="Some reason.",
                    supporting_evidence_ids=["technical_skills", "made_up_evidence_id_xyz"],
                    recommended_intervention="Do something.",
                ),
                None,
            )
            result = outcome_ai_analysis.analyze_non_placement(db, user.id)

        assert not any("made_up_evidence_id_xyz" in s for s in result.supporting_evidence)
        assert any("Technical skill proficiency" in s for s in result.supporting_evidence)

    def test_ai_failure_falls_back_deterministically(self, db):
        user = _make_user(db)
        with patch("app.services.outcome_ai_analysis.groq_client") as mock_groq:
            mock_groq.analyze_non_placement.return_value = (None, "AI service error")
            result = outcome_ai_analysis.analyze_non_placement(db, user.id)

        assert result.source == "fallback"
        assert result.primary_reason != "Insufficient evidence."  # real signals exist, just no AI
        assert result.confidence == "high"  # technical/project/knowledge/resume all trigger by default

    def test_unowned_training_enrollment_returns_none(self, db):
        user_a = _make_user(db, "a@test.com")
        user_b = _make_user(db, "b@test.com")
        program = outcome_service.create_training_program(
            db, TrainingProgramCreate(name="X", provider_name="Y")
        )
        enrollment = outcome_service.create_enrollment(
            db, user_a.id, TrainingEnrollmentCreate(training_program_id=program.id)
        )
        with patch("app.services.outcome_ai_analysis.groq_client"):
            result = outcome_ai_analysis.analyze_non_placement(
                db, user_b.id, training_enrollment_id=enrollment.id,
            )
        assert result is None


# ---------------------------------------------------------------------------
# Attrition analysis
# ---------------------------------------------------------------------------

class TestAttritionAnalysis:
    def _make_ended_outcome(self, db, user, **overrides):
        start = _add_months(date.today(), -6)
        data = dict(
            employment_status="looking_for_work",
            employment_start_date=start,
            employment_end_date=_add_months(start, 3),
        )
        data.update(overrides)
        return outcome_service.create_employment_outcome(db, user.id, EmploymentOutcomeCreate(**data))

    def test_unowned_outcome_returns_none(self, db):
        user_a = _make_user(db, "a@test.com")
        user_b = _make_user(db, "b@test.com")
        outcome = self._make_ended_outcome(db, user_a)
        with patch("app.services.outcome_ai_analysis.groq_client"):
            result = outcome_ai_analysis.analyze_attrition(db, user_b.id, outcome.id)
        assert result is None

    def test_employment_not_ended_is_insufficient_evidence(self, db):
        user = _make_user(db)
        outcome = outcome_service.create_employment_outcome(
            db, user.id, EmploymentOutcomeCreate(employment_status="employed"),
        )
        with patch("app.services.outcome_ai_analysis.groq_client") as mock_groq:
            result = outcome_ai_analysis.analyze_attrition(db, user.id, outcome.id)
        mock_groq.analyze_attrition.assert_not_called()
        assert result.primary_reason == "Insufficient evidence."
        assert result.confidence == "insufficient"
        assert result.category == "unknown"

    def test_ended_with_no_recorded_reason_is_insufficient(self, db):
        """Employment ended but nothing else was ever recorded about it."""
        user = _make_user(db)
        outcome = self._make_ended_outcome(db, user)
        with patch("app.services.outcome_ai_analysis.groq_client") as mock_groq:
            result = outcome_ai_analysis.analyze_attrition(db, user.id, outcome.id)
        mock_groq.analyze_attrition.assert_not_called()
        assert result.primary_reason == "Insufficient evidence."

    def test_reason_for_leaving_becomes_evidence_and_high_confidence_alone(self, db):
        user = _make_user(db)
        outcome = self._make_ended_outcome(db, user)
        outcome_service.create_check_in(
            db, outcome,
            OutcomeCheckInCreate(
                employment_outcome_id=outcome.id,
                employment_status="looking_for_work",
                still_employed=False,
                reason_for_leaving="Relocated to a different city",
                notes="Company didn't support remote work",
            ),
        )
        with patch("app.services.outcome_ai_analysis.groq_client") as mock_groq:
            mock_groq.analyze_attrition.return_value = (
                AttritionAIAnalysis(
                    category="location",
                    primary_reason="Relocation appears to be the reason employment ended.",
                    supporting_evidence_ids=["reason_for_leaving", "check_in_notes"],
                    recommended_intervention="Explore remote-friendly roles.",
                ),
                None,
            )
            result = outcome_ai_analysis.analyze_attrition(db, user.id, outcome.id)

        assert result.category == "location"
        assert result.source == "ai"
        assert any("Relocated" in s for s in result.supporting_evidence)

    def test_out_of_vocabulary_category_coerced_to_unknown(self, db):
        user = _make_user(db)
        outcome = self._make_ended_outcome(db, user)
        outcome_service.create_check_in(
            db, outcome,
            OutcomeCheckInCreate(
                employment_outcome_id=outcome.id, employment_status="looking_for_work",
                reason_for_leaving="Not sure why, it just ended.",
            ),
        )
        with patch("app.services.outcome_ai_analysis.groq_client") as mock_groq:
            mock_groq.analyze_attrition.return_value = (
                AttritionAIAnalysis(
                    category="the_ai_made_this_up",
                    primary_reason="Reason.",
                    supporting_evidence_ids=["reason_for_leaving"],
                    recommended_intervention="Action.",
                ),
                None,
            )
            result = outcome_ai_analysis.analyze_attrition(db, user.id, outcome.id)

        assert result.category == "unknown"

    def test_ai_failure_falls_back(self, db):
        user = _make_user(db)
        outcome = self._make_ended_outcome(db, user)
        outcome_service.create_check_in(
            db, outcome,
            OutcomeCheckInCreate(
                employment_outcome_id=outcome.id, employment_status="looking_for_work",
                reason_for_leaving="Contract ended",
            ),
        )
        with patch("app.services.outcome_ai_analysis.groq_client") as mock_groq:
            mock_groq.analyze_attrition.return_value = (None, "AI unavailable")
            result = outcome_ai_analysis.analyze_attrition(db, user.id, outcome.id)

        assert result.source == "fallback"
        assert result.category == "unknown"
        assert "Contract ended" in result.primary_reason


# ---------------------------------------------------------------------------
# Training relevance explanation
# ---------------------------------------------------------------------------

class TestTrainingRelevanceExplanation:
    def _make_program(self, db, skills):
        for name in skills:
            if not db.query(Skill).filter(Skill.name == name).first():
                db.add(Skill(name=name, category="Programming"))
        db.commit()
        return outcome_service.create_training_program(
            db, TrainingProgramCreate(name="Full Stack", provider_name="Acme", skill_names=skills)
        )

    def test_unknown_program_returns_none(self, db):
        user = _make_user(db)
        with patch("app.services.outcome_ai_analysis.groq_client"):
            result = outcome_ai_analysis.explain_training_relevance(db, user.id, uuid4())
        assert result is None

    def test_ai_cannot_override_deterministic_level(self, db):
        """Even if a compromised/malicious AI response tried to change the
        level, the schema has no field for it — the response always carries
        the deterministically-computed level."""
        program = self._make_program(db, ["JavaScript", "React", "Node.js"])
        user = _make_user(db)
        career = Career(
            name="Frontend Developer", description="", category="Software",
            required_skills=["JavaScript", "React", "HTML/CSS", "Git"], optional_skills=[],
            skill_importance={},
        )
        db.add(career)
        db.commit()

        with patch("app.services.outcome_ai_analysis.groq_client") as mock_groq:
            mock_groq.explain_training_relevance.return_value = (
                TrainingRelevanceAIExplanation(explanation="JavaScript and React both apply directly to this role."),
                None,
            )
            result = outcome_ai_analysis.explain_training_relevance(
                db, user.id, program.id, employment_job_title="Frontend Developer",
            )

        assert result.level == "high"  # deterministic outcome for this overlap, per Phase 2
        assert result.source == "ai"
        assert "JavaScript" in result.explanation

    def test_falls_back_to_deterministic_reason_when_ai_unavailable(self, db):
        program = self._make_program(db, ["JavaScript", "React", "Node.js"])
        user = _make_user(db)
        with patch("app.services.outcome_ai_analysis.groq_client") as mock_groq:
            mock_groq.explain_training_relevance.return_value = (None, "AI unavailable")
            result = outcome_ai_analysis.explain_training_relevance(
                db, user.id, program.id, employment_job_title="Sales Executive",
            )

        assert result.source == "fallback"
        assert result.level == "low"
        assert result.explanation  # deterministic template reason, never empty

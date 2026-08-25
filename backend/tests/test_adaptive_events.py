import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch

from app.services.adaptive_events import (
    on_skill_assessment_completed,
    on_project_completed,
    on_resume_analyzed,
    on_job_analyzed,
)


def _make_skill(skill_id=None, name="JavaScript"):
    skill = MagicMock()
    skill.id = skill_id or uuid4()
    skill.name = name
    return skill


def _make_user_skill(user_id=None, skill_id=None, proficiency=3, confidence="LOW"):
    us = MagicMock()
    us.id = uuid4()
    us.user_id = user_id
    us.skill_id = skill_id
    us.proficiency = proficiency
    us.level_name = "Intermediate"
    us.confidence = confidence
    return us


def _make_career_recommendation(user_id=None, career_id=None, score=0.6):
    rec = MagicMock()
    rec.id = uuid4()
    rec.user_id = user_id
    rec.career_id = career_id or uuid4()
    rec.match_score = score
    rec.confidence = "Medium"
    rec.why_matches = []
    rec.strengths = []
    rec.missing_skills = []
    return rec


class TestOnSkillAssessmentCompleted:
    @patch("app.services.adaptive_events._recompute_career_readiness")
    @patch("app.services.adaptive_events._adapt_roadmaps_after_skill_change")
    def test_returns_updates_dict(self, mock_adapt, mock_recompute):
        db = MagicMock()
        user_id = uuid4()
        skill_id = uuid4()

        result = on_skill_assessment_completed(db, user_id, skill_id, proficiency=3, score_percentage=60.0)

        assert "skill_assessment" in result
        assert result["skill_assessment"] is True
        mock_recompute.assert_called_once()
        mock_adapt.assert_called_once()

    @patch("app.services.adaptive_events._recompute_career_readiness")
    @patch("app.services.adaptive_events._adapt_roadmaps_after_skill_change")
    def test_passes_correct_params(self, mock_adapt, mock_recompute):
        db = MagicMock()
        user_id = uuid4()
        skill_id = uuid4()

        on_skill_assessment_completed(db, user_id, skill_id, proficiency=4, score_percentage=80.0)

        args = mock_recompute.call_args
        assert args[0][0] is db
        assert args[0][1] == user_id

        args = mock_adapt.call_args
        assert args[0][0] is db
        assert args[0][1] == user_id
        assert args[0][2] == skill_id


class TestOnProjectCompleted:
    @patch("app.services.adaptive_events._create_project_evidence")
    @patch("app.services.adaptive_events._recompute_career_readiness")
    def test_returns_updates_dict(self, mock_recompute, mock_evidence):
        db = MagicMock()
        user_id = uuid4()
        project_id = uuid4()

        result = on_project_completed(db, user_id, project_id)

        assert "project_completed" in result
        assert result["project_completed"] is True
        mock_evidence.assert_called_once()
        mock_recompute.assert_called_once()

    @patch("app.services.adaptive_events._create_project_evidence")
    @patch("app.services.adaptive_events._recompute_career_readiness")
    def test_passes_correct_params(self, mock_recompute, mock_evidence):
        db = MagicMock()
        user_id = uuid4()
        project_id = uuid4()

        on_project_completed(db, user_id, project_id)

        args = mock_evidence.call_args
        assert args[0][0] is db
        assert args[0][1] == user_id
        assert args[0][2] == project_id


class TestOnResumeAnalyzed:
    @patch("app.services.adaptive_events._recompute_career_readiness")
    def test_returns_updates_dict(self, mock_recompute):
        db = MagicMock()
        user_id = uuid4()
        resume_id = uuid4()

        result = on_resume_analyzed(db, user_id, resume_id, matched_skills_count=5)

        assert "resume_analyzed" in result
        assert result["resume_analyzed"] is True
        assert result["matched_skills_count"] == 5
        mock_recompute.assert_called_once()

    @patch("app.services.adaptive_events._recompute_career_readiness")
    def test_zero_matched_skills(self, mock_recompute):
        db = MagicMock()
        user_id = uuid4()
        resume_id = uuid4()

        result = on_resume_analyzed(db, user_id, resume_id, matched_skills_count=0)

        assert result["matched_skills_count"] == 0


class TestOnJobAnalyzed:
    @patch("app.services.adaptive_events._recompute_career_readiness")
    def test_returns_updates_dict(self, mock_recompute):
        db = MagicMock()
        user_id = uuid4()
        job_id = uuid4()

        result = on_job_analyzed(db, user_id, job_id, evidence_created=3)

        assert "job_analyzed" in result
        assert result["job_analyzed"] is True
        assert result["evidence_created"] == 3
        mock_recompute.assert_called_once()

    @patch("app.services.adaptive_events._recompute_career_readiness")
    def test_zero_evidence(self, mock_recompute):
        db = MagicMock()
        user_id = uuid4()
        job_id = uuid4()

        result = on_job_analyzed(db, user_id, job_id, evidence_created=0)

        assert result["evidence_created"] == 0


class TestRecomputeCareerReadiness:
    def test_updates_match_scores(self):
        from app.services.adaptive_events import _recompute_career_readiness

        db = MagicMock()
        user_id = uuid4()
        career_id = uuid4()

        old_rec = _make_career_recommendation(user_id=user_id, career_id=career_id, score=0.5)
        db.query.return_value.filter.return_value.all.return_value = [old_rec]

        new_recs = [{
            "career_id": career_id,
            "match_score": 0.75,
            "confidence": "High",
            "why_matches": ["Improved skills"],
            "strengths": ["Python"],
            "missing_skills": [],
        }]

        updates = {}
        with patch("app.services.career_matching.compute_career_recommendations", return_value=new_recs):
            _recompute_career_readiness(db, user_id, updates)

        assert old_rec.match_score == 0.75
        assert old_rec.confidence == "High"

    def test_no_recs_does_nothing(self):
        from app.services.adaptive_events import _recompute_career_readiness

        db = MagicMock()
        user_id = uuid4()

        db.query.return_value.filter.return_value.all.return_value = []

        updates = {}
        _recompute_career_readiness(db, user_id, updates)
        assert len(updates) == 0


class TestAdaptRoadmapsAfterSkillChange:
    @patch("app.services.roadmap_service._evaluate_phase_adaptation", return_value="skipped")
    def test_adapts_phase_mode(self, mock_eval):
        from app.services.adaptive_events import _adapt_roadmaps_after_skill_change

        db = MagicMock()
        user_id = uuid4()
        skill_id = uuid4()

        skill = _make_skill(skill_id=skill_id, name="Python")
        user_skill = _make_user_skill(user_id=user_id, skill_id=skill_id, proficiency=5)

        roadmap = MagicMock()
        roadmap.id = uuid4()

        phase = MagicMock()
        phase.id = uuid4()
        phase.skills = ["Python", "SQL"]
        phase.status = "not_started"
        phase.adaptation_mode = "full"

        db.query.return_value.filter.return_value.first.side_effect = [skill, user_skill]
        db.query.return_value.filter.return_value.all.side_effect = [[roadmap], [phase], [user_skill], [skill]]

        updates = {}
        _adapt_roadmaps_after_skill_change(db, user_id, skill_id, updates)

        # Phase should have been adapted since _evaluate_phase_adaptation returns "skipped"
        assert phase.adaptation_mode == "skipped"
        assert f"roadmap_phase_{phase.id}_adapted" in updates

    def test_no_roadmaps_does_nothing(self):
        from app.services.adaptive_events import _adapt_roadmaps_after_skill_change

        db = MagicMock()
        user_id = uuid4()
        skill_id = uuid4()

        skill = _make_skill(skill_id=skill_id, name="Python")
        user_skill = _make_user_skill(user_id=user_id, skill_id=skill_id, proficiency=3)

        db.query.return_value.filter.return_value.first.side_effect = [skill, user_skill]
        db.query.return_value.filter.return_value.all.side_effect = [[], [], [user_skill], [skill]]

        updates = {}
        _adapt_roadmaps_after_skill_change(db, user_id, skill_id, updates)
        assert len(updates) == 0


class TestCreateProjectEvidence:
    @patch("app.services.evidence_service.create_evidence")
    def test_creates_evidence_for_project_skills(self, mock_create):
        from app.services.adaptive_events import _create_project_evidence

        db = MagicMock()
        user_id = uuid4()
        project_id = uuid4()

        project = MagicMock()
        project.title = "Data Pipeline"
        project.skills_developed = ["Python"]

        rec = MagicMock()
        rec.project_id = uuid4()

        skill = _make_skill(name="Python")

        # Set up separate query mocks for each model
        rec_query = MagicMock()
        rec_query.filter.return_value.first.return_value = rec

        proj_query = MagicMock()
        proj_query.filter.return_value.first.return_value = project

        skill_query = MagicMock()
        skill_query.all.return_value = [skill]

        user_skill_query = MagicMock()
        user_skill_query.filter.return_value.first.return_value = None

        def query_side_effect(model):
            name = getattr(model, "__name__", str(model))
            if name == "RecommendedProject":
                return rec_query
            elif name == "Project":
                return proj_query
            elif name == "Skill":
                return skill_query
            elif name == "UserSkill":
                return user_skill_query
            elif name == "AIGeneratedProject":
                return MagicMock()
            return MagicMock()

        db.query.side_effect = query_side_effect

        updates = {}
        _create_project_evidence(db, user_id, project_id, updates)

        assert "project_evidence_created" in updates
        assert updates["project_evidence_created"] == 1

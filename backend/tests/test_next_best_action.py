import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.services.next_best_action import (
    compute_next_best_action,
    _score_assess_skill,
    _score_retake_assessment,
    _score_start_phase,
    _score_complete_phase,
    _score_build_project,
    _score_upload_resume,
    _score_analyze_job,
    ACTION_TYPES,
)


def _make_skill(name, skill_id=None):
    s = MagicMock()
    s.id = skill_id or uuid4()
    s.name = name
    return s


def _make_user_skill(skill, proficiency, confidence="LOW"):
    us = MagicMock()
    us.skill_id = skill.id
    us.proficiency = proficiency
    us.confidence = confidence
    us.id = uuid4()
    return us


def _make_career(required_skills, optional_skills=None, skill_importance=None):
    c = MagicMock()
    c.id = uuid4()
    c.name = "Software Engineer"
    c.required_skills = required_skills
    c.optional_skills = optional_skills or []
    c.skill_importance = skill_importance or {}
    return c


def _make_assessment(scores, days_old=0):
    a = MagicMock()
    a.id = uuid4()
    a.scores = scores
    now = datetime.now(timezone.utc)
    a.created_at = now - __import__("datetime").timedelta(days=days_old)
    return a


def _make_phase(phase_id=None, phase_number=1, title="Phase 1", status="not_started",
                adaptation_mode="full", skills=None, duration_weeks=4):
    p = MagicMock()
    p.id = phase_id or uuid4()
    p.phase_number = phase_number
    p.title = title
    p.status = status
    p.adaptation_mode = adaptation_mode
    p.skills = skills or ["Python"]
    p.duration_weeks = duration_weeks
    p.objective = f"Learn {title}"
    return p


def _make_project(project_id=None, title="Test Project", difficulty="beginner",
                  skills_developed=None, estimated_duration_weeks=2):
    p = MagicMock()
    p.id = project_id or uuid4()
    p.title = title
    p.difficulty = difficulty
    p.skills_developed = skills_developed or ["Python"]
    p.estimated_duration_weeks = estimated_duration_weeks
    p.description = f"Build a {title}"
    return p


def _make_recommended_project(project, career_id=None, match_score=0.8, status="recommended"):
    rp = MagicMock()
    rp.id = uuid4()
    rp.project_id = project.id
    rp.project = project
    rp.career_id = career_id or uuid4()
    rp.match_score = match_score
    rp.status = status
    return rp


def _make_progress(item_type, item_id, status):
    p = MagicMock()
    p.id = uuid4()
    p.item_type = item_type
    p.item_id = str(item_id)
    p.status = status
    return p


def _make_evidence(skill, source_type="manual", confidence="LOW"):
    e = MagicMock()
    e.id = uuid4()
    e.skill_id = skill.id
    e.source_type = source_type
    e.confidence = confidence
    return e


def _make_career_recommendation(missing_skills=None):
    cr = MagicMock()
    cr.id = uuid4()
    if missing_skills is None:
        cr.missing_skills = ["React", "Node.js"]
    else:
        cr.missing_skills = missing_skills
    return cr


def _make_profile(internship=None, work=None):
    p = MagicMock()
    p.internship_experience = internship
    p.work_experience = work
    return p


def _make_db(user_skills=None, all_skills=None, career=None, assessments=None,
             phases=None, recommended_projects=None, progress_items=None,
             evidence_records=None, profile=None, career_recommendation=None,
             roadmaps=None):
    db = MagicMock()

    us_query = MagicMock()
    us_query.filter.return_value.all.return_value = user_skills or []

    skill_query = MagicMock()
    skill_query.all.return_value = all_skills or []

    career_query = MagicMock()
    career_query.filter.return_value.first.return_value = career

    assessment_query = MagicMock()
    assessment_query.filter.return_value.all.return_value = assessments or []

    progress_query = MagicMock()
    progress_query.filter.return_value.all.return_value = progress_items or []

    evidence_query = MagicMock()
    evidence_query.filter.return_value.all.return_value = evidence_records or []

    profile_query = MagicMock()
    profile_query.filter.return_value.first.return_value = profile

    cr_query = MagicMock()
    cr_query.filter.return_value.order_by.return_value.first.return_value = career_recommendation
    cr_query.filter.return_value.first.return_value = career_recommendation

    roadmap_query = MagicMock()
    roadmap_query.filter.return_value.first.return_value = None
    if roadmaps:
        roadmap_query.filter.return_value.first.return_value = roadmaps[0]

    phase_query = MagicMock()
    phase_query.filter.return_value.order_by.return_value.all.return_value = phases or []

    rp_query = MagicMock()
    rp_query.filter.return_value.all.return_value = recommended_projects or []

    project_query = MagicMock()
    project_query.filter.return_value.first.return_value = None
    if recommended_projects:
        project_query.filter.return_value.first.return_value = recommended_projects[0].project

    def query_side_effect(model):
        name = getattr(model, "__name__", str(model))
        if name == "UserSkill":
            return us_query
        elif name == "Skill":
            return skill_query
        elif name == "Career":
            return career_query
        elif name == "UserAssessment":
            return assessment_query
        elif name == "UserProgress":
            return progress_query
        elif name == "SkillEvidence":
            return evidence_query
        elif name == "Profile":
            return profile_query
        elif name == "CareerRecommendation":
            return cr_query
        elif name == "Roadmap":
            return roadmap_query
        elif name == "RoadmapPhase":
            return phase_query
        elif name == "RecommendedProject":
            return rp_query
        elif name == "Project":
            return project_query
        return MagicMock()

    db.query.side_effect = query_side_effect
    return db


class TestNextBestActionScoring:
    def test_assess_skill_no_assessment_evidence(self):
        skill1 = _make_skill("Python")
        user_skills = [_make_user_skill(skill1, 1)]
        career = _make_career(["Python"], skill_importance={"Python": 1.0})
        evidence = []

        result = _score_assess_skill(user_skills, career, {skill1.id: skill1}, evidence)
        assert result is not None
        assert result["action_type"] == "ASSESS_SKILL"
        assert "Python" in result["title"]
        assert result["priority_score"] > 0.5

    def test_assess_skill_with_high_confidence_skipped(self):
        skill1 = _make_skill("Python")
        user_skills = [_make_user_skill(skill1, 4, confidence="HIGH")]
        career = _make_career(["Python"], skill_importance={"Python": 1.0})
        evidence = []

        result = _score_assess_skill(user_skills, career, {skill1.id: skill1}, evidence)
        assert result is None

    def test_assess_skill_no_career(self):
        result = _score_assess_skill([], None, {}, [])
        assert result is None

    def test_retake_assessment_low_score(self):
        assessments = [_make_assessment({"technical_interest": 0.3, "problem_solving": 0.4}, days_old=5)]
        result = _score_retake_assessment(assessments)
        assert result is not None
        assert result["action_type"] == "RETAKE_ASSESSMENT"

    def test_retake_assessment_high_score_skipped(self):
        assessments = [_make_assessment({"technical_interest": 0.8, "problem_solving": 0.9})]
        result = _score_retake_assessment(assessments)
        assert result is None

    def test_retake_assessment_no_assessments(self):
        result = _score_retake_assessment([])
        assert result is None

    def test_start_phase(self):
        phase = _make_phase(skills=["Python"], status="not_started")
        career = _make_career(["Python"], skill_importance={"Python": 1.0})
        skill1 = _make_skill("Python")
        user_skills = [_make_user_skill(skill1, 1)]

        result = _score_start_phase([phase], [], user_skills, career, {skill1.id: skill1})
        assert result is not None
        assert result["action_type"] == "START_PHASE"
        assert "Phase 1" in result["title"]

    def test_start_phase_all_completed(self):
        phase = _make_phase(skills=["Python"], status="completed")
        career = _make_career(["Python"])
        result = _score_start_phase([phase], [], [], career, {})
        assert result is None

    def test_start_phase_skipped(self):
        phase = _make_phase(adaptation_mode="skipped")
        result = _score_start_phase([phase], [], [], None, {})
        assert result is None

    def test_complete_phase(self):
        phase = _make_phase(status="in_progress")
        progress = [_make_progress("phase", phase.id, "in_progress")]

        result = _score_complete_phase([phase], progress)
        assert result is not None
        assert result["action_type"] == "COMPLETE_PHASE"
        assert result["priority_score"] == 0.65

    def test_complete_phase_none_in_progress(self):
        phase = _make_phase(status="not_started")
        result = _score_complete_phase([phase], [])
        assert result is None

    def test_build_project_in_progress(self):
        project = _make_project(title="Build API")
        rec = _make_recommended_project(project, match_score=0.9, status="in_progress")
        progress = [_make_progress("project", project.id, "in_progress")]

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = project

        result = _score_build_project(db, [rec], progress)
        assert result is not None
        assert result["action_type"] == "BUILD_PROJECT"
        assert "Build API" in result["title"]

    def test_build_project_recommended(self):
        project = _make_project(title="ML Model")
        rec = _make_recommended_project(project, match_score=0.8, status="recommended")

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = project

        result = _score_build_project(db, [rec], [])
        assert result is not None
        assert result["action_type"] == "BUILD_PROJECT"

    def test_upload_resume_no_work_experience(self):
        profile = _make_profile(work=None)
        skill1 = _make_skill("Python")
        user_skills = [_make_user_skill(skill1, 2, confidence="LOW")]

        result = _score_upload_resume(profile, user_skills)
        assert result is not None
        assert result["action_type"] == "UPLOAD_RESUME"

    def test_upload_resume_has_work_experience(self):
        profile = _make_profile(work="2 years at Google")
        skill1 = _make_skill("Python")
        user_skills = [_make_user_skill(skill1, 2)]

        result = _score_upload_resume(profile, user_skills)
        assert result is None

    def test_upload_resume_no_low_confidence(self):
        profile = _make_profile(work=None)
        skill1 = _make_skill("Python")
        user_skills = [_make_user_skill(skill1, 3, confidence="MEDIUM")]

        result = _score_upload_resume(profile, user_skills)
        assert result is None

    def test_analyze_job_with_missing_skills(self):
        cr = _make_career_recommendation(missing_skills=["React", "Node.js", "TypeScript"])
        result = _score_analyze_job(cr)
        assert result is not None
        assert result["action_type"] == "ANALYZE_JOB"
        assert "3 missing" in result["current"]

    def test_analyze_job_no_missing(self):
        cr = _make_career_recommendation(missing_skills=[])
        result = _score_analyze_job(cr)
        assert result is None


class TestNextBestActionIntegration:
    def test_deterministic_returns_one_action(self):
        skill1 = _make_skill("Python")
        skill2 = _make_skill("React")
        user_skills = [_make_user_skill(skill1, 1), _make_user_skill(skill2, 0)]
        career = _make_career(["Python", "React"], skill_importance={"Python": 1.0, "React": 0.8})
        evidence = [_make_evidence(skill1, "manual", "LOW")]
        assessments = [_make_assessment({"technical_interest": 0.3})]
        profile = _make_profile(work=None)

        rec = _make_career_recommendation(["React"])
        cr_query = MagicMock()
        cr_query.filter.return_value.order_by.return_value.first.return_value = rec

        db = _make_db(
            user_skills=user_skills,
            all_skills=[skill1, skill2],
            career=career,
            assessments=assessments,
            evidence_records=evidence,
            profile=profile,
            career_recommendation=rec,
        )

        result = compute_next_best_action(db, uuid4(), career.id)

        assert result["action"] in ACTION_TYPES
        assert result["title"] is not None
        assert result["why"] is not None
        assert result["priority_score"] > 0
        assert len(result["all_candidates"]) > 0

    def test_no_data_returns_no_action(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None

        def query_side_effect(model):
            q = MagicMock()
            q.filter.return_value.all.return_value = []
            q.filter.return_value.first.return_value = None
            q.filter.return_value.order_by.return_value.first.return_value = None
            return q
        db.query.side_effect = query_side_effect

        result = compute_next_best_action(db, uuid4())
        assert result["action"] is None

    def test_all_action_types_valid(self):
        assert len(ACTION_TYPES) == 10
        expected = {
            "ASSESS_SKILL", "START_PHASE", "COMPLETE_PHASE", "BUILD_PROJECT",
            "UPLOAD_RESUME", "ANALYZE_JOB", "RETAKE_ASSESSMENT",
            "IMPROVE_SKILL_FOR_PLACEMENT", "APPLY_OPPORTUNITIES", "EXPLORE_RELEVANT_OPPORTUNITIES",
        }
        assert set(ACTION_TYPES) == expected

    def test_scores_are_deterministic(self):
        skill1 = _make_skill("Python")
        user_skills = [_make_user_skill(skill1, 2)]
        career = _make_career(["Python"], skill_importance={"Python": 1.0})

        scores = []
        for _ in range(5):
            result = _score_assess_skill(user_skills, career, {skill1.id: skill1}, [])
            scores.append(result["priority_score"])

        assert len(set(scores)) == 1

    def test_priority_ordering(self):
        skill1 = _make_skill("Python")
        user_skills = [_make_user_skill(skill1, 1)]
        career = _make_career(["Python"], skill_importance={"Python": 1.0})

        assess = _score_assess_skill(user_skills, career, {skill1.id: skill1}, [])
        retake = _score_retake_assessment([])
        upload = _score_upload_resume(_make_profile(work=None), user_skills)

        assert assess is not None
        assert retake is None
        assert upload is not None
        assert assess["priority_score"] > upload["priority_score"]

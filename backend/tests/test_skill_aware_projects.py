import pytest
from uuid import uuid4
from unittest.mock import MagicMock

from app.services.skill_aware_projects import (
    compute_user_difficulty_level,
    rank_skill_aware_projects,
    _compute_career_relevance,
    _compute_gap_relevance,
    _compute_roadmap_relevance,
    _compute_difficulty_fit,
    _compute_history_penalty,
    _get_skill_gaps,
    DIFFICULTY_LEVELS,
    DIFFICULTY_ORDER,
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


def _make_project(project_id=None, title="Test Project", difficulty="beginner",
                  skills_developed=None, estimated_duration_weeks=2):
    p = MagicMock()
    p.id = project_id or uuid4()
    p.title = title
    p.difficulty = difficulty
    p.skills_developed = skills_developed or ["Python"]
    p.estimated_duration_weeks = estimated_duration_weeks
    p.description = f"Build a {title}"
    p.expected_outcome = "Portfolio piece"
    p.portfolio_value = "High"
    return p


def _make_career(required_skills=None, skill_importance=None, optional_skills=None):
    c = MagicMock()
    c.id = uuid4()
    c.name = "Software Engineer"
    c.required_skills = required_skills or ["Python", "JavaScript"]
    c.optional_skills = optional_skills or []
    c.skill_importance = skill_importance or {}
    return c


def _make_phase(phase_id=None, phase_number=1, title="Phase 1", status="not_started",
                adaptation_mode="full", skills=None):
    p = MagicMock()
    p.id = phase_id or uuid4()
    p.phase_number = phase_number
    p.title = title
    p.status = status
    p.adaptation_mode = adaptation_mode
    p.skills = skills or ["Python"]
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


class TestUserDifficultyLevel:
    def test_beginner_no_skills(self):
        assert compute_user_difficulty_level([], {}) == "BEGINNER"

    def test_beginner_low_proficiency(self):
        skill = _make_skill("Python")
        us = _make_user_skill(skill, 1)
        assert compute_user_difficulty_level([us], {skill.id: skill}) == "BEGINNER"

    def test_intermediate(self):
        skill1 = _make_skill("Python")
        skill2 = _make_skill("JavaScript")
        us1 = _make_user_skill(skill1, 2)
        us2 = _make_user_skill(skill2, 3)
        assert compute_user_difficulty_level([us1, us2], {skill1.id: skill1, skill2.id: skill2}) == "INTERMEDIATE"

    def test_advanced(self):
        skill1 = _make_skill("Python")
        skill2 = _make_skill("React")
        us1 = _make_user_skill(skill1, 4)
        us2 = _make_user_skill(skill2, 3)
        result = compute_user_difficulty_level([us1, us2], {skill1.id: skill1, skill2.id: skill2})
        assert result in ("ADVANCED", "INTERMEDIATE")

    def test_industry(self):
        skill1 = _make_skill("Python")
        skill2 = _make_skill("React")
        skill3 = _make_skill("AWS")
        us1 = _make_user_skill(skill1, 5)
        us2 = _make_user_skill(skill2, 5)
        us3 = _make_user_skill(skill3, 4)
        skills = {skill1.id: skill1, skill2.id: skill2, skill3.id: skill3}
        result = compute_user_difficulty_level([us1, us2, us3], skills)
        assert result in ("INDUSTRY", "ADVANCED")


class TestCareerRelevance:
    def test_perfect_overlap(self):
        project_skills = {"Python", "JavaScript"}
        required = {"Python", "JavaScript"}
        importance = {"Python": 1.0, "JavaScript": 1.0}
        score = _compute_career_relevance(project_skills, required, importance)
        assert score == 1.0

    def test_no_overlap(self):
        project_skills = {"Docker"}
        required = {"Python", "JavaScript"}
        score = _compute_career_relevance(project_skills, required, {})
        assert score == 0.0

    def test_partial_overlap_weighted(self):
        project_skills = {"Python"}
        required = {"Python", "JavaScript"}
        importance = {"Python": 1.0, "JavaScript": 0.5}
        score = _compute_career_relevance(project_skills, required, importance)
        assert 0.0 < score < 1.0
        assert score == 1.0 / 1.5

    def test_empty_required(self):
        score = _compute_career_relevance({"Python"}, set(), {})
        assert score == 0.0


class TestGapRelevance:
    def test_addresses_gap(self):
        project_skills = {"Python"}
        user_skill_map = {"Python": 1}
        importance = {"Python": 1.0}
        score = _compute_gap_relevance(project_skills, user_skill_map, importance)
        assert score > 0.5

    def test_no_gap(self):
        project_skills = {"Python"}
        user_skill_map = {"Python": 5}
        score = _compute_gap_relevance(project_skills, user_skill_map, {})
        assert score == 0.0

    def test_skill_not_known(self):
        project_skills = {"React"}
        user_skill_map = {}
        importance = {"React": 1.0}
        score = _compute_gap_relevance(project_skills, user_skill_map, importance)
        assert score == 1.0


class TestRoadmapRelevance:
    def test_active_phase_match(self):
        project_skills = {"Python"}
        roadmap_skills = {"Python", "JavaScript"}
        active_phase_skills = {"Python"}
        score = _compute_roadmap_relevance(project_skills, roadmap_skills, active_phase_skills)
        assert score == 1.0

    def test_roadmap_match(self):
        project_skills = {"Python"}
        roadmap_skills = {"Python", "JavaScript"}
        score = _compute_roadmap_relevance(project_skills, roadmap_skills, set())
        assert score > 0

    def test_no_roadmap(self):
        score = _compute_roadmap_relevance({"Python"}, set(), set())
        assert score == 0.3


class TestDifficultyFit:
    def test_perfect_match(self):
        assert _compute_difficulty_fit("BEGINNER", "BEGINNER") == 1.0
        assert _compute_difficulty_fit("ADVANCED", "ADVANCED") == 1.0

    def test_one_level_off(self):
        assert _compute_difficulty_fit("BEGINNER", "INTERMEDIATE") == 0.6
        assert _compute_difficulty_fit("INTERMEDIATE", "BEGINNER") == 0.6

    def test_two_levels_off(self):
        assert _compute_difficulty_fit("BEGINNER", "ADVANCED") == 0.2

    def test_three_levels_off(self):
        assert _compute_difficulty_fit("BEGINNER", "INDUSTRY") == 0.0


class TestHistoryPenalty:
    def test_new_project(self):
        pid = uuid4()
        score = _compute_history_penalty(pid, set(), set(), set())
        assert score == 1.0

    def test_completed_project(self):
        pid = uuid4()
        score = _compute_history_penalty(pid, set(), {str(pid)}, set())
        assert score == 0.0

    def test_in_progress_project(self):
        pid = uuid4()
        score = _compute_history_penalty(pid, set(), set(), {str(pid)})
        assert score == 0.8

    def test_already_recommended(self):
        pid = uuid4()
        score = _compute_history_penalty(pid, {pid}, set(), set())
        assert score == 0.5


class TestSkillGaps:
    def test_gap_calculation(self):
        user_skill_map = {"Python": 3}
        required = {"Python", "React"}
        importance = {"Python": 1.0, "React": 0.8}
        gaps = _get_skill_gaps(user_skill_map, required, importance)

        assert gaps["Python"] == 2 * 1.0
        assert gaps["React"] == 5 * 0.8

    def test_no_gap(self):
        gaps = _get_skill_gaps({"Python": 5}, {"Python"}, {"Python": 1.0})
        assert gaps["Python"] == 0


class TestRankSkillAwareProjects:
    def _make_db(self, user_skills, all_skills, career, projects,
                 recommended_projects=None, progress_items=None,
                 evidence_records=None, roadmap=None, phases=None):
        db = MagicMock()

        us_query = MagicMock()
        us_query.filter.return_value.all.return_value = user_skills

        skill_query = MagicMock()
        skill_query.all.return_value = all_skills

        career_query = MagicMock()
        career_query.filter.return_value.first.return_value = career

        project_query = MagicMock()
        project_query.all.return_value = projects

        rp_query = MagicMock()
        rp_query.filter.return_value.all.return_value = recommended_projects or []

        progress_query = MagicMock()
        progress_query.filter.return_value.all.return_value = progress_items or []

        evidence_query = MagicMock()
        evidence_query.filter.return_value.all.return_value = evidence_records or []

        roadmap_query = MagicMock()
        roadmap_query.filter.return_value.first.return_value = roadmap

        phase_query = MagicMock()
        phase_query.filter.return_value.all.return_value = phases or []

        def query_side_effect(model):
            name = getattr(model, "__name__", str(model))
            if name == "UserSkill":
                return us_query
            elif name == "Skill":
                return skill_query
            elif name == "Career":
                return career_query
            elif name == "Project":
                return project_query
            elif name == "RecommendedProject":
                return rp_query
            elif name == "UserProgress":
                return progress_query
            elif name == "SkillEvidence":
                return evidence_query
            elif name == "Roadmap":
                return roadmap_query
            elif name == "RoadmapPhase":
                return phase_query
            return MagicMock()

        db.query.side_effect = query_side_effect
        return db

    def test_returns_top_projects(self):
        skill1 = _make_skill("Python")
        skill2 = _make_skill("JavaScript")
        all_skills = [skill1, skill2]
        user_skills = [_make_user_skill(skill1, 1)]

        career = _make_career(
            required_skills=["Python", "JavaScript"],
            skill_importance={"Python": 1.0, "JavaScript": 0.8},
        )

        p1 = _make_project(title="Python API", skills_developed=["Python", "FastAPI"])
        p2 = _make_project(title="React App", skills_developed=["React", "JavaScript"])
        p3 = _make_project(title="Full Stack", skills_developed=["Python", "JavaScript"])

        db = self._make_db(user_skills, all_skills, career, [p1, p2, p3])
        results = rank_skill_aware_projects(db, uuid4(), career.id, top_n=3)

        assert len(results) == 3
        assert results[0]["composite_score"] >= results[1]["composite_score"]
        assert results[1]["composite_score"] >= results[2]["composite_score"]

    def test_gives_career_relevant_projects_higher_score(self):
        skill1 = _make_skill("Python")
        user_skills = [_make_user_skill(skill1, 1)]
        career = _make_career(
            required_skills=["Python"],
            skill_importance={"Python": 1.0},
        )

        p_relevant = _make_project(title="Python Project", skills_developed=["Python"])
        p_irrelevant = _make_project(title="Docker Project", skills_developed=["Docker"])

        db = self._make_db(user_skills, [skill1], career, [p_relevant, p_irrelevant])
        results = rank_skill_aware_projects(db, uuid4(), career.id)

        assert len(results) == 2
        assert results[0]["project"].title == "Python Project"

    def test_difficulty_fit_affects_score(self):
        skill1 = _make_skill("Python")
        user_skills = [_make_user_skill(skill1, 2)]
        career = _make_career(required_skills=["Python"])

        p_beginner = _make_project(title="Beginner", difficulty="beginner", skills_developed=["Python"])
        p_advanced = _make_project(title="Advanced", difficulty="advanced", skills_developed=["Python"])

        db = self._make_db(user_skills, [skill1], career, [p_beginner, p_advanced])
        results = rank_skill_aware_projects(db, uuid4(), career.id)

        assert len(results) == 2
        beginner_idx = next(i for i, r in enumerate(results) if r["project"].title == "Beginner")
        advanced_idx = next(i for i, r in enumerate(results) if r["project"].title == "Advanced")
        assert results[beginner_idx]["difficulty_fit"] >= results[advanced_idx]["difficulty_fit"]

    def test_empty_career_returns_empty(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        results = rank_skill_aware_projects(db, uuid4(), uuid4())
        assert results == []

    def test_no_projects_returns_empty(self):
        skill1 = _make_skill("Python")
        career = _make_career(required_skills=["Python"])
        db = self._make_db([], [skill1], career, [])
        results = rank_skill_aware_projects(db, uuid4(), career.id)
        assert results == []

    def test_completed_projects_penalized(self):
        skill1 = _make_skill("Python")
        user_skills = [_make_user_skill(skill1, 1)]
        career = _make_career(required_skills=["Python"])

        p1_id = uuid4()
        p1 = _make_project(project_id=p1_id, title="Done Project", skills_developed=["Python"])
        p2 = _make_project(title="New Project", skills_developed=["Python"])

        progress = [MagicMock(item_type="project", item_id=str(p1_id), status="completed")]

        db = self._make_db(user_skills, [skill1], career, [p1, p2], progress_items=progress)
        results = rank_skill_aware_projects(db, uuid4(), career.id)

        assert len(results) == 2
        new_idx = next(i for i, r in enumerate(results) if r["project"].title == "New Project")
        done_idx = next(i for i, r in enumerate(results) if r["project"].title == "Done Project")
        assert results[new_idx]["history_penalty"] > results[done_idx]["history_penalty"]

    def test_roadmap_aligned_projects_boosted(self):
        skill1 = _make_skill("Python")
        user_skills = [_make_user_skill(skill1, 1)]
        career = _make_career(required_skills=["Python"])

        p1 = _make_project(title="Roadmap Project", skills_developed=["Python"])
        p2 = _make_project(title="Other Project", skills_developed=["Docker"])

        phase = _make_phase(skills=["Python"], status="in_progress")
        roadmap = MagicMock()
        roadmap.id = uuid4()

        db = self._make_db(user_skills, [skill1], career, [p1, p2],
                          roadmap=roadmap, phases=[phase])
        results = rank_skill_aware_projects(db, uuid4(), career.id)

        assert len(results) == 2
        roadmap_idx = next(i for i, r in enumerate(results) if r["project"].title == "Roadmap Project")
        other_idx = next(i for i, r in enumerate(results) if r["project"].title == "Other Project")
        assert results[roadmap_idx]["roadmap_relevance"] >= results[other_idx]["roadmap_relevance"]

    def test_composite_score_components_sum_correctly(self):
        skill1 = _make_skill("Python")
        user_skills = [_make_user_skill(skill1, 1)]
        career = _make_career(required_skills=["Python"], skill_importance={"Python": 1.0})
        p = _make_project(title="Test", skills_developed=["Python"])

        db = self._make_db(user_skills, [skill1], career, [p])
        results = rank_skill_aware_projects(db, uuid4(), career.id)

        assert len(results) == 1
        r = results[0]
        expected = (
            r["career_relevance"] * 0.30
            + r["gap_relevance"] * 0.30
            + r["roadmap_relevance"] * 0.20
            + r["difficulty_fit"] * 0.15
            + r.get("history_penalty", 1.0) * 0.05
        )
        assert abs(r["composite_score"] - round(expected, 4)) < 0.01


class TestDifficultyProgression:
    def test_difficulty_levels_ordering(self):
        assert DIFFICULTY_LEVELS == ["BEGINNER", "INTERMEDIATE", "ADVANCED", "INDUSTRY"]
        assert DIFFICULTY_ORDER["BEGINNER"] < DIFFICULTY_ORDER["INTERMEDIATE"]
        assert DIFFICULTY_ORDER["INTERMEDIATE"] < DIFFICULTY_ORDER["ADVANCED"]
        assert DIFFICULTY_ORDER["ADVANCED"] < DIFFICULTY_ORDER["INDUSTRY"]

    def test_beginner_user_gets_beginner_projects(self):
        skill1 = _make_skill("Python")
        user_skills = [_make_user_skill(skill1, 1)]
        career = _make_career(required_skills=["Python"])

        p_beginner = _make_project(title="B", difficulty="beginner", skills_developed=["Python"])
        p_advanced = _make_project(title="A", difficulty="advanced", skills_developed=["Python"])

        db = MagicMock()
        us_q = MagicMock()
        us_q.filter.return_value.all.return_value = user_skills
        s_q = MagicMock()
        s_q.all.return_value = [skill1]
        c_q = MagicMock()
        c_q.filter.return_value.first.return_value = career
        p_q = MagicMock()
        p_q.all.return_value = [p_beginner, p_advanced]
        rp_q = MagicMock()
        rp_q.filter.return_value.all.return_value = []
        pr_q = MagicMock()
        pr_q.filter.return_value.all.return_value = []
        e_q = MagicMock()
        e_q.filter.return_value.all.return_value = []
        rm_q = MagicMock()
        rm_q.filter.return_value.first.return_value = None
        ph_q = MagicMock()
        ph_q.filter.return_value.all.return_value = []

        def query_side_effect(model):
            name = getattr(model, "__name__", str(model))
            mapping = {
                "UserSkill": us_q, "Skill": s_q, "Career": c_q,
                "Project": p_q, "RecommendedProject": rp_q,
                "UserProgress": pr_q, "SkillEvidence": e_q,
                "Roadmap": rm_q, "RoadmapPhase": ph_q,
            }
            return mapping.get(name, MagicMock())

        db.query.side_effect = query_side_effect
        results = rank_skill_aware_projects(db, uuid4(), career.id)

        assert len(results) == 2
        assert results[0]["user_difficulty"] == "BEGINNER"
        assert results[0]["difficulty_fit"] >= results[1]["difficulty_fit"]

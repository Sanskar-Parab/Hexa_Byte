import pytest
from uuid import uuid4, UUID
from unittest.mock import MagicMock
from datetime import datetime

from app.services.career_matching import (
    compute_career_recommendations,
    _compute_skill_score,
    _compute_interest_score,
    _compute_assessment_score,
    _compute_experience_score,
    _build_why_matches,
    _build_strengths,
    _build_missing_skills,
    _build_biggest_blocker,
    _build_recommended_action,
    _build_skill_details,
    _build_user_current_skills,
    WEIGHTS,
)


def _make_mock_skill(name, skill_id=None):
    s = MagicMock()
    s.id = skill_id or uuid4()
    s.name = name
    return s


def _make_mock_user_skill(skill, proficiency, confidence="LOW"):
    us = MagicMock()
    us.skill_id = skill.id
    us.proficiency = proficiency
    us.confidence = confidence
    return us


def _make_mock_interest(name, category, interest_id=None):
    i = MagicMock()
    i.id = interest_id or uuid4()
    i.name = name
    i.category = category
    return i


def _make_mock_user_interest(interest):
    ui = MagicMock()
    ui.interest_id = interest.id
    return ui


def _make_mock_career(name, required_skills, category="Software Development", optional_skills=None, skill_importance=None):
    c = MagicMock()
    c.id = uuid4()
    c.name = name
    c.required_skills = required_skills
    c.optional_skills = optional_skills or []
    c.category = category
    c.skill_importance = skill_importance or {}
    c.recommended_projects = []
    c.learning_sequence = []
    c.related_careers = []
    return c


def _make_mock_assessment(scores, created_at=None):
    a = MagicMock()
    a.id = uuid4()
    a.scores = scores
    a.created_at = created_at or datetime.utcnow()
    return a


def _make_mock_profile(internship="", work="", projects_count=0):
    p = MagicMock()
    p.internship_experience = internship
    p.work_experience = work
    p.projects_count = projects_count
    return p


class TestSkillScore:
    def test_perfect_match(self):
        skill1 = _make_mock_skill("Python")
        skill2 = _make_mock_skill("JavaScript")
        user_skills = [_make_mock_user_skill(skill1, 5), _make_mock_user_skill(skill2, 5)]
        career = _make_mock_career("Dev", ["Python", "JavaScript"])
        all_skills = {skill1.id: skill1, skill2.id: skill2}

        score = _compute_skill_score(user_skills, career, all_skills)
        assert score == 1.0

    def test_no_match(self):
        skill1 = _make_mock_skill("Python")
        user_skills = [_make_mock_user_skill(skill1, 5)]
        career = _make_mock_career("Dev", ["JavaScript", "React"])
        all_skills = {skill1.id: skill1}

        score = _compute_skill_score(user_skills, career, all_skills)
        assert score == 0.0

    def test_partial_match(self):
        skill1 = _make_mock_skill("Python")
        skill2 = _make_mock_skill("JavaScript")
        user_skills = [_make_mock_user_skill(skill1, 5), _make_mock_user_skill(skill2, 3)]
        career = _make_mock_career("Dev", ["Python", "JavaScript"])
        all_skills = {skill1.id: skill1, skill2.id: skill2}

        score = _compute_skill_score(user_skills, career, all_skills)
        expected = (1.0 + 0.6) / 2
        assert abs(score - expected) < 0.01

    def test_weighted_importance(self):
        skill1 = _make_mock_skill("Python")
        skill2 = _make_mock_skill("JavaScript")
        user_skills = [_make_mock_user_skill(skill1, 5), _make_mock_user_skill(skill2, 1)]
        career = _make_mock_career(
            "Dev", ["Python", "JavaScript"],
            skill_importance={"Python": 1.0, "JavaScript": 0.5},
        )
        all_skills = {skill1.id: skill1, skill2.id: skill2}

        score = _compute_skill_score(user_skills, career, all_skills)
        # Python (weight=1.0, proficiency=5) + JavaScript (weight=0.5, proficiency=1)
        # = (1.0*1.0 + 0.2*0.5) / (1.0 + 0.5) = 1.1/1.5 = 0.733
        assert score > 0.7

    def test_empty_required_skills(self):
        career = _make_mock_career("Dev", [])
        score = _compute_skill_score([], career, {})
        assert score == 0.0


class TestInterestScore:
    def test_matching_category(self):
        interest = _make_mock_interest("Web Dev", "Software Development")
        user_interests = [_make_mock_user_interest(interest)]
        career = _make_mock_career("Full Stack", [], category="Software Development")
        all_interests = {interest.id: interest}

        score = _compute_interest_score(user_interests, career, all_interests)
        assert score == 1.0

    def test_no_matching_category(self):
        interest = _make_mock_interest("Cooking", "Food")
        user_interests = [_make_mock_user_interest(interest)]
        career = _make_mock_career("Full Stack", [], category="Software Development")
        all_interests = {interest.id: interest}

        score = _compute_interest_score(user_interests, career, all_interests)
        assert score == 0.0

    def test_empty_interests(self):
        score = _compute_interest_score([], _make_mock_career("Dev", []), {})
        assert score == 0.0


class TestAssessmentScore:
    def test_high_scores_software(self):
        assessment = _make_mock_assessment({
            "technical_interest": 0.9,
            "problem_solving": 0.8,
            "analytical_ability": 0.7,
            "creativity": 0.5,
            "communication": 0.6,
            "technology_interest": 0.85,
            "business_interest": 0.4,
            "research_interest": 0.5,
        })
        career = _make_mock_career("Software Engineer", [], category="Software Development")
        score = _compute_assessment_score([assessment], career)
        assert score > 0.5

    def test_empty_assessment(self):
        score = _compute_assessment_score([], _make_mock_career("Dev", []))
        assert score == 0.5

    def test_data_scientist_category(self):
        assessment = _make_mock_assessment({
            "analytical_ability": 0.9,
            "problem_solving": 0.8,
            "technology_interest": 0.7,
            "research_interest": 0.85,
            "technical_interest": 0.7,
            "creativity": 0.5,
            "communication": 0.6,
            "business_interest": 0.4,
        })
        career = _make_mock_career("Data Scientist", [], category="Data Science")
        score = _compute_assessment_score([assessment], career)
        assert score > 0.6


class TestExperienceScore:
    def test_no_profile(self):
        score = _compute_experience_score(None)
        assert score == 0.2

    def test_empty_profile(self):
        profile = _make_mock_profile()
        score = _compute_experience_score(profile)
        assert score == 0.2

    def test_with_internship(self):
        profile = _make_mock_profile(internship="Tech Corp internship")
        score = _compute_experience_score(profile)
        assert score > 0.3

    def test_with_projects(self):
        profile = _make_mock_profile(projects_count=5)
        score = _compute_experience_score(profile)
        assert score > 0.4

    def test_full_experience(self):
        profile = _make_mock_profile(internship="Tech Corp", work="Google", projects_count=10)
        score = _compute_experience_score(profile)
        assert score >= 0.9


class TestWeightConfiguration:
    def test_weights_sum_to_one(self):
        total = sum(WEIGHTS.values())
        assert abs(total - 1.0) < 0.001


class TestBiggestBlocker:
    def test_identifies_highest_priority_gap(self):
        skill1 = _make_mock_skill("Python")
        skill2 = _make_mock_skill("Machine Learning")
        user_skills = [_make_mock_user_skill(skill1, 4)]
        career = _make_mock_career(
            "Data Scientist",
            ["Python", "Machine Learning"],
            skill_importance={"Python": 0.95, "Machine Learning": 0.9},
        )
        all_skills = {skill1.id: skill1, skill2.id: skill2}

        blocker = _build_biggest_blocker(user_skills, career, all_skills)
        assert blocker is not None
        assert "Machine Learning" in blocker

    def test_no_gaps_returns_none(self):
        skill1 = _make_mock_skill("Python")
        skill2 = _make_mock_skill("JavaScript")
        user_skills = [
            _make_mock_user_skill(skill1, 5),
            _make_mock_user_skill(skill2, 5),
        ]
        career = _make_mock_career("Dev", ["Python", "JavaScript"])
        all_skills = {skill1.id: skill1, skill2.id: skill2}

        blocker = _build_biggest_blocker(user_skills, career, all_skills)
        assert blocker is None

    def test_empty_required_skills(self):
        career = _make_mock_career("Dev", [])
        blocker = _build_biggest_blocker([], career, {})
        assert blocker is None


class TestRecommendedAction:
    def test_returns_first_learning_phase(self):
        skill1 = _make_mock_skill("Machine Learning")
        user_skills = [_make_mock_user_skill(skill1, 1)]
        career = _make_mock_career(
            "Data Scientist",
            ["Machine Learning"],
            skill_importance={"Machine Learning": 0.9},
        )
        career.learning_sequence = [
            {"title": "ML Basics", "skills": ["Machine Learning"], "objective": "Learn ML"},
            {"title": "Advanced ML", "skills": ["Deep Learning"], "objective": "Master ML"},
        ]
        all_skills = {skill1.id: skill1}

        action = _build_recommended_action(user_skills, career, all_skills)
        assert "ML Basics" in action

    def test_fallback_without_learning_sequence(self):
        skill1 = _make_mock_skill("React Native")
        user_skills = []
        career = _make_mock_career(
            "Mobile Developer",
            ["React Native"],
            skill_importance={"React Native": 0.9},
        )
        career.learning_sequence = []
        all_skills = {skill1.id: skill1}

        action = _build_recommended_action(user_skills, career, all_skills)
        assert "React Native" in action

    def test_no_gaps_message(self):
        skill1 = _make_mock_skill("Python")
        user_skills = [_make_mock_user_skill(skill1, 5)]
        career = _make_mock_career("Dev", ["Python"])
        all_skills = {skill1.id: skill1}

        action = _build_recommended_action(user_skills, career, all_skills)
        assert "all required skills" in action.lower() or "practical experience" in action.lower()


class TestEnhancedWhyMatches:
    def test_includes_strong_proficiency(self):
        skill1 = _make_mock_skill("Python")
        user_skills = [_make_mock_user_skill(skill1, 5)]
        career = _make_mock_career("Data Scientist", ["Python", "Machine Learning"])
        all_skills = {skill1.id: skill1}

        reasons = _build_why_matches(user_skills, career, all_skills)
        assert any("strong proficiency" in r.lower() for r in reasons)

    def test_includes_category_alignment(self):
        career = _make_mock_career("Dev", ["Python"], category="Software Development")
        reasons = _build_why_matches([], career, {})
        assert any("software development" in r.lower() for r in reasons)

    def test_includes_assessment_aptitude(self):
        skill1 = _make_mock_skill("Python")
        user_skills = [_make_mock_user_skill(skill1, 5)]
        career = _make_mock_career("Dev", ["Python"])
        all_skills = {skill1.id: skill1}

        reasons = _build_why_matches(user_skills, career, all_skills, assessment_score=0.8)
        assert any("assessment" in r.lower() for r in reasons)


class TestEnhancedStrengths:
    def test_sorted_by_weighted_proficiency(self):
        skill1 = _make_mock_skill("Python")
        skill2 = _make_mock_skill("JavaScript")
        user_skills = [
            _make_mock_user_skill(skill1, 4),
            _make_mock_user_skill(skill2, 5),
        ]
        career = _make_mock_career(
            "Dev",
            ["Python", "JavaScript"],
            skill_importance={"Python": 1.0, "JavaScript": 0.5},
        )
        all_skills = {skill1.id: skill1, skill2.id: skill2}

        strengths = _build_strengths(user_skills, career, all_skills)
        assert len(strengths) == 2
        assert "Python" in strengths[0]

    def test_includes_level_name(self):
        skill1 = _make_mock_skill("Python")
        user_skills = [_make_mock_user_skill(skill1, 4)]
        career = _make_mock_career("Dev", ["Python"])
        all_skills = {skill1.id: skill1}

        strengths = _build_strengths(user_skills, career, all_skills)
        assert len(strengths) == 1
        assert "Advanced" in strengths[0]


class TestSkillDetails:
    def test_computes_gap_and_status(self):
        skill1 = _make_mock_skill("Python")
        skill2 = _make_mock_skill("Machine Learning")
        user_skills = [
            _make_mock_user_skill(skill1, 4, "HIGH"),
            _make_mock_user_skill(skill2, 1, "LOW"),
        ]
        career = _make_mock_career(
            "Data Scientist",
            ["Python", "Machine Learning"],
            skill_importance={"Python": 0.95, "Machine Learning": 0.9},
        )
        all_skills = {skill1.id: skill1, skill2.id: skill2}

        details = _build_skill_details(user_skills, career, all_skills)
        assert len(details) == 2

        python_detail = next(d for d in details if d["skill_name"] == "Python")
        assert python_detail["gap"] == 1
        assert python_detail["status"] == "strong"
        assert python_detail["evidence_confidence"] == "HIGH"

        ml_detail = next(d for d in details if d["skill_name"] == "Machine Learning")
        assert ml_detail["gap"] == 4
        assert ml_detail["status"] == "gap"
        assert ml_detail["evidence_confidence"] == "LOW"

    def test_missing_skill_zero_proficiency(self):
        skill1 = _make_mock_skill("Python")
        user_skills = [_make_mock_user_skill(skill1, 5)]
        career = _make_mock_career("Dev", ["Python", "React"])
        all_skills = {skill1.id: skill1}

        details = _build_skill_details(user_skills, career, all_skills)
        react_detail = next(d for d in details if d["skill_name"] == "React")
        assert react_detail["user_proficiency"] == 0
        assert react_detail["evidence_confidence"] == "LOW"
        assert react_detail["status"] == "gap"


class TestUserCurrentSkills:
    def test_returns_only_career_skills(self):
        skill1 = _make_mock_skill("Python")
        skill2 = _make_mock_skill("Cooking")
        user_skills = [
            _make_mock_user_skill(skill1, 4, "HIGH"),
            _make_mock_user_skill(skill2, 5, "HIGH"),
        ]
        career = _make_mock_career("Dev", ["Python"])
        all_skills = {skill1.id: skill1, skill2.id: skill2}

        current = _build_user_current_skills(user_skills, career, all_skills)
        assert len(current) == 1
        assert current[0]["name"] == "Python"
        assert current[0]["proficiency"] == "4"
        assert current[0]["confidence"] == "HIGH"

    def test_sorted_by_proficiency(self):
        skill1 = _make_mock_skill("Python")
        skill2 = _make_mock_skill("JavaScript")
        user_skills = [
            _make_mock_user_skill(skill1, 3, "MEDIUM"),
            _make_mock_user_skill(skill2, 5, "HIGH"),
        ]
        career = _make_mock_career("Dev", ["Python", "JavaScript"])
        all_skills = {skill1.id: skill1, skill2.id: skill2}

        current = _build_user_current_skills(user_skills, career, all_skills)
        assert len(current) == 2
        assert current[0]["name"] == "JavaScript"
        assert current[1]["name"] == "Python"

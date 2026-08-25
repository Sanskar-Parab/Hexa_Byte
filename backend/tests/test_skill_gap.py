import pytest
from uuid import uuid4
from unittest.mock import MagicMock

from app.services.skill_gap import analyze_skill_gaps


def _make_mock_skill(name, skill_id=None):
    s = MagicMock()
    s.id = skill_id or uuid4()
    s.name = name
    return s


def _make_mock_user_skill(skill, proficiency):
    us = MagicMock()
    us.skill_id = skill.id
    us.proficiency = proficiency
    us.id = uuid4()
    return us


def _make_mock_career(required_skills, optional_skills=None, skill_importance=None):
    c = MagicMock()
    c.id = uuid4()
    c.required_skills = required_skills
    c.optional_skills = optional_skills or []
    c.skill_importance = skill_importance or {}
    c.name = "TestCareer"
    return c


def _make_db(user_skills, all_skills, career):
    """Create a properly mocked db that handles both filtered and unfiltered queries."""
    db = MagicMock()

    user_skill_query = MagicMock()
    user_skill_query.filter.return_value.all.return_value = user_skills

    skill_query = MagicMock()
    skill_query.all.return_value = all_skills

    career_query = MagicMock()
    career_query.filter.return_value.first.return_value = career

    def query_side_effect(model):
        name = getattr(model, "__name__", str(model))
        if name == "UserSkill":
            return user_skill_query
        elif name == "Skill":
            return skill_query
        elif name == "Career":
            return career_query
        return MagicMock()

    db.query.side_effect = query_side_effect
    return db


class TestSkillGapAnalysis:
    def test_all_skills_present(self):
        skill1 = _make_mock_skill("Python")
        skill2 = _make_mock_skill("JavaScript")
        user_skills = [_make_mock_user_skill(skill1, 5), _make_mock_user_skill(skill2, 4)]
        career = _make_mock_career(["Python", "JavaScript"])
        db = _make_db(user_skills, [skill1, skill2], career)

        result = analyze_skill_gaps(db, uuid4(), career.id)
        assert result["overall_gap_score"] < 1.0

    def test_no_skills_matched(self):
        skill1 = _make_mock_skill("Python")
        user_skills = [_make_mock_user_skill(skill1, 3)]
        career = _make_mock_career(["React", "Node.js"])
        db = _make_db(user_skills, [skill1], career)

        result = analyze_skill_gaps(db, uuid4(), career.id)
        assert result["overall_gap_score"] > 2.0

    def test_high_gap_detection(self):
        skill1 = _make_mock_skill("Python")
        user_skills = [_make_mock_user_skill(skill1, 1)]
        career = _make_mock_career(
            ["Python"],
            skill_importance={"Python": 1.0},
        )
        db = _make_db(user_skills, [skill1], career)

        result = analyze_skill_gaps(db, uuid4(), career.id)
        assert len(result["high_priority"]) == 1
        assert result["high_priority"][0]["gap_severity"] == "High"

    def test_medium_gap_detection(self):
        skill1 = _make_mock_skill("Python")
        user_skills = [_make_mock_user_skill(skill1, 3)]
        career = _make_mock_career(["Python"])
        db = _make_db(user_skills, [skill1], career)

        result = analyze_skill_gaps(db, uuid4(), career.id)
        assert len(result["medium_priority"]) == 1
        assert result["medium_priority"][0]["gap_severity"] == "Medium"

    def test_low_gap_detection(self):
        skill1 = _make_mock_skill("Python")
        user_skills = [_make_mock_user_skill(skill1, 5)]
        career = _make_mock_career(["Python"])
        db = _make_db(user_skills, [skill1], career)

        result = analyze_skill_gaps(db, uuid4(), career.id)
        assert len(result["low_priority"]) == 1
        assert result["low_priority"][0]["gap_severity"] == "Low"

    def test_gap_size_calculation(self):
        skill1 = _make_mock_skill("Python")
        user_skills = [_make_mock_user_skill(skill1, 2)]
        career = _make_mock_career(["Python"])
        db = _make_db(user_skills, [skill1], career)

        result = analyze_skill_gaps(db, uuid4(), career.id)
        gap = result["gaps"][0]
        assert gap["current_level"] == 2
        assert gap["target_level"] == 5
        assert gap["gap_size"] == 3

    def test_priority_scoring(self):
        skill1 = _make_mock_skill("Python")
        skill2 = _make_mock_skill("JavaScript")
        user_skills = [
            _make_mock_user_skill(skill1, 1),
            _make_mock_user_skill(skill2, 4),
        ]
        career = _make_mock_career(
            ["Python", "JavaScript"],
            skill_importance={"Python": 1.0, "JavaScript": 0.5},
        )
        db = _make_db(user_skills, [skill1, skill2], career)

        result = analyze_skill_gaps(db, uuid4(), career.id)
        assert result["gaps"][0]["priority_score"] > result["gaps"][1]["priority_score"]

    def test_optional_skills_included(self):
        skill1 = _make_mock_skill("Python")
        skill2 = _make_mock_skill("Docker")
        user_skills = [_make_mock_user_skill(skill1, 5)]
        career = _make_mock_career(
            required_skills=["Python"],
            optional_skills=["Docker"],
        )
        db = _make_db(user_skills, [skill1, skill2], career)

        result = analyze_skill_gaps(db, uuid4(), career.id)
        gap_skills = [g["skill"] for g in result["gaps"]]
        assert "Docker" in gap_skills

    def test_career_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = analyze_skill_gaps(db, uuid4(), uuid4())
        assert "error" in result

    def test_summary_counts(self):
        skill1 = _make_mock_skill("Python")
        skill2 = _make_mock_skill("JavaScript")
        skill3 = _make_mock_skill("React")
        user_skills = [_make_mock_user_skill(skill1, 1)]
        career = _make_mock_career(["Python", "JavaScript", "React"])
        db = _make_db(user_skills, [skill1, skill2, skill3], career)

        result = analyze_skill_gaps(db, uuid4(), career.id)
        total = result["summary"]["high_count"] + result["summary"]["medium_count"] + result["summary"]["low_count"]
        assert total == 3

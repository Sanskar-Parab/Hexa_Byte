import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.job_analysis_service import (
    parse_job_description,
    match_job_to_user,
    create_job_evidence,
    _extract_title,
    _extract_experience,
    _extract_education,
    _extract_technologies,
    _suggest_next_action,
    _match_requirement_to_skill,
)


class TestExtractTitle:
    def test_extracts_first_meaningful_line(self):
        lines = ["Software Engineer", "Posted 2 days ago", "Remote"]
        assert _extract_title(lines) == "Software Engineer"

    def test_skips_location_line(self):
        lines = ["Location: Remote", "Software Engineer", "Posted 2 days ago"]
        assert _extract_title(lines) == "Software Engineer"

    def test_returns_unknown_for_empty(self):
        assert _extract_title([]) == "Unknown Position"


class TestExtractExperience:
    def test_extracts_range(self):
        text = "Requirements: 3-5 years of experience"
        result = _extract_experience(text)
        assert result is not None
        assert "3" in result

    def test_extracts_single(self):
        text = "Minimum 5 years experience required"
        result = _extract_experience(text)
        assert result is not None
        assert "5" in result

    def test_returns_none_when_not_found(self):
        text = "We are a great company"
        assert _extract_experience(text) is None


class TestExtractEducation:
    def test_extracts_bachelor(self):
        text = "BS in Computer Science required"
        result = _extract_education(text)
        assert result is not None

    def test_extracts_master(self):
        text = "Master degree preferred"
        result = _extract_education(text)
        assert result is not None

    def test_returns_none_when_not_found(self):
        text = "We love engineers"
        assert _extract_education(text) is None


class TestExtractTechnologies:
    def test_extracts_known_tech(self):
        text = "Experience with React, Python, and AWS"
        result = _extract_technologies(text)
        assert "react" in result
        assert "python" in result
        assert "aws" in result

    def test_no_tech(self):
        text = "We are a great company with great culture"
        result = _extract_technologies(text)
        assert len(result) == 0

    def test_case_insensitive(self):
        text = "REACT and Python and docker"
        result = _extract_technologies(text)
        assert "react" in result
        assert "python" in result
        assert "docker" in result


class TestParseJobDescription:
    def test_extracts_title(self):
        text = "Software Engineer\n\nRequirements:\n- Python"
        result = parse_job_description(text)
        assert result["job_title"] == "Software Engineer"

    def test_extracts_required_skills(self):
        text = """Job Title
Requirements:
- Python experience
- React knowledge
- SQL proficiency"""
        result = parse_job_description(text)
        assert len(result["required_skills"]) > 0

    def test_extracts_preferred_skills(self):
        text = """Job Title
Requirements:
- Python
Nice to have:
- Docker
- Kubernetes"""
        result = parse_job_description(text)
        assert len(result["preferred_skills"]) > 0

    def test_extracts_responsibilities(self):
        text = """Job Title
Responsibilities:
- Build APIs
- Write tests
- Code review"""
        result = parse_job_description(text)
        assert len(result["responsibilities"]) > 0

    def test_extracts_technologies(self):
        text = """Job Title
Requirements:
- React, Python, AWS experience"""
        result = parse_job_description(text)
        assert "react" in result["technologies"]
        assert "python" in result["technologies"]

    def test_empty_text(self):
        result = parse_job_description("")
        assert result["required_skills"] == []
        assert result["preferred_skills"] == []


class TestMatchRequirementToSkill:
    def test_direct_match(self):
        user_map = {"python": {"skill_id": str(uuid4()), "proficiency": 4, "confidence": "HIGH"}}
        all_skills = {}
        skill = MagicMock()
        skill.name = "Python"
        all_skills[UUID(user_map["python"]["skill_id"])] = skill

        result = _match_requirement_to_skill("Python experience", user_map, all_skills)
        assert result is not None
        assert result["skill_name"] == "Python"

    def test_no_match(self):
        user_map = {"python": {"skill_id": str(uuid4()), "proficiency": 4, "confidence": "HIGH"}}
        all_skills = {}
        result = _match_requirement_to_skill("Docker knowledge", user_map, all_skills)
        assert result is None


from uuid import UUID


class TestSuggestNextAction:
    def test_suggests_project_for_missing(self):
        missing = [{"skill_name": "Docker"}]
        result = _suggest_next_action([], [], missing, [])
        assert "Docker" in result
        assert "project" in result.lower()

    def test_suggests_assessment_for_not_demonstrated(self):
        not_demo = [{"skill_name": "React"}]
        result = _suggest_next_action([], [], [], not_demo)
        assert "React" in result
        assert "assess" in result.lower()

    def test_suggests_advancement_for_developing(self):
        developing = [{"skill_name": "Python"}]
        result = _suggest_next_action([], developing, [], [])
        assert "Python" in result

    def test_well_qualified(self):
        result = _suggest_next_action(
            [{"skill_name": "Python"}], [], [], []
        )
        assert "well-qualified" in result.lower()


class TestMatchJobToUser:
    def _make_skill(name, skill_id=None):
        skill = MagicMock()
        skill.name = name
        skill.id = skill_id or uuid4()
        return skill

    def _make_user_skill(skill_id, proficiency, confidence="LOW"):
        us = MagicMock()
        us.skill_id = skill_id
        us.proficiency = proficiency
        us.confidence = confidence
        return us

    def _make_db(user_skills, all_skills, evidence):
        """Create a mock db that dispatches queries by model type."""
        from app.models.skill import Skill, UserSkill
        from app.models.skill_evidence import SkillEvidence

        db = MagicMock()

        def query_side_effect(model):
            mock_q = MagicMock()
            if model is UserSkill:
                mock_q.filter.return_value.all.return_value = user_skills
            elif model is Skill:
                # Skill.all() - no filter
                mock_q.all.return_value = all_skills
                mock_q.filter.return_value.all.return_value = all_skills
            elif model is SkillEvidence:
                mock_q.filter.return_value.all.return_value = evidence
            return mock_q

        db.query.side_effect = query_side_effect
        return db

    def test_strong_skills(self):
        skill = MagicMock()
        skill.name = "Python"
        skill_id = uuid4()
        skill.id = skill_id

        user_skill = TestMatchJobToUser._make_user_skill(skill_id, 5, "HIGH")
        db = TestMatchJobToUser._make_db([user_skill], [skill], [])

        job_data = {
            "job_title": "Python Developer",
            "required_skills": ["Python"],
        }

        result = match_job_to_user(db, uuid4(), job_data)
        assert len(result["strong_skills"]) == 1
        assert result["strong_skills"][0]["skill_name"] == "Python"
        assert result["strong_skills"][0]["status"] == "strong"

    def test_missing_skills(self):
        db = TestMatchJobToUser._make_db([], [], [])

        job_data = {
            "job_title": "Developer",
            "required_skills": ["Docker"],
        }

        result = match_job_to_user(db, uuid4(), job_data)
        assert len(result["missing_skills"]) == 1
        assert result["missing_skills"][0]["skill_name"] == "Docker"

    def test_alignment_percentage(self):
        skill = MagicMock()
        skill.name = "Python"
        skill_id = uuid4()
        skill.id = skill_id

        user_skill = TestMatchJobToUser._make_user_skill(skill_id, 5, "HIGH")
        db = TestMatchJobToUser._make_db([user_skill], [skill], [])

        job_data = {
            "job_title": "Dev",
            "required_skills": ["Python", "Docker"],
        }

        result = match_job_to_user(db, uuid4(), job_data)
        # Python = strong (1.0), Docker = missing (0.0) -> 50%
        assert result["alignment_percentage"] == 50.0

    def test_empty_requirements(self):
        db = TestMatchJobToUser._make_db([], [], [])

        job_data = {"job_title": "Dev", "required_skills": []}

        result = match_job_to_user(db, uuid4(), job_data)
        assert result["alignment_percentage"] == 0.0


class TestCreateJobEvidence:
    @patch("app.services.job_analysis_service.create_evidence")
    def test_creates_evidence_for_strong_skills(self, mock_create):
        db = MagicMock()
        skill = MagicMock()
        skill.name = "Python"
        db.query.return_value.filter.return_value.first.return_value = MagicMock()  # user_skill
        db.query.return_value.all.return_value = [skill]

        matched = [{"skill_name": "Python", "status": "strong", "user_proficiency": 5}]
        job_data = {"job_title": "Python Dev"}

        count = create_job_evidence(db, uuid4(), job_data, matched)
        assert count == 1
        mock_create.assert_called_once()

    @patch("app.services.job_analysis_service.create_evidence")
    def test_no_evidence_for_missing_skills(self, mock_create):
        db = MagicMock()
        db.query.return_value.all.return_value = []

        matched = [{"skill_name": "Docker", "status": "missing", "user_proficiency": 0}]
        job_data = {"job_title": "Dev"}

        count = create_job_evidence(db, uuid4(), job_data, matched)
        assert count == 0
        mock_create.assert_not_called()

    @patch("app.services.job_analysis_service.create_evidence")
    def test_creates_evidence_for_developing_skills(self, mock_create):
        db = MagicMock()
        skill = MagicMock()
        skill.name = "React"
        db.query.return_value.filter.return_value.first.return_value = MagicMock()
        db.query.return_value.all.return_value = [skill]

        matched = [{"skill_name": "React", "status": "developing", "user_proficiency": 2}]
        job_data = {"job_title": "Frontend Dev"}

        count = create_job_evidence(db, uuid4(), job_data, matched)
        assert count == 1

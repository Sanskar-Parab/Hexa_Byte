import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime

from app.services.resume_service import (
    parse_resume_text,
    extract_skills_from_text,
    _find_context,
)


class TestParseResumeText:
    def test_empty_text(self):
        result = parse_resume_text("")
        assert result["skills"] == []
        assert result["experience"] == []
        assert result["education"] == []

    def test_skills_section(self):
        text = "Skills\nPython\nJavaScript\nReact\nSQL"
        result = parse_resume_text(text)
        assert "Python" in result["skills"]
        assert "JavaScript" in result["skills"]
        assert "React" in result["skills"]
        assert "SQL" in result["skills"]

    def test_experience_section(self):
        text = "Experience\nSoftware Engineer at Google\nBuilt microservices"
        result = parse_resume_text(text)
        assert len(result["experience"]) > 0
        assert any("Software Engineer" in e for e in result["experience"])

    def test_education_section(self):
        text = "Education\nBS Computer Science, MIT"
        result = parse_resume_text(text)
        assert len(result["education"]) > 0
        assert any("MIT" in e for e in result["education"])

    def test_projects_section(self):
        text = "Projects\nE-commerce app with React\nChat application"
        result = parse_resume_text(text)
        assert len(result["projects"]) > 0

    def test_certifications_section(self):
        text = "Certifications\nAWS Certified Solutions Architect\nGoogle Cloud Professional"
        result = parse_resume_text(text)
        assert len(result["certifications"]) > 0

    def test_technologies_section(self):
        text = "Technologies\nDocker\nKubernetes\nAWS"
        result = parse_resume_text(text)
        assert len(result["technologies"]) > 0

    def test_tools_section(self):
        text = "Tools\nGit\nVS Code\nPostman"
        result = parse_resume_text(text)
        assert len(result["tools"]) > 0

    def test_bullet_points_cleaned(self):
        text = "Skills\n- Python\n* JavaScript\n• React"
        result = parse_resume_text(text)
        assert "Python" in result["skills"]
        assert "JavaScript" in result["skills"]
        assert "React" in result["skills"]

    def test_numbered_items_cleaned(self):
        text = "Skills\n1. Python\n2. JavaScript\n3. React"
        result = parse_resume_text(text)
        assert "Python" in result["skills"]
        assert "JavaScript" in result["skills"]

    def test_multiple_sections(self):
        text = """Skills
Python
JavaScript

Experience
Software Engineer at Meta

Education
BS Computer Science"""
        result = parse_resume_text(text)
        assert "Python" in result["skills"]
        assert "JavaScript" in result["skills"]
        assert len(result["experience"]) > 0
        assert len(result["education"]) > 0

    def test_overlong_lines_skipped(self):
        text = "Skills\nPython\n" + "x" * 300 + "\nJavaScript"
        result = parse_resume_text(text)
        assert "Python" in result["skills"]
        assert "JavaScript" in result["skills"]
        assert len(result["skills"]) == 2

    def test_case_insensitive_headers(self):
        text = "SKILLS\nPython\nJavaScript"
        result = parse_resume_text(text)
        assert "Python" in result["skills"]


class TestExtractSkillsFromText:
    def _make_skill(name, skill_id=None):
        skill = MagicMock()
        skill.name = name
        skill.id = skill_id or uuid4()
        return skill

    def test_matches_known_skill(self):
        skill = TestExtractSkillsFromText._make_skill("Python")
        text = "I have experience with Python and JavaScript"
        result = extract_skills_from_text(text, [skill])
        assert len(result) == 1
        assert result[0]["skill_name"] == "Python"

    def test_case_insensitive_match(self):
        skill = TestExtractSkillsFromText._make_skill("React")
        text = "Built apps with react and REACT"
        result = extract_skills_from_text(text, [skill])
        assert len(result) == 1

    def test_no_match(self):
        skill = TestExtractSkillsFromText._make_skill("Docker")
        text = "I know Python and JavaScript"
        result = extract_skills_from_text(text, [skill])
        assert len(result) == 0

    def test_multiple_matches(self):
        skills = [
            TestExtractSkillsFromText._make_skill("Python"),
            TestExtractSkillsFromText._make_skill("JavaScript"),
        ]
        text = "Proficient in Python and JavaScript"
        result = extract_skills_from_text(text, skills)
        assert len(result) == 2
        names = [r["skill_name"] for r in result]
        assert "Python" in names
        assert "JavaScript" in names

    def test_empty_text(self):
        skill = TestExtractSkillsFromText._make_skill("Python")
        result = extract_skills_from_text("", [skill])
        assert len(result) == 0

    def test_context_found(self):
        skill = TestExtractSkillsFromText._make_skill("Python")
        text = "Used Python for backend development"
        result = extract_skills_from_text(text, [skill])
        assert len(result) == 1
        assert "Python" in result[0]["context"]

    def test_empty_skills_list(self):
        result = extract_skills_from_text("Python and JavaScript", [])
        assert len(result) == 0


class TestFindContext:
    def test_finds_line_with_term(self):
        text = "Line one\nUsed Python for backend\nLine three"
        ctx = _find_context(text, "Python")
        assert "Python" in ctx

    def test_returns_default_when_not_found(self):
        text = "Line one\nLine two"
        ctx = _find_context(text, "Python")
        assert "mentioned" in ctx.lower()

    def test_truncates_long_lines(self):
        text = "Short line\n" + "x" * 200
        ctx = _find_context(text, "x" * 200)
        assert len(ctx) <= 160  # 150 + "..."

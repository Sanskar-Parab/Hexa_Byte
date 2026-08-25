import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.utils.auth import get_current_user


def _mock_user(user_id=None):
    user = MagicMock()
    user.id = user_id or uuid4()
    user.email = "test@test.com"
    user.name = "Test User"
    return user


@pytest.fixture(autouse=True)
def override_auth():
    """Override FastAPI dependency for all tests in this module."""
    user = _mock_user()
    app.dependency_overrides[get_current_user] = lambda: user
    yield
    app.dependency_overrides.clear()


class TestAnalyzeJob:
    def test_analyze_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post(
            "/api/job/analyze",
            json={"job_description": "Some job description"},
        )
        assert response.status_code in (401, 403)

    @patch("app.api.job_analysis.parse_job_description")
    @patch("app.api.job_analysis.match_job_to_user")
    @patch("app.api.job_analysis.create_job_evidence")
    @patch("app.api.job_analysis.save_job_analysis")
    def test_analyze_success(self, mock_save, mock_evidence, mock_match, mock_parse):
        mock_parse.return_value = {
            "job_title": "Python Developer",
            "required_skills": ["Python", "Docker"],
            "preferred_skills": ["Kubernetes"],
            "experience_required": "3+ years",
            "education_required": "BS in CS",
            "responsibilities": ["Build APIs"],
            "technologies": ["python", "docker"],
        }
        mock_match.return_value = {
            "alignment_percentage": 50.0,
            "strong_skills": [{"skill_name": "Python", "status": "strong", "user_proficiency": 5, "confidence": "HIGH", "evidence_count": 3, "is_required": True}],
            "developing_skills": [],
            "missing_skills": [{"skill_name": "Docker", "status": "missing", "user_proficiency": 0, "confidence": None, "evidence_count": 0, "is_required": True}],
            "not_demonstrated": [],
            "top_gap": "Docker",
            "next_action": "Build a project demonstrating Docker",
            "required_skills_count": 2,
            "matched_count": 1,
        }
        mock_evidence.return_value = 1
        mock_save.return_value = MagicMock(id=uuid4())

        client = TestClient(app)
        response = client.post(
            "/api/job/analyze",
            json={"job_description": "Python Developer\nRequirements:\n- Python\n- Docker"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["job_title"] == "Python Developer"
        assert data["alignment_percentage"] == 50.0
        assert len(data["strong_skills"]) == 1
        assert len(data["missing_skills"]) == 1
        assert data["top_gap"] == "Docker"
        assert data["evidence_created"] == 1

    def test_analyze_empty_description(self):
        client = TestClient(app)
        response = client.post(
            "/api/job/analyze",
            json={"job_description": ""},
        )
        assert response.status_code == 400


class TestJobHistory:
    def test_history_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get("/api/job/history")
        assert response.status_code in (401, 403)

    @patch("app.api.job_analysis.get_job_analyses_for_user")
    def test_history_returns_list(self, mock_list):
        mock_list.return_value = []
        client = TestClient(app)
        response = client.get("/api/job/history")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestDeleteJobAnalysis:
    def test_delete_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.delete(f"/api/job/{uuid4()}")
        assert response.status_code in (401, 403)

    @patch("app.api.job_analysis.delete_job_analysis")
    def test_delete_success(self, mock_delete):
        mock_delete.return_value = True
        client = TestClient(app)
        response = client.delete(f"/api/job/{uuid4()}")
        assert response.status_code == 200

    @patch("app.api.job_analysis.delete_job_analysis")
    def test_delete_not_found(self, mock_delete):
        mock_delete.return_value = False
        client = TestClient(app)
        response = client.delete(f"/api/job/{uuid4()}")
        assert response.status_code == 404

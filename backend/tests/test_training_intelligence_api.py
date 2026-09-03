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
    user = _mock_user()
    app.dependency_overrides[get_current_user] = lambda: user
    yield
    app.dependency_overrides.clear()


class TestSkillMatchApi:
    def test_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get(f"/api/outcomes/training/{uuid4()}/skill-match")
        assert response.status_code in (401, 403)

    @patch("app.api.training_intelligence.training_intelligence.compare_training_to_student_skills")
    def test_404_for_unknown_program(self, mock_compare):
        mock_compare.return_value = None
        client = TestClient(app)
        response = client.get(f"/api/outcomes/training/{uuid4()}/skill-match")
        assert response.status_code == 404

    @patch("app.api.training_intelligence.training_intelligence.compare_training_to_student_skills")
    def test_success(self, mock_compare):
        mock_compare.return_value = {
            "training_program_id": str(uuid4()),
            "training_program_name": "Full Stack Web Development",
            "skills_taught": ["JavaScript", "React", "Node.js"],
            "coverage_score": 55,
            "strong_skills": ["JavaScript"],
            "developing_skills": ["React"],
            "gap_skills": ["Node.js"],
            "skill_breakdown": [
                {"skill": "JavaScript", "user_proficiency": 4, "status": "strong"},
                {"skill": "React", "user_proficiency": 2, "status": "developing"},
                {"skill": "Node.js", "user_proficiency": 0, "status": "gap"},
            ],
        }
        client = TestClient(app)
        response = client.get(f"/api/outcomes/training/{uuid4()}/skill-match")
        assert response.status_code == 200
        data = response.json()
        assert data["strong_skills"] == ["JavaScript"]
        assert data["gap_skills"] == ["Node.js"]


class TestRelevanceApi:
    def test_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get(f"/api/outcomes/training/{uuid4()}/relevance")
        assert response.status_code in (401, 403)

    @patch("app.api.training_intelligence.outcome_service.get_training_program")
    def test_404_for_unknown_program(self, mock_get_program):
        mock_get_program.return_value = None
        client = TestClient(app)
        response = client.get(f"/api/outcomes/training/{uuid4()}/relevance")
        assert response.status_code == 404

    @patch("app.api.training_intelligence.outcome_service.get_employment_outcome")
    @patch("app.api.training_intelligence.outcome_service.get_training_program")
    def test_404_for_unowned_employment_outcome(self, mock_get_program, mock_get_outcome):
        mock_get_program.return_value = MagicMock(id=uuid4())
        mock_get_outcome.return_value = None
        client = TestClient(app)
        response = client.get(
            f"/api/outcomes/training/{uuid4()}/relevance",
            params={"employment_outcome_id": str(uuid4())},
        )
        assert response.status_code == 404

    @patch("app.api.training_intelligence.training_intelligence.calculate_training_relevance")
    @patch("app.api.training_intelligence.outcome_service.training_program_skill_names")
    @patch("app.api.training_intelligence.outcome_service.get_training_program")
    def test_success_without_employment_outcome(self, mock_get_program, mock_skill_names, mock_calc):
        mock_get_program.return_value = MagicMock(id=uuid4())
        mock_skill_names.return_value = ["JavaScript", "React", "Node.js"]
        mock_calc.return_value = {
            "level": "unknown",
            "reason": "No employment or job title information available to assess relevance.",
            "overlap_skills": [],
            "coverage_ratio": 0.0,
        }
        client = TestClient(app)
        response = client.get(f"/api/outcomes/training/{uuid4()}/relevance")
        assert response.status_code == 200
        assert response.json()["level"] == "unknown"


class TestPlacementReadinessApi:
    def test_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get("/api/outcomes/readiness")
        assert response.status_code in (401, 403)

    @patch("app.api.training_intelligence.training_intelligence.calculate_placement_readiness")
    def test_404_for_unowned_training_enrollment(self, mock_calc):
        mock_calc.return_value = None
        client = TestClient(app)
        response = client.get(
            "/api/outcomes/readiness", params={"training_enrollment_id": str(uuid4())}
        )
        assert response.status_code == 404

    @patch("app.api.training_intelligence.training_intelligence.calculate_placement_readiness")
    def test_success(self, mock_calc):
        mock_calc.return_value = {
            "readiness_score": 72.0,
            "is_ready": True,
            "breakdown": {"overall": 72.0},
            "resume_ready": True,
            "career": None,
            "skill_gap": None,
            "training": None,
            "why_ready": ["Technical skill proficiency is strong (80%)."],
            "what_is_missing": [],
            "recommended_action": "Keep building projects.",
        }
        client = TestClient(app)
        response = client.get("/api/outcomes/readiness")
        assert response.status_code == 200
        data = response.json()
        assert data["is_ready"] is True
        assert data["why_ready"]


class TestTrainingOpportunitiesApi:
    def test_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get("/api/outcomes/opportunities")
        assert response.status_code in (401, 403)

    @patch("app.api.training_intelligence.training_intelligence.get_opportunities_for_training")
    def test_404_for_unowned_enrollment(self, mock_get_opps):
        mock_get_opps.return_value = None
        client = TestClient(app)
        response = client.get(
            "/api/outcomes/opportunities", params={"training_enrollment_id": str(uuid4())}
        )
        assert response.status_code == 404

    @patch("app.api.training_intelligence.training_intelligence.get_opportunities_for_training")
    def test_success(self, mock_get_opps):
        mock_get_opps.return_value = {
            "recommendations": [],
            "user_skill_summary": {"skills_used": [], "skill_count": 0},
            "source_status": "ok",
            "message": None,
        }
        client = TestClient(app)
        response = client.get("/api/outcomes/opportunities")
        assert response.status_code == 200
        assert response.json()["source_status"] == "ok"

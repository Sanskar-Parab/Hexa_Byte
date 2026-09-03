import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.utils.auth import get_current_user
from app.schemas.outcome_ai import (
    NonPlacementAnalysisResponse,
    AttritionAnalysisResponse,
    TrainingRelevanceExplanationResponse,
    EvidenceItem,
)


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


class TestNonPlacementAnalysisApi:
    def test_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get("/api/outcomes/analysis/non-placement")
        assert response.status_code in (401, 403)

    @patch("app.api.outcome_ai.outcome_ai_analysis.analyze_non_placement")
    def test_404_for_unowned_training_enrollment(self, mock_analyze):
        mock_analyze.return_value = None
        client = TestClient(app)
        response = client.get(
            "/api/outcomes/analysis/non-placement",
            params={"training_enrollment_id": str(uuid4())},
        )
        assert response.status_code == 404

    @patch("app.api.outcome_ai.outcome_ai_analysis.analyze_non_placement")
    def test_success(self, mock_analyze):
        mock_analyze.return_value = NonPlacementAnalysisResponse(
            primary_reason="Technical readiness appears low.",
            supporting_evidence=["Technical skill proficiency is below target: 30%"],
            confidence="high",
            recommended_intervention="Complete a React Hooks project.",
            source="ai",
            evidence=[EvidenceItem(id="technical_skills", statement="Technical skill proficiency is below target: 30%")],
        )
        client = TestClient(app)
        response = client.get("/api/outcomes/analysis/non-placement")
        assert response.status_code == 200
        data = response.json()
        assert data["confidence"] == "high"
        assert data["source"] == "ai"


class TestAttritionAnalysisApi:
    def test_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get("/api/outcomes/analysis/attrition", params={"employment_outcome_id": str(uuid4())})
        assert response.status_code in (401, 403)

    def test_requires_employment_outcome_id(self):
        client = TestClient(app)
        response = client.get("/api/outcomes/analysis/attrition")
        assert response.status_code == 422

    @patch("app.api.outcome_ai.outcome_ai_analysis.analyze_attrition")
    def test_404_for_unowned_outcome(self, mock_analyze):
        """Ownership enforcement: an outcome id belonging to another user
        must never leak that user's attrition analysis."""
        mock_analyze.return_value = None
        client = TestClient(app)
        response = client.get(
            "/api/outcomes/analysis/attrition", params={"employment_outcome_id": str(uuid4())},
        )
        assert response.status_code == 404

    @patch("app.api.outcome_ai.outcome_ai_analysis.analyze_attrition")
    def test_success(self, mock_analyze):
        mock_analyze.return_value = AttritionAnalysisResponse(
            category="location",
            primary_reason="Relocation appears to be the reason.",
            supporting_evidence=["Self-reported reason for leaving: Relocated to a different city"],
            confidence="medium",
            recommended_intervention="Explore remote-friendly roles.",
            source="ai",
            evidence=[],
        )
        client = TestClient(app)
        response = client.get(
            "/api/outcomes/analysis/attrition", params={"employment_outcome_id": str(uuid4())},
        )
        assert response.status_code == 200
        assert response.json()["category"] == "location"


class TestRelevanceExplanationApi:
    def test_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get(
            "/api/outcomes/analysis/relevance-explanation", params={"training_program_id": str(uuid4())},
        )
        assert response.status_code in (401, 403)

    def test_requires_training_program_id(self):
        client = TestClient(app)
        response = client.get("/api/outcomes/analysis/relevance-explanation")
        assert response.status_code == 422

    @patch("app.api.outcome_ai.outcome_service.get_employment_outcome")
    def test_404_for_unowned_employment_outcome(self, mock_get_outcome):
        mock_get_outcome.return_value = None
        client = TestClient(app)
        response = client.get(
            "/api/outcomes/analysis/relevance-explanation",
            params={"training_program_id": str(uuid4()), "employment_outcome_id": str(uuid4())},
        )
        assert response.status_code == 404

    @patch("app.api.outcome_ai.outcome_ai_analysis.explain_training_relevance")
    def test_404_for_unknown_training_program(self, mock_explain):
        mock_explain.return_value = None
        client = TestClient(app)
        response = client.get(
            "/api/outcomes/analysis/relevance-explanation", params={"training_program_id": str(uuid4())},
        )
        assert response.status_code == 404

    @patch("app.api.outcome_ai.outcome_ai_analysis.explain_training_relevance")
    def test_success(self, mock_explain):
        mock_explain.return_value = TrainingRelevanceExplanationResponse(
            level="high",
            explanation="JavaScript and React both apply directly to this role.",
            overlap_skills=["JavaScript", "React"],
            coverage_ratio=0.67,
            source="ai",
        )
        client = TestClient(app)
        response = client.get(
            "/api/outcomes/analysis/relevance-explanation", params={"training_program_id": str(uuid4())},
        )
        assert response.status_code == 200
        assert response.json()["level"] == "high"

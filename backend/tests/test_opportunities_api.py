from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
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


SAMPLE_RESULT = {
    "recommendations": [
        {
            "id": "1",
            "title": "Frontend Developer Intern",
            "organization": "Acme Corp",
            "organization_url": "https://acme.example.com",
            "type": "internship",
            "url": "https://acme.example.com/careers/frontend-intern",
            "logo": None,
            "location": "Remote",
            "remote": True,
            "work_type": "INTERN",
            "seniority": "Internship",
            "salary": "15000",
            "posted_date": "2026-08-20T00:00:00.000Z",
            "valid_through": "2026-12-01T00:00:00.000Z",
            "source": "greenhouse",
            "source_domain": "greenhouse.io",
            "registration_open": True,
            "match_score": 92,
            "matched_skills": [{"skill": "JavaScript", "user_proficiency": 4, "requirement": "required"}],
            "partial_skills": [],
            "missing_skills": ["Node.js"],
            "why_match": ["Strong JavaScript proficiency (4/5)"],
            "skill_gap_message": "Learning Node.js would strengthen this match.",
            "recommendation": None,
        }
    ],
    "user_skill_summary": {"skills_used": ["JavaScript"], "skill_count": 1},
    "source_status": "ok",
    "message": None,
}


class TestOpportunityRecommendationsEndpoint:
    def test_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get("/api/opportunities/recommendations")
        assert response.status_code in (401, 403)

    def test_ignores_client_supplied_user_id(self):
        """The endpoint must never accept a user_id override — identity comes
        only from the authenticated JWT (Phase 20)."""
        client = TestClient(app)
        with patch("app.api.opportunities.get_recommendations", return_value=SAMPLE_RESULT) as mock_get:
            response = client.get("/api/opportunities/recommendations?user_id=some-other-user")
        assert response.status_code == 200
        called_kwargs = mock_get.call_args.kwargs
        assert "user_id" in called_kwargs
        # user_id passed to the service is the authenticated mock user, not the query string value.
        assert str(called_kwargs["user_id"]) != "some-other-user"

    def test_returns_recommendations(self):
        client = TestClient(app)
        with patch("app.api.opportunities.get_recommendations", return_value=SAMPLE_RESULT):
            response = client.get("/api/opportunities/recommendations?type=internship&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert data["recommendations"][0]["match_score"] == 92
        assert data["recommendations"][0]["missing_skills"] == ["Node.js"]
        assert data["user_skill_summary"]["skill_count"] == 1

    def test_invalid_type_rejected(self):
        client = TestClient(app)
        response = client.get("/api/opportunities/recommendations?type=banana")
        assert response.status_code == 422

    def test_graceful_unavailable_response(self):
        client = TestClient(app)
        unavailable = {
            "recommendations": [],
            "user_skill_summary": {"skills_used": [], "skill_count": 0},
            "source_status": "unavailable",
            "message": "Opportunities are temporarily unavailable. Please try again later.",
        }
        with patch("app.api.opportunities.get_recommendations", return_value=unavailable):
            response = client.get("/api/opportunities/recommendations")

        assert response.status_code == 200
        data = response.json()
        assert data["recommendations"] == []
        assert data["source_status"] == "unavailable"

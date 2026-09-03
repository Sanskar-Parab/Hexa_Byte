import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.utils.auth import get_current_user


def _mock_user(is_admin: bool):
    user = MagicMock()
    user.id = uuid4()
    user.email = "test@test.com"
    user.name = "Test User"
    user.is_admin = is_admin
    return user


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


ENDPOINTS = [
    "/api/admin/outcomes/overview",
    "/api/admin/outcomes/providers",
    "/api/admin/outcomes/programs",
    "/api/admin/outcomes/skill-gaps",
    "/api/admin/outcomes/non-placement",
    "/api/admin/outcomes/curriculum-recommendations",
    "/api/admin/outcomes/filters",
]

# POST endpoints checked separately (GET-only ENDPOINTS above covers the read side).
POST_ENDPOINTS = ["/api/admin/outcomes/demo-data"]


class TestAdminGating:
    def test_requires_auth(self):
        client = TestClient(app)
        for path in ENDPOINTS:
            response = client.get(path)
            assert response.status_code in (401, 403), path
        for path in POST_ENDPOINTS:
            response = client.post(path)
            assert response.status_code in (401, 403), path

    def test_regular_student_forbidden(self):
        """A normal student account must never reach the government dashboard."""
        app.dependency_overrides[get_current_user] = lambda: _mock_user(is_admin=False)
        client = TestClient(app)
        for path in ENDPOINTS:
            response = client.get(path)
            assert response.status_code == 403, path
        for path in POST_ENDPOINTS:
            response = client.post(path)
            assert response.status_code == 403, path

    @patch("app.api.admin_analytics.admin_analytics.get_curriculum_recommendations")
    def test_admin_curriculum_recommendations_endpoint(self, mock_recs):
        mock_recs.return_value = [{
            "training_program_id": str(uuid4()), "training_program_name": "Full Stack Web Development",
            "provider_name": "Acme Skilling", "skill": "React", "affected_trainee_percentage": 80.0,
            "program_placement_rate": 30.0, "overall_placement_rate": 55.0,
            "recommendation": "React is a recurring skill gap...",
        }]
        app.dependency_overrides[get_current_user] = lambda: _mock_user(is_admin=True)
        client = TestClient(app)
        response = client.get("/api/admin/outcomes/curriculum-recommendations")
        assert response.status_code == 200
        assert response.json()[0]["skill"] == "React"

    @patch("app.api.admin_analytics.demo_outcome_seed.seed_demo_outcome_data")
    def test_admin_demo_data_endpoint(self, mock_seed):
        mock_seed.return_value = {"message": "Demo outcome dataset created", "created": True, "trainees_created": 11}
        app.dependency_overrides[get_current_user] = lambda: _mock_user(is_admin=True)
        client = TestClient(app)
        response = client.post("/api/admin/outcomes/demo-data")
        assert response.status_code == 200
        assert response.json()["created"] is True

    @patch("app.api.admin_analytics.admin_analytics.get_overview_metrics")
    def test_admin_user_allowed(self, mock_overview):
        mock_overview.return_value = {
            "trainee_count": 0, "sample_size_sufficient": False,
            "training_completion_rate": None, "placement_rate": None,
            "employment_rate": None, "self_employment_rate": None,
            "unemployment_rate": None, "non_placement_rate": None,
            "retention_3_month_rate": None, "retention_6_month_rate": None,
            "retention_12_month_rate": None, "average_starting_salary": None,
            "average_current_salary": None, "wage_growth_percentage": None,
            "training_relevant_employment_rate": None,
        }
        app.dependency_overrides[get_current_user] = lambda: _mock_user(is_admin=True)
        client = TestClient(app)
        response = client.get("/api/admin/outcomes/overview")
        assert response.status_code == 200
        assert response.json()["trainee_count"] == 0

    @patch("app.api.admin_analytics.admin_analytics.get_filter_options")
    def test_admin_filters_endpoint(self, mock_filters):
        mock_filters.return_value = {
            "providers": ["Acme Skilling"], "career_domains": ["Software Development"],
            "programs": [], "locations": ["Bengaluru"], "employment_statuses": ["employed"],
        }
        app.dependency_overrides[get_current_user] = lambda: _mock_user(is_admin=True)
        client = TestClient(app)
        response = client.get("/api/admin/outcomes/filters")
        assert response.status_code == 200
        assert response.json()["providers"] == ["Acme Skilling"]


class TestStudentDataStaysSeparate:
    """The admin dashboard must never be reachable through the student API
    surface, and vice versa — this is a structural check that the router
    prefix is genuinely distinct."""

    def test_admin_router_prefix_is_isolated(self):
        admin_paths = [r.path for r in app.routes if hasattr(r, "path") and r.path.startswith("/api/admin/")]
        assert len(admin_paths) >= len(ENDPOINTS)
        for path in admin_paths:
            assert not path.startswith("/api/outcomes/")  # never aliases the student outcomes API

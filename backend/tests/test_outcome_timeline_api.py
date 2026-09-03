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
def current_user():
    user = _mock_user()
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides.clear()


class TestTimelineApi:
    def test_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get("/api/outcomes/timeline")
        assert response.status_code in (401, 403)

    @patch("app.api.outcome_timeline.build_outcome_timeline")
    def test_404_for_unowned_training_enrollment(self, mock_build):
        """Ownership enforcement: an enrollment id belonging to another user
        must never leak that user's timeline."""
        mock_build.return_value = None
        client = TestClient(app)
        response = client.get(
            "/api/outcomes/timeline", params={"training_enrollment_id": str(uuid4())}
        )
        assert response.status_code == 404

    @patch("app.api.outcome_timeline.build_outcome_timeline")
    def test_success_empty_shell(self, mock_build):
        mock_build.return_value = {
            "training": None,
            "placement": None,
            "employment": None,
            "check_ins": [],
            "milestones": {"3_month": None, "6_month": None, "12_month": None},
            "retention": {"3_month": "not_applicable", "6_month": "not_applicable", "12_month": "not_applicable"},
            "salary_progression": {"initial": None, "at_3_months": None, "at_6_months": None, "at_12_months": None, "changes": []},
            "training_relevance_over_time": [],
        }
        client = TestClient(app)
        response = client.get("/api/outcomes/timeline")
        assert response.status_code == 200
        data = response.json()
        assert data["training"] is None
        assert data["retention"]["3_month"] == "not_applicable"

    @patch("app.api.outcome_timeline.build_outcome_timeline")
    def test_never_passes_client_user_id(self, mock_build, current_user):
        """The timeline must always be built for the JWT-resolved user, never
        a client-supplied id — the endpoint has no user_id parameter, so even
        a spoofed one in the query string is silently ignored."""
        mock_build.return_value = {
            "training": None, "placement": None, "employment": None, "check_ins": [],
            "milestones": {}, "retention": {}, "salary_progression": {}, "training_relevance_over_time": [],
        }
        client = TestClient(app)
        spoofed_user_id = uuid4()
        client.get("/api/outcomes/timeline", params={"user_id": str(spoofed_user_id)})

        args, kwargs = mock_build.call_args
        passed_user_id = args[1] if len(args) > 1 else kwargs.get("user_id")
        assert passed_user_id == current_user.id
        assert passed_user_id != spoofed_user_id

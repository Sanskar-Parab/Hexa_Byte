import pytest
from uuid import uuid4
from datetime import datetime, date
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


class TestTrainingProgramApi:
    def test_create_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post("/api/outcomes/training", json={"name": "X", "provider_name": "Y"})
        assert response.status_code in (401, 403)

    @patch("app.services.outcome_service.training_program_skill_names")
    @patch("app.services.outcome_service.create_training_program")
    def test_create_success(self, mock_create, mock_skills):
        mock_create.return_value = MagicMock(
            id=uuid4(), provider_name="Y", description=None,
            career_domain=None, location=None, start_date=None, end_date=None,
            certification=None, status="active",
            created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
        )
        mock_create.return_value.name = "X"  # MagicMock(name=...) names the mock itself, not the attribute
        mock_skills.return_value = []
        client = TestClient(app)
        response = client.post("/api/outcomes/training", json={"name": "X", "provider_name": "Y"})
        assert response.status_code == 200
        assert response.json()["name"] == "X"

    def test_create_rejects_invalid_dates(self):
        client = TestClient(app)
        response = client.post(
            "/api/outcomes/training",
            json={
                "name": "X", "provider_name": "Y",
                "start_date": "2026-05-01", "end_date": "2026-04-01",
            },
        )
        assert response.status_code == 422

    def test_list_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get("/api/outcomes/training")
        assert response.status_code in (401, 403)


class TestEnrollmentApi:
    def test_create_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post("/api/outcomes/enrollment", json={"training_program_id": str(uuid4())})
        assert response.status_code in (401, 403)

    @patch("app.services.outcome_service.get_training_program")
    def test_create_rejects_unknown_program(self, mock_get):
        mock_get.return_value = None
        client = TestClient(app)
        response = client.post("/api/outcomes/enrollment", json={"training_program_id": str(uuid4())})
        assert response.status_code == 404

    @patch("app.services.outcome_service.get_training_program")
    @patch("app.services.outcome_service.create_enrollment")
    def test_create_success(self, mock_create, mock_get):
        mock_get.return_value = MagicMock(id=uuid4())
        mock_create.return_value = MagicMock(
            id=uuid4(), user_id=uuid4(), training_program_id=uuid4(),
            enrollment_date=date.today(), completion_date=None, status="enrolled",
            attendance_percentage=None, assessment_score=None, certificate_status=None,
            created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
        )
        client = TestClient(app)
        response = client.post("/api/outcomes/enrollment", json={"training_program_id": str(uuid4())})
        assert response.status_code == 200
        assert response.json()["status"] == "enrolled"

    def test_list_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get("/api/outcomes/enrollment")
        assert response.status_code in (401, 403)

    @patch("app.services.outcome_service.get_enrollment")
    def test_update_not_found_returns_404(self, mock_get):
        """Ownership enforcement: get_enrollment returns None for records the caller doesn't own."""
        mock_get.return_value = None
        client = TestClient(app)
        response = client.patch(f"/api/outcomes/enrollment/{uuid4()}", json={"status": "completed"})
        assert response.status_code == 404

    @patch("app.services.outcome_service.get_enrollment")
    @patch("app.services.outcome_service.update_enrollment")
    def test_update_success(self, mock_update, mock_get):
        mock_get.return_value = MagicMock(id=uuid4())
        mock_update.return_value = MagicMock(
            id=uuid4(), user_id=uuid4(), training_program_id=uuid4(),
            enrollment_date=date.today(), completion_date=date.today(), status="completed",
            attendance_percentage=95.0, assessment_score=90.0, certificate_status="issued",
            created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
        )
        client = TestClient(app)
        response = client.patch(f"/api/outcomes/enrollment/{uuid4()}", json={"status": "completed"})
        assert response.status_code == 200
        assert response.json()["status"] == "completed"


class TestEmploymentOutcomeApi:
    def test_create_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post("/api/outcomes/employment", json={})
        assert response.status_code in (401, 403)

    @patch("app.services.outcome_service.has_active_consent")
    def test_create_blocked_without_consent(self, mock_consent):
        mock_consent.return_value = False
        client = TestClient(app)
        response = client.post("/api/outcomes/employment", json={"employment_status": "placed"})
        assert response.status_code == 403

    @patch("app.services.outcome_service.has_active_consent")
    @patch("app.services.outcome_service.get_enrollment")
    def test_create_rejects_unowned_enrollment(self, mock_get_enrollment, mock_consent):
        mock_consent.return_value = True
        mock_get_enrollment.return_value = None
        client = TestClient(app)
        response = client.post(
            "/api/outcomes/employment",
            json={"employment_status": "placed", "training_enrollment_id": str(uuid4())},
        )
        assert response.status_code == 404

    @patch("app.services.outcome_service.has_active_consent")
    @patch("app.services.outcome_service.create_employment_outcome")
    def test_create_success_with_consent(self, mock_create, mock_consent):
        mock_consent.return_value = True
        mock_create.return_value = MagicMock(
            id=uuid4(), user_id=uuid4(), training_enrollment_id=None,
            employment_status="placed", employment_type=None, company_name=None,
            job_title=None, industry=None, location=None, country=None, is_remote=None,
            employment_start_date=None, employment_end_date=None, salary=None,
            salary_currency=None, salary_period=None, source="self_reported",
            source_opportunity_id=None, source_opportunity_title=None, verified=False,
            created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
        )
        client = TestClient(app)
        response = client.post("/api/outcomes/employment", json={"employment_status": "placed"})
        assert response.status_code == 200
        assert response.json()["employment_status"] == "placed"
        assert response.json()["verified"] is False

    def test_negative_salary_rejected(self):
        client = TestClient(app)
        response = client.post("/api/outcomes/employment", json={"salary": -500})
        assert response.status_code == 422

    def test_list_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get("/api/outcomes/employment")
        assert response.status_code in (401, 403)


class TestCheckInApi:
    def test_create_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post(
            "/api/outcomes/check-in",
            json={"employment_outcome_id": str(uuid4()), "employment_status": "employed"},
        )
        assert response.status_code in (401, 403)

    @patch("app.services.outcome_service.has_active_consent")
    def test_create_blocked_without_consent(self, mock_consent):
        mock_consent.return_value = False
        client = TestClient(app)
        response = client.post(
            "/api/outcomes/check-in",
            json={"employment_outcome_id": str(uuid4()), "employment_status": "employed"},
        )
        assert response.status_code == 403

    @patch("app.services.outcome_service.has_active_consent")
    @patch("app.services.outcome_service.get_employment_outcome")
    def test_create_rejects_unowned_outcome(self, mock_get, mock_consent):
        """Ownership enforcement: User A cannot check in against User B's employment outcome."""
        mock_consent.return_value = True
        mock_get.return_value = None
        client = TestClient(app)
        response = client.post(
            "/api/outcomes/check-in",
            json={"employment_outcome_id": str(uuid4()), "employment_status": "employed"},
        )
        assert response.status_code == 404

    @patch("app.services.outcome_service.has_active_consent")
    @patch("app.services.outcome_service.get_employment_outcome")
    @patch("app.services.outcome_service.create_check_in")
    def test_create_success(self, mock_create, mock_get, mock_consent):
        mock_consent.return_value = True
        mock_get.return_value = MagicMock(id=uuid4())
        mock_create.return_value = MagicMock(
            id=uuid4(), employment_outcome_id=uuid4(), check_in_date=date.today(),
            months_since_employment=3, employment_status="employed", company_name=None,
            job_title=None, salary=None, salary_currency=None, salary_period=None,
            training_relevance="high", still_employed=True, reason_for_leaving=None,
            notes=None, created_at=datetime.utcnow(),
        )
        client = TestClient(app)
        response = client.post(
            "/api/outcomes/check-in",
            json={"employment_outcome_id": str(uuid4()), "employment_status": "employed", "training_relevance": "high"},
        )
        assert response.status_code == 200
        assert response.json()["training_relevance"] == "high"

    def test_list_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get("/api/outcomes/check-ins")
        assert response.status_code in (401, 403)


class TestConsentApi:
    def test_get_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get("/api/outcomes/consent")
        assert response.status_code in (401, 403)

    @patch("app.services.outcome_service.get_consent")
    def test_get_defaults_to_not_consented(self, mock_get):
        mock_get.return_value = None
        client = TestClient(app)
        response = client.get("/api/outcomes/consent")
        assert response.status_code == 200
        assert response.json()["consented"] is False

    def test_post_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post("/api/outcomes/consent", json={"consented": True})
        assert response.status_code in (401, 403)

    @patch("app.services.outcome_service.set_consent")
    def test_post_consent(self, mock_set):
        mock_set.return_value = MagicMock(
            user_id=uuid4(), consented=True, consent_date=datetime.utcnow(), revoked_at=None,
        )
        client = TestClient(app)
        response = client.post("/api/outcomes/consent", json={"consented": True})
        assert response.status_code == 200
        assert response.json()["consented"] is True

    def test_post_consent_missing_field_rejected(self):
        client = TestClient(app)
        response = client.post("/api/outcomes/consent", json={})
        assert response.status_code == 422

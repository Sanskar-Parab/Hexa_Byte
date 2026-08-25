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


class TestUploadResume:
    def test_upload_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post(
            "/api/resume/upload",
            files={"file": ("test.pdf", b"fake content", "application/pdf")},
        )
        assert response.status_code in (401, 403)

    @patch("app.api.resume.extract_text_from_pdf")
    @patch("app.api.resume.parse_resume_text")
    @patch("app.api.resume.extract_skills_from_text")
    @patch("app.api.resume.save_resume_and_create_evidence")
    def test_upload_pdf_success(self, mock_save, mock_extract_skills, mock_parse, mock_pdf):
        mock_pdf.return_value = "Skills\nPython\nJavaScript"
        mock_parse.return_value = {
            "skills": ["Python", "JavaScript"],
            "projects": [],
            "experience": [],
            "education": [],
            "certifications": [],
            "technologies": [],
            "tools": [],
        }
        mock_extract_skills.return_value = [
            {"skill_name": "Python", "skill_id": str(uuid4()), "context": "Python in resume"},
        ]
        mock_save.return_value = MagicMock(id=uuid4())

        client = TestClient(app)
        response = client.post(
            "/api/resume/upload",
            files={"file": ("resume.pdf", b"fake pdf content", "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "resume_id" in data
        assert data["filename"] == "resume.pdf"
        assert data["evidence_created"] == 1

    def test_upload_rejects_non_pdf(self):
        client = TestClient(app)
        response = client.post(
            "/api/resume/upload",
            files={"file": ("resume.txt", b"fake content", "text/plain")},
        )
        assert response.status_code == 400

    def test_upload_rejects_empty_file(self):
        client = TestClient(app)
        response = client.post(
            "/api/resume/upload",
            files={"file": ("resume.pdf", b"", "application/pdf")},
        )
        assert response.status_code == 400


class TestListResumes:
    def test_list_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get("/api/resume")
        assert response.status_code in (401, 403)

    @patch("app.api.resume.get_resumes_for_user")
    def test_list_returns_resumes(self, mock_list):
        mock_list.return_value = []
        client = TestClient(app)
        response = client.get("/api/resume")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestDeleteResume:
    def test_delete_requires_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.delete(f"/api/resume/{uuid4()}")
        assert response.status_code in (401, 403)

    @patch("app.api.resume.delete_resume")
    def test_delete_success(self, mock_delete):
        mock_delete.return_value = True
        client = TestClient(app)
        response = client.delete(f"/api/resume/{uuid4()}")
        assert response.status_code == 200

    @patch("app.api.resume.delete_resume")
    def test_delete_not_found(self, mock_delete):
        mock_delete.return_value = False
        client = TestClient(app)
        response = client.delete(f"/api/resume/{uuid4()}")
        assert response.status_code == 404

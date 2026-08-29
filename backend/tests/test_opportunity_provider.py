from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services import opportunity_provider


@pytest.fixture(autouse=True)
def _clear_cache_and_configure(monkeypatch):
    opportunity_provider.clear_cache()
    monkeypatch.setenv("OPPORTUNITY_RAPIDAPI_KEY", "test-key")
    monkeypatch.setenv("OPPORTUNITY_RAPIDAPI_HOST", "internships-api.p.rapidapi.com")
    yield
    opportunity_provider.clear_cache()


def _mock_response(json_data, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=resp
        )
    else:
        resp.raise_for_status.return_value = None
    return resp


class TestIsConfigured:
    def test_not_configured_without_key(self, monkeypatch):
        monkeypatch.delenv("OPPORTUNITY_RAPIDAPI_KEY", raising=False)
        assert opportunity_provider.is_configured() is False

    def test_configured_with_key(self):
        assert opportunity_provider.is_configured() is True


class TestRequestFailureHandling:
    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("OPPORTUNITY_RAPIDAPI_KEY", raising=False)
        with pytest.raises(opportunity_provider.OpportunityProviderError):
            opportunity_provider.fetch_internships()

    def test_timeout_raises_provider_error_never_leaks_exception(self):
        with patch("httpx.get", side_effect=httpx.TimeoutException("timed out")):
            with pytest.raises(opportunity_provider.OpportunityProviderError):
                opportunity_provider.fetch_internships()

    def test_rate_limit_raises_provider_error(self):
        with patch("httpx.get", return_value=_mock_response({}, status_code=429)):
            with pytest.raises(opportunity_provider.OpportunityProviderError):
                opportunity_provider.fetch_internships()

    def test_http_error_raises_provider_error(self):
        with patch("httpx.get", return_value=_mock_response({}, status_code=500)):
            with pytest.raises(opportunity_provider.OpportunityProviderError):
                opportunity_provider.fetch_internships()

    def test_never_exposes_api_key_in_error_message(self):
        with patch("httpx.get", side_effect=httpx.TimeoutException("timed out")):
            try:
                opportunity_provider.fetch_internships()
            except opportunity_provider.OpportunityProviderError as e:
                assert "test-key" not in str(e)

    def test_sends_expected_headers_and_paths(self):
        with patch("httpx.get", return_value=_mock_response([])) as mock_get:
            opportunity_provider.fetch_internships()
        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs["headers"]["x-rapidapi-key"] == "test-key"
        assert call_kwargs["headers"]["x-rapidapi-host"] == "internships-api.p.rapidapi.com"
        assert call_kwargs["headers"]["Content-Type"] == "application/json"
        url = mock_get.call_args.args[0]
        assert url == "https://internships-api.p.rapidapi.com/active-jb-7d"

    def test_jobs_use_job_board_endpoint(self):
        with patch("httpx.get", return_value=_mock_response([])) as mock_get:
            opportunity_provider.fetch_jobs()
        url = mock_get.call_args.args[0]
        assert url == "https://internships-api.p.rapidapi.com/active-ats-7d"


class TestFetchAndExtractList:
    def test_fetch_handles_raw_list_response(self):
        payload = [{"id": 1, "title": "Backend Intern"}]
        with patch("httpx.get", return_value=_mock_response(payload)):
            items = opportunity_provider.fetch_internships()
        assert len(items) == 1

    def test_fetch_unwraps_data_key(self):
        payload = {"data": [{"id": 1, "title": "Frontend Intern"}]}
        with patch("httpx.get", return_value=_mock_response(payload)):
            items = opportunity_provider.fetch_internships()
        assert len(items) == 1
        assert items[0]["title"] == "Frontend Intern"

    def test_results_are_cached_between_calls(self):
        payload = [{"id": 1, "title": "Cached Intern"}]
        with patch("httpx.get", return_value=_mock_response(payload)) as mock_get:
            opportunity_provider.fetch_internships()
            opportunity_provider.fetch_internships()
        assert mock_get.call_count == 1

    def test_internships_and_jobs_cached_separately(self):
        with patch("httpx.get", return_value=_mock_response([])) as mock_get:
            opportunity_provider.fetch_internships()
            opportunity_provider.fetch_jobs()
        assert mock_get.call_count == 2


class TestNormalizeOpportunity:
    def test_minimal_valid_record(self):
        raw = {"id": "abc123", "title": "Web Dev Intern"}
        opp = opportunity_provider.normalize_opportunity(raw, "internship")
        assert opp["id"] == "abc123"
        assert opp["title"] == "Web Dev Intern"
        assert opp["organization"] == "Unknown Organization"
        assert opp["registration_open"] is True
        assert opp["required_skills"] == []
        assert opp["url"] is None

    def test_missing_id_or_title_returns_none(self):
        assert opportunity_provider.normalize_opportunity({"title": "No ID"}, "internship") is None
        assert opportunity_provider.normalize_opportunity({"id": 1}, "internship") is None

    def test_full_realistic_record(self):
        # Shape confirmed against the real Career Site API response.
        raw = {
            "id": "9f1c2b3a",
            "date_posted": "2026-08-20T10:00:00.000Z",
            "date_created": "2026-08-20T10:05:00.000Z",
            "title": "Frontend Engineering Intern",
            "organization": "Acme Robotics",
            "organization_url": "https://acme-robotics.example.com",
            "date_validthrough": "2026-12-01T00:00:00.000Z",
            "locations_derived": ["Bengaluru, India"],
            "location_type": "ON_SITE",
            "location_requirements_raw": "Bengaluru",
            "salary_raw": {"currency": "INR", "value": {"minValue": 15000, "maxValue": 25000, "unitText": "MONTH"}},
            "employment_type": ["INTERN"],
            "url": "https://acme-robotics.example.com/careers/frontend-intern",
            "source_type": "ats",
            "source": "greenhouse",
            "source_domain": "greenhouse.io",
            "organization_logo": "https://acme-robotics.example.com/logo.png",
            "remote_derived": False,
            "seniority": "Internship",
            "description": "Build UI features using React and TypeScript.",
        }
        opp = opportunity_provider.normalize_opportunity(raw, "internship")
        assert opp["organization"] == "Acme Robotics"
        assert opp["organization_url"] == "https://acme-robotics.example.com"
        assert opp["url"] == "https://acme-robotics.example.com/careers/frontend-intern"
        assert opp["logo"] == "https://acme-robotics.example.com/logo.png"
        assert opp["location"] == "Bengaluru, India"
        assert opp["remote"] is False
        assert opp["employment_type"] == "INTERN"
        assert opp["seniority"] == "Internship"
        assert opp["posted_date"] == "2026-08-20T10:00:00.000Z"
        assert opp["valid_through"] == "2026-12-01T00:00:00.000Z"
        assert opp["source"] == "greenhouse"
        assert opp["source_domain"] == "greenhouse.io"
        assert opp["salary"] == "INR 15000-25000/month"
        assert opp["registration_open"] is True

    def test_expired_valid_through_marks_closed(self):
        raw = {"id": 1, "title": "Expired Internship", "date_validthrough": "2020-01-01T00:00:00.000Z"}
        opp = opportunity_provider.normalize_opportunity(raw, "internship")
        assert opp["registration_open"] is False

    def test_missing_valid_through_stays_open(self):
        # We must never invent an expiry — absence means "still active".
        raw = {"id": 1, "title": "No Expiry Info"}
        opp = opportunity_provider.normalize_opportunity(raw, "internship")
        assert opp["registration_open"] is True

    def test_relative_or_non_http_url_is_rejected_not_guessed(self):
        raw = {"id": 1, "title": "Bad URL Posting", "url": "careers/some-job"}
        opp = opportunity_provider.normalize_opportunity(raw, "job")
        assert opp["url"] is None

    def test_location_falls_back_to_raw_schema_org_shape(self):
        raw = {
            "id": 1,
            "title": "Ops Intern",
            "locations_raw": [{"address": {"addressLocality": "Pune", "addressCountry": "IN"}}],
        }
        opp = opportunity_provider.normalize_opportunity(raw, "internship")
        assert opp["location"] == "Pune, IN"

    def test_employment_type_list_is_joined(self):
        raw = {"id": 1, "title": "Job", "employment_type": ["FULL_TIME", "CONTRACT"]}
        opp = opportunity_provider.normalize_opportunity(raw, "job")
        assert opp["employment_type"] == "FULL_TIME, CONTRACT"

    def test_no_required_skills_field_ever_present(self):
        raw = {"id": 1, "title": "Job", "description": "React, Node.js required."}
        opp = opportunity_provider.normalize_opportunity(raw, "job")
        assert opp["required_skills"] == []


class TestGetOpportunities:
    def test_dedupes_by_id(self):
        payload = [
            {"id": 1, "title": "Dup Internship", "url": "https://x.com/a"},
            {"id": 1, "title": "Dup Internship", "url": "https://x.com/a"},
        ]
        with patch("httpx.get", return_value=_mock_response(payload)):
            results = opportunity_provider.get_opportunities("internship")
        assert len(results) == 1

    def test_dedupes_by_url_when_ids_differ(self):
        payload = [
            {"id": 1, "title": "Cross-posted", "url": "https://x.com/same"},
            {"id": 2, "title": "Cross-posted", "url": "https://x.com/same"},
        ]
        with patch("httpx.get", return_value=_mock_response(payload)):
            results = opportunity_provider.get_opportunities("internship")
        assert len(results) == 1

    def test_filters_out_expired(self):
        payload = [
            {"id": 1, "title": "Active", "date_validthrough": "2099-01-01T00:00:00.000Z"},
            {"id": 2, "title": "Expired", "date_validthrough": "2020-01-01T00:00:00.000Z"},
        ]
        with patch("httpx.get", return_value=_mock_response(payload)):
            results = opportunity_provider.get_opportunities("internship")
        assert len(results) == 1
        assert results[0]["title"] == "Active"

    def test_propagates_provider_error_when_no_results_at_all(self):
        with patch("httpx.get", side_effect=httpx.TimeoutException("timed out")):
            with pytest.raises(opportunity_provider.OpportunityProviderError):
                opportunity_provider.get_opportunities("job")

    def test_exactly_one_upstream_call_per_type(self):
        with patch("httpx.get", return_value=_mock_response([])) as mock_get:
            opportunity_provider.get_opportunities("internship")
        assert mock_get.call_count == 1


class TestQuotaBackoff:
    def test_429_starts_backoff_and_short_circuits_next_call(self, monkeypatch):
        monkeypatch.setenv("OPPORTUNITY_QUOTA_BACKOFF_SECONDS", "60")
        with patch("httpx.get", return_value=_mock_response({}, status_code=429)) as mock_get:
            with pytest.raises(opportunity_provider.OpportunityProviderError):
                opportunity_provider.fetch_internships()
            assert mock_get.call_count == 1

            with pytest.raises(opportunity_provider.OpportunityProviderError):
                opportunity_provider.fetch_jobs()
            assert mock_get.call_count == 1

    def test_reset_quota_backoff_clears_cooldown(self, monkeypatch):
        monkeypatch.setenv("OPPORTUNITY_QUOTA_BACKOFF_SECONDS", "60")
        with patch("httpx.get", return_value=_mock_response({}, status_code=429)):
            with pytest.raises(opportunity_provider.OpportunityProviderError):
                opportunity_provider.fetch_internships()

        opportunity_provider.reset_quota_backoff()

        with patch("httpx.get", return_value=_mock_response([{"id": 1, "title": "Back online"}])) as mock_get:
            items = opportunity_provider.fetch_internships()
        assert len(items) == 1
        assert mock_get.call_count == 1

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services import opportunity_provider


@pytest.fixture(autouse=True)
def _clear_cache_and_configure(monkeypatch):
    opportunity_provider.clear_cache()
    monkeypatch.setenv("OPPORTUNITY_RAPIDAPI_KEY", "test-key")
    monkeypatch.setenv("OPPORTUNITY_RAPIDAPI_HOST", "jsearch.p.rapidapi.com")
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


def _envelope(jobs):
    """/search's documented envelope: `data` is a bare list."""
    return {"status": "OK", "request_id": "abc", "parameters": {}, "data": jobs}


def _envelope_v2(jobs):
    """/search-v2's live-confirmed envelope: `data` is `{"jobs": [...], "cursor": ...}`."""
    return {"status": "OK", "request_id": "abc", "parameters": {}, "data": {"jobs": jobs, "cursor": "xyz"}}


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
            opportunity_provider.search("frontend developer")

    def test_timeout_raises_provider_error_never_leaks_exception(self):
        with patch("httpx.get", side_effect=httpx.TimeoutException("timed out")):
            with pytest.raises(opportunity_provider.OpportunityProviderError):
                opportunity_provider.search("frontend developer")

    def test_rate_limit_raises_provider_error(self):
        with patch("httpx.get", return_value=_mock_response({}, status_code=429)):
            with pytest.raises(opportunity_provider.OpportunityProviderError):
                opportunity_provider.search("frontend developer")

    def test_http_error_raises_provider_error(self):
        with patch("httpx.get", return_value=_mock_response({}, status_code=500)):
            with pytest.raises(opportunity_provider.OpportunityProviderError):
                opportunity_provider.search("frontend developer")

    def test_never_exposes_api_key_in_error_message(self):
        with patch("httpx.get", side_effect=httpx.TimeoutException("timed out")):
            try:
                opportunity_provider.search("frontend developer")
            except opportunity_provider.OpportunityProviderError as e:
                assert "test-key" not in str(e)

    def test_sends_expected_headers_params_and_path(self):
        with patch("httpx.get", return_value=_mock_response(_envelope([]))) as mock_get:
            opportunity_provider.search("frontend developer")
        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs["headers"]["x-rapidapi-key"] == "test-key"
        assert call_kwargs["headers"]["x-rapidapi-host"] == "jsearch.p.rapidapi.com"
        assert call_kwargs["params"]["query"] == "frontend developer"
        assert call_kwargs["params"]["country"] == "in"
        url = mock_get.call_args.args[0]
        assert url == "https://jsearch.p.rapidapi.com/search-v2"

    def test_default_country_is_india(self):
        with patch("httpx.get", return_value=_mock_response(_envelope([]))) as mock_get:
            opportunity_provider.search("react developer")
        assert mock_get.call_args.kwargs["params"]["country"] == "in"

    def test_custom_country_and_paging_are_forwarded(self):
        with patch("httpx.get", return_value=_mock_response(_envelope([]))) as mock_get:
            opportunity_provider.search("react developer", country="us", date_posted="week", page=2, num_pages=1)
        params = mock_get.call_args.kwargs["params"]
        assert params["country"] == "us"
        assert params["date_posted"] == "week"
        assert params["page"] == "2"


class TestSearchAndExtractList:
    def test_search_unwraps_data_envelope(self):
        payload = _envelope([{"job_id": "1", "job_title": "Frontend Intern"}])
        with patch("httpx.get", return_value=_mock_response(payload)):
            items = opportunity_provider.search("frontend developer")
        assert len(items) == 1
        assert items[0]["job_title"] == "Frontend Intern"

    def test_search_unwraps_v2_jobs_cursor_envelope(self):
        """Live-confirmed shape (2026-08-31): /search-v2 nests results under data.jobs."""
        payload = _envelope_v2([{"job_id": "1", "job_title": "Frontend Intern"}])
        with patch("httpx.get", return_value=_mock_response(payload)):
            items = opportunity_provider.search("frontend developer")
        assert len(items) == 1
        assert items[0]["job_title"] == "Frontend Intern"

    def test_search_handles_raw_list_response(self):
        payload = [{"job_id": "1", "job_title": "Backend Intern"}]
        with patch("httpx.get", return_value=_mock_response(payload)):
            items = opportunity_provider.search("backend developer")
        assert len(items) == 1

    def test_malformed_response_returns_empty_list(self):
        with patch("httpx.get", return_value=_mock_response({"status": "OK"})):
            items = opportunity_provider.search("backend developer")
        assert items == []

    def test_results_are_cached_between_calls_for_same_query(self):
        payload = _envelope([{"job_id": "1", "job_title": "Cached Intern"}])
        with patch("httpx.get", return_value=_mock_response(payload)) as mock_get:
            opportunity_provider.search("frontend developer")
            opportunity_provider.search("frontend developer")
        assert mock_get.call_count == 1

    def test_different_queries_are_cached_separately(self):
        with patch("httpx.get", return_value=_mock_response(_envelope([]))) as mock_get:
            opportunity_provider.search("frontend developer")
            opportunity_provider.search("react developer")
        assert mock_get.call_count == 2


class TestClassifyOpportunityType:
    def test_intern_employment_types_list_classified_as_internship(self):
        """Live-confirmed (2026-08-31): job_employment_types is the clean enum
        list ["INTERN"]; this is the primary signal, not the singular field."""
        raw = {"job_title": "Software Engineer", "job_employment_types": ["INTERN"]}
        assert opportunity_provider.classify_opportunity_type(raw) == "internship"

    def test_garbled_singular_field_does_not_prevent_classification_when_list_present(self):
        """Live-confirmed: job_employment_type can carry a mangled encoding
        (e.g. "Full�time") — job_employment_types must take priority."""
        raw = {"job_title": "Frontend Role", "job_employment_type": "Internship", "job_employment_types": ["INTERN"]}
        assert opportunity_provider.classify_opportunity_type(raw) == "internship"

    def test_intern_employment_type_classified_as_internship(self):
        raw = {"job_title": "Software Engineer", "job_employment_type": "INTERN"}
        assert opportunity_provider.classify_opportunity_type(raw) == "internship"

    def test_intern_title_classified_as_internship(self):
        raw = {"job_title": "Frontend Developer Intern", "job_employment_type": "FULLTIME"}
        assert opportunity_provider.classify_opportunity_type(raw) == "internship"

    def test_internship_word_in_title_classified_as_internship(self):
        raw = {"job_title": "Machine Learning Internship", "job_employment_type": None}
        assert opportunity_provider.classify_opportunity_type(raw) == "internship"

    def test_ambiguous_posting_defaults_to_job_not_internship(self):
        raw = {"job_title": "International Business Analyst", "job_employment_type": "FULLTIME"}
        assert opportunity_provider.classify_opportunity_type(raw) == "job"

    def test_full_time_role_classified_as_job(self):
        raw = {"job_title": "Backend Engineer", "job_employment_type": "FULLTIME"}
        assert opportunity_provider.classify_opportunity_type(raw) == "job"


class TestNormalizeOpportunity:
    def test_minimal_valid_record(self):
        raw = {"job_id": "abc123", "job_title": "Web Dev Intern", "job_country": "IN"}
        opp = opportunity_provider.normalize_opportunity(raw)
        assert opp["id"] == "abc123"
        assert opp["title"] == "Web Dev Intern"
        assert opp["organization"] == "Unknown Organization"
        assert opp["type"] == "internship"
        assert opp["registration_open"] is True
        assert opp["required_skills"] == []
        assert opp["url"] is None

    def test_missing_id_or_title_returns_none(self):
        assert opportunity_provider.normalize_opportunity({"job_title": "No ID"}) is None
        assert opportunity_provider.normalize_opportunity({"job_id": "1"}) is None

    def test_non_india_country_is_rejected(self):
        raw = {"job_id": "1", "job_title": "Backend Engineer", "job_country": "US"}
        assert opportunity_provider.normalize_opportunity(raw) is None

    def test_missing_country_is_not_rejected(self):
        raw = {"job_id": "1", "job_title": "Backend Engineer"}
        assert opportunity_provider.normalize_opportunity(raw) is not None

    def test_full_realistic_record(self):
        raw = {
            "job_id": "9f1c2b3a",
            "job_title": "Frontend Engineering Intern",
            "employer_name": "Acme Robotics",
            "employer_website": "https://acme-robotics.example.com",
            "employer_logo": "https://acme-robotics.example.com/logo.png",
            "job_apply_link": "https://acme-robotics.example.com/careers/frontend-intern",
            "job_publisher": "LinkedIn",
            "job_description": "Build UI features using React and TypeScript.",
            "job_highlights": {"Qualifications": ["React", "TypeScript"], "Responsibilities": ["Ship features"]},
            "job_is_remote": False,
            "job_employment_type": "INTERN",
            "job_city": "Bengaluru",
            "job_state": "Karnataka",
            "job_country": "IN",
            "job_min_salary": 15000,
            "job_max_salary": 25000,
            "job_salary_currency": "INR",
            "job_salary_period": "MONTH",
            "job_posted_at_datetime_utc": "2026-08-20T10:00:00.000Z",
            "job_required_experience": {"required_experience_in_months": 0, "experience_mentioned": False},
            "job_required_skills": ["React", "TypeScript"],
        }
        opp = opportunity_provider.normalize_opportunity(raw)
        assert opp["organization"] == "Acme Robotics"
        assert opp["organization_url"] == "https://acme-robotics.example.com"
        assert opp["url"] == "https://acme-robotics.example.com/careers/frontend-intern"
        assert opp["logo"] == "https://acme-robotics.example.com/logo.png"
        assert opp["location"] == "Bengaluru, Karnataka, India"
        assert opp["remote"] is False
        assert opp["employment_type"] == "Internship"
        assert opp["type"] == "internship"
        assert opp["posted_date"] == "2026-08-20T10:00:00.000Z"
        assert opp["source"] == "LinkedIn"
        assert opp["source_domain"] == "acme-robotics.example.com"
        assert opp["salary"] == "INR 15000-25000/month"
        assert opp["required_skills"] == ["React", "TypeScript"]
        assert "Qualifications: React; TypeScript" in opp["description"]
        assert opp["registration_open"] is True

    def test_full_time_role_maps_employment_type_label(self):
        raw = {"job_id": "1", "job_title": "Backend Engineer", "job_employment_type": "FULLTIME"}
        opp = opportunity_provider.normalize_opportunity(raw)
        assert opp["employment_type"] == "Full Time"

    def test_employment_type_prefers_types_list_over_garbled_singular_field(self):
        raw = {
            "job_id": "1",
            "job_title": "Frontend Intern",
            "job_employment_type": "Full�time",
            "job_employment_types": ["INTERN"],
        }
        opp = opportunity_provider.normalize_opportunity(raw)
        assert opp["employment_type"] == "Internship"
        assert opp["type"] == "internship"

    def test_salary_string_fallback_when_no_structured_min_max(self):
        raw = {"job_id": "1", "job_title": "Job", "job_salary_string": "₹6-9 LPA"}
        opp = opportunity_provider.normalize_opportunity(raw)
        assert opp["salary"] == "₹6-9 LPA"

    def test_salary_number_fallback_with_currency_and_period(self):
        raw = {
            "job_id": "1",
            "job_title": "Job",
            "job_salary": 50000,
            "job_salary_currency": "INR",
            "job_salary_period": "MONTH",
        }
        opp = opportunity_provider.normalize_opportunity(raw)
        assert opp["salary"] == "INR 50000/month"

    def test_experience_required_produces_seniority_label(self):
        raw = {
            "job_id": "1",
            "job_title": "Senior Backend Engineer",
            "job_required_experience": {"required_experience_in_months": 60, "experience_mentioned": True},
        }
        opp = opportunity_provider.normalize_opportunity(raw)
        assert opp["seniority"] == "5+ years experience"
        assert opp["experience_years_required"] == 5.0

    def test_relative_or_non_http_apply_link_is_rejected_not_guessed(self):
        raw = {"job_id": "1", "job_title": "Bad URL Posting", "job_apply_link": "careers/some-job"}
        opp = opportunity_provider.normalize_opportunity(raw)
        assert opp["url"] is None

    def test_apply_url_falls_back_to_apply_options(self):
        raw = {
            "job_id": "1",
            "job_title": "Job With Apply Options",
            "apply_options": [{"publisher": "Indeed", "apply_link": "https://indeed.example.com/apply/1"}],
        }
        opp = opportunity_provider.normalize_opportunity(raw)
        assert opp["url"] == "https://indeed.example.com/apply/1"

    def test_remote_location_falls_back_when_no_city(self):
        raw = {"job_id": "1", "job_title": "Remote Job", "job_is_remote": True}
        opp = opportunity_provider.normalize_opportunity(raw)
        assert opp["location"] == "Remote"

    def test_no_salary_data_is_hidden_not_invented(self):
        raw = {"job_id": "1", "job_title": "No Salary Job"}
        opp = opportunity_provider.normalize_opportunity(raw)
        assert opp["salary"] is None

    def test_required_skills_absent_defaults_to_empty_list(self):
        raw = {"job_id": "1", "job_title": "Job", "job_description": "React, Node.js required."}
        opp = opportunity_provider.normalize_opportunity(raw)
        assert opp["required_skills"] == []


class TestGetOpportunities:
    def test_dedupes_by_job_id(self):
        payload = _envelope([
            {"job_id": "1", "job_title": "Dup Internship", "job_apply_link": "https://x.com/a"},
            {"job_id": "1", "job_title": "Dup Internship", "job_apply_link": "https://x.com/a"},
        ])
        with patch("httpx.get", return_value=_mock_response(payload)):
            results = opportunity_provider.get_opportunities("frontend developer")
        assert len(results) == 1

    def test_dedupes_by_apply_url_when_ids_differ(self):
        payload = _envelope([
            {"job_id": "1", "job_title": "Cross-posted", "job_apply_link": "https://x.com/same"},
            {"job_id": "2", "job_title": "Cross-posted", "job_apply_link": "https://x.com/same"},
        ])
        with patch("httpx.get", return_value=_mock_response(payload)):
            results = opportunity_provider.get_opportunities("frontend developer")
        assert len(results) == 1

    def test_dedupes_by_title_employer_location_fallback(self):
        payload = _envelope([
            {"job_id": "1", "job_title": "Backend Engineer", "employer_name": "Acme", "job_city": "Pune"},
            {"job_id": "2", "job_title": "Backend Engineer", "employer_name": "Acme", "job_city": "Pune"},
        ])
        with patch("httpx.get", return_value=_mock_response(payload)):
            results = opportunity_provider.get_opportunities("backend developer")
        assert len(results) == 1

    def test_non_india_results_are_filtered_out(self):
        payload = _envelope([
            {"job_id": "1", "job_title": "India Job", "job_country": "IN"},
            {"job_id": "2", "job_title": "US Job", "job_country": "US"},
        ])
        with patch("httpx.get", return_value=_mock_response(payload)):
            results = opportunity_provider.get_opportunities("developer")
        assert len(results) == 1
        assert results[0]["title"] == "India Job"

    def test_propagates_provider_error(self):
        with patch("httpx.get", side_effect=httpx.TimeoutException("timed out")):
            with pytest.raises(opportunity_provider.OpportunityProviderError):
                opportunity_provider.get_opportunities("developer")

    def test_exactly_one_upstream_call_per_query(self):
        with patch("httpx.get", return_value=_mock_response(_envelope([]))) as mock_get:
            opportunity_provider.get_opportunities("frontend developer")
        assert mock_get.call_count == 1


class TestQuotaBackoff:
    def test_429_starts_backoff_and_short_circuits_next_call(self, monkeypatch):
        monkeypatch.setenv("OPPORTUNITY_QUOTA_BACKOFF_SECONDS", "60")
        with patch("httpx.get", return_value=_mock_response({}, status_code=429)) as mock_get:
            with pytest.raises(opportunity_provider.OpportunityProviderError):
                opportunity_provider.search("frontend developer")
            assert mock_get.call_count == 1

            with pytest.raises(opportunity_provider.OpportunityProviderError):
                opportunity_provider.search("react developer")
            assert mock_get.call_count == 1

    def test_reset_quota_backoff_clears_cooldown(self, monkeypatch):
        monkeypatch.setenv("OPPORTUNITY_QUOTA_BACKOFF_SECONDS", "60")
        with patch("httpx.get", return_value=_mock_response({}, status_code=429)):
            with pytest.raises(opportunity_provider.OpportunityProviderError):
                opportunity_provider.search("frontend developer")

        opportunity_provider.reset_quota_backoff()

        with patch(
            "httpx.get",
            return_value=_mock_response(_envelope([{"job_id": "1", "job_title": "Back online"}])),
        ) as mock_get:
            items = opportunity_provider.search("frontend developer")
        assert len(items) == 1
        assert mock_get.call_count == 1

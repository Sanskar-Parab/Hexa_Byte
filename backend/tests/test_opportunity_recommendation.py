from unittest.mock import MagicMock, PropertyMock, patch
from uuid import uuid4

import pytest

from app.ai.groq_client import GroqAIClient
from app.models.skill import Skill, UserSkill
from app.services import opportunity_provider
from app.services import opportunity_recommendation as reco


def _ai_available(value: bool):
    return patch.object(GroqAIClient, "is_available", new_callable=PropertyMock, return_value=value)


@pytest.fixture(autouse=True)
def _clear_skill_extraction_cache():
    reco.clear_skill_extraction_cache()
    yield
    reco.clear_skill_extraction_cache()


def _make_skill(name):
    s = MagicMock()
    s.id = uuid4()
    s.name = name
    return s


def _make_user_skill(skill, proficiency):
    us = MagicMock()
    us.skill_id = skill.id
    us.proficiency = proficiency
    return us


def _make_db(user_skills, all_skills):
    db = MagicMock()

    def query_side_effect(model):
        q = MagicMock()
        if model is UserSkill:
            q.filter.return_value.all.return_value = user_skills
        elif model is Skill:
            q.all.return_value = all_skills
        else:
            q.filter.return_value.first.return_value = None
        return q

    db.query.side_effect = query_side_effect
    return db


def _sample_opportunity(opp_id="1", title="Frontend Developer Intern", required_skills=None):
    """Shape matches what opportunity_provider.get_opportunities() returns
    (already normalized) — this is the contract get_recommendations relies on."""
    return {
        "id": opp_id,
        "title": title,
        "organization": "Acme Corp",
        "organization_url": "https://acme.example.com",
        "type": "internship",
        "url": "https://acme.example.com/careers/1",
        "logo": None,
        "location": "Remote",
        "remote": True,
        "employment_type": "INTERN",
        "seniority": "Internship",
        "posted_date": "2026-08-20T00:00:00.000Z",
        "valid_through": "2026-12-01T00:00:00.000Z",
        "salary": "15000",
        "registration_open": True,
        "required_skills": required_skills if required_skills is not None else ["JavaScript", "React", "Node.js"],
        "description": "Build UI features using React.",
        "source": "greenhouse",
        "source_domain": "greenhouse.io",
    }


class TestGetUserSkillMap:
    def test_returns_empty_for_user_with_no_skills(self):
        db = _make_db([], [])
        result = reco.get_user_skill_map(db, uuid4())
        assert result == {}

    def test_maps_skill_name_to_proficiency(self):
        js = _make_skill("JavaScript")
        react = _make_skill("React")
        user_skills = [_make_user_skill(js, 4), _make_user_skill(react, 3)]
        db = _make_db(user_skills, [js, react])
        result = reco.get_user_skill_map(db, uuid4())
        assert result == {"JavaScript": 4, "React": 3}


class TestGetRecommendations:
    def test_empty_user_skill_profile_still_returns_opportunities(self):
        db = _make_db([], [])
        with patch.object(opportunity_provider, "get_opportunities", return_value=[_sample_opportunity()]), \
             _ai_available(False):
            result = reco.get_recommendations(db, uuid4(), opportunity_type="internship")

        assert result["source_status"] == "ok"
        assert len(result["recommendations"]) == 1
        assert result["recommendations"][0]["match_score"] == 0
        assert set(result["recommendations"][0]["missing_skills"]) == {"JavaScript", "React", "Node.js"}

    def test_response_carries_new_provider_fields(self):
        db = _make_db([], [])
        with patch.object(opportunity_provider, "get_opportunities", return_value=[_sample_opportunity()]), \
             _ai_available(False):
            result = reco.get_recommendations(db, uuid4(), opportunity_type="internship")

        rec = result["recommendations"][0]
        assert rec["organization_url"] == "https://acme.example.com"
        assert rec["remote"] is True
        assert rec["work_type"] == "INTERN"
        assert rec["seniority"] == "Internship"
        assert rec["posted_date"] == "2026-08-20T00:00:00.000Z"
        assert rec["valid_through"] == "2026-12-01T00:00:00.000Z"
        assert rec["source"] == "greenhouse"
        assert rec["source_domain"] == "greenhouse.io"

    def test_ranks_by_match_score_and_matches_via_aliases(self):
        js = _make_skill("JavaScript")
        react = _make_skill("React")
        git = _make_skill("Git")
        user_skills = [_make_user_skill(js, 4), _make_user_skill(react, 3), _make_user_skill(git, 3)]
        db = _make_db(user_skills, [js, react, git])

        strong_match = _sample_opportunity("1", "React Developer", ["JavaScript", "React", "Git"])
        weak_match = _sample_opportunity("2", "Sales Associate", ["Salesforce", "Negotiation"])

        with patch.object(opportunity_provider, "get_opportunities", return_value=[weak_match, strong_match]), \
             _ai_available(False):
            result = reco.get_recommendations(db, uuid4(), opportunity_type="internship")

        scores = {r["id"]: r["match_score"] for r in result["recommendations"]}
        assert scores["1"] > scores["2"]
        assert result["recommendations"][0]["id"] == "1"

    def test_min_match_filters_out_poor_matches(self):
        db = _make_db([], [])
        weak_match = _sample_opportunity("1", "Sales Associate", ["Salesforce"])
        with patch.object(opportunity_provider, "get_opportunities", return_value=[weak_match]), \
             _ai_available(False):
            result = reco.get_recommendations(db, uuid4(), opportunity_type="internship", min_match=50)

        assert result["recommendations"] == []

    def test_no_opportunities_available(self):
        db = _make_db([], [])
        with patch.object(opportunity_provider, "get_opportunities", return_value=[]):
            result = reco.get_recommendations(db, uuid4(), opportunity_type="internship")

        assert result["recommendations"] == []
        assert result["source_status"] == "ok"

    def test_provider_failure_degrades_gracefully(self):
        db = _make_db([], [])
        with patch.object(
            opportunity_provider, "get_opportunities",
            side_effect=opportunity_provider.OpportunityProviderError("boom"),
        ):
            result = reco.get_recommendations(db, uuid4(), opportunity_type="internship")

        assert result["recommendations"] == []
        assert result["source_status"] == "unavailable"
        assert "temporarily unavailable" in result["message"]
        assert "boom" not in result["message"]

    def test_partial_failure_keeps_data_from_the_type_that_succeeded(self):
        """type=all where internships succeed but jobs fail must still return
        the internship recommendations — not blank the whole response."""
        js = _make_skill("JavaScript")
        user_skills = [_make_user_skill(js, 4)]
        db = _make_db(user_skills, [js])

        opp = _sample_opportunity("1", "JS Developer", ["JavaScript"])

        def side_effect(otype):
            if otype == "internship":
                return [opp]
            raise opportunity_provider.OpportunityProviderError("jobs down")

        with patch.object(opportunity_provider, "get_opportunities", side_effect=side_effect), \
             _ai_available(False):
            result = reco.get_recommendations(db, uuid4(), opportunity_type="all")

        assert result["source_status"] == "ok"
        assert len(result["recommendations"]) == 1
        assert result["message"] is not None
        assert "temporarily unavailable" in result["message"].lower()

    def test_ai_failure_falls_back_to_deterministic_score(self):
        js = _make_skill("JavaScript")
        user_skills = [_make_user_skill(js, 4)]
        db = _make_db(user_skills, [js])

        opp = _sample_opportunity("1", "JS Developer", ["JavaScript"])
        with patch.object(opportunity_provider, "get_opportunities", return_value=[opp]), \
             _ai_available(True), \
             patch.object(GroqAIClient, "analyze_opportunity_match", return_value=(None, "AI error")):
            result = reco.get_recommendations(db, uuid4(), opportunity_type="internship")

        assert len(result["recommendations"]) == 1
        # Proficiency 4/5 -> deterministic weight 0.9 -> 90/100; AI failure means
        # the deterministic score is used as-is, unblended.
        assert result["recommendations"][0]["match_score"] == 90

    def test_ai_score_blended_with_deterministic_score(self):
        js = _make_skill("JavaScript")
        user_skills = [_make_user_skill(js, 4)]
        db = _make_db(user_skills, [js])

        opp = _sample_opportunity("1", "JS Developer", ["JavaScript"])
        ai_result = MagicMock(match_score=50, why_match=["contextual reason"], recommendation="Good fit")

        with patch.object(opportunity_provider, "get_opportunities", return_value=[opp]), \
             _ai_available(True), \
             patch.object(GroqAIClient, "analyze_opportunity_match", return_value=(ai_result, None)):
            result = reco.get_recommendations(db, uuid4(), opportunity_type="internship")

        # deterministic=100, ai=50 -> weighted blend strictly between the two
        score = result["recommendations"][0]["match_score"]
        assert 50 < score < 100

    def test_ai_cannot_arbitrarily_make_unrelated_opportunity_high_match(self):
        """An opportunity requiring skills the user has none of must stay at
        a low final score even if the AI (mocked here as buggy/adversarial)
        tries to report a high match. In practice AI analysis is only invoked
        for opportunities with a nonzero deterministic score in the first
        place, so a fully unrelated opportunity never even reaches the AI —
        which is itself the strongest guarantee against AI overriding a
        "no real skill overlap" verdict."""
        js = _make_skill("JavaScript")
        user_skills = [_make_user_skill(js, 4)]
        db = _make_db(user_skills, [js])

        unrelated = _sample_opportunity("1", "Mechanical Engineering Intern", ["AutoCAD", "SolidWorks"])
        ai_result = MagicMock(match_score=95, why_match=["seems great"], recommendation="Great fit")

        with patch.object(opportunity_provider, "get_opportunities", return_value=[unrelated]), \
             _ai_available(True), \
             patch.object(GroqAIClient, "analyze_opportunity_match", return_value=(ai_result, None)) as mock_ai:
            result = reco.get_recommendations(db, uuid4(), opportunity_type="internship")

        assert result["recommendations"][0]["match_score"] == 0
        mock_ai.assert_not_called()

    def test_fetches_exactly_once_per_type_no_call_multiplication(self):
        """Regression guard: a previous provider integration issued extra
        role-discovery + per-role fan-out requests (up to ~10 calls for one
        page load), which exhausted a tiny RapidAPI quota. Must stay at
        exactly one upstream call per type per request."""
        js = _make_skill("JavaScript")
        user_skills = [_make_user_skill(js, 4)]
        db = _make_db(user_skills, [js])

        with patch.object(opportunity_provider, "get_opportunities", return_value=[]) as mock_fetch, \
             _ai_available(False):
            reco.get_recommendations(db, uuid4(), opportunity_type="all")

        assert mock_fetch.call_count == 2  # once for "internship", once for "job"
        called_types = {call.args[0] for call in mock_fetch.call_args_list}
        assert called_types == {"internship", "job"}

    def test_single_type_fetches_exactly_once(self):
        db = _make_db([], [])
        with patch.object(opportunity_provider, "get_opportunities", return_value=[]) as mock_fetch:
            reco.get_recommendations(db, uuid4(), opportunity_type="internship")
        assert mock_fetch.call_count == 1

    def test_skill_extraction_is_cached_across_requests(self):
        """This provider never supplies required_skills, so extraction falls
        back to Groq per posting. Two separate requests for the same
        opportunity must not call Groq twice for it."""
        db = _make_db([], [])
        opp = _sample_opportunity("1", "Backend Intern", required_skills=[])

        with patch.object(opportunity_provider, "get_opportunities", return_value=[opp]), \
             _ai_available(True), \
             patch.object(GroqAIClient, "extract_skills_from_text", return_value=(["Python"], None)) as mock_extract:
            reco.get_recommendations(_make_db([], []), uuid4(), opportunity_type="internship")
            reco.get_recommendations(_make_db([], []), uuid4(), opportunity_type="internship")

        mock_extract.assert_called_once()

    def test_skill_extraction_budget_caps_new_groq_calls_per_request(self):
        """Many opportunities with no skills field must not each trigger a
        Groq call unboundedly — that would be one uncontrolled AI call per
        posting on every request."""
        opportunities = [
            _sample_opportunity(str(i), f"Role {i}", required_skills=[])
            for i in range(reco.MAX_SKILL_EXTRACTIONS_PER_REQUEST + 5)
        ]
        db = _make_db([], [])

        with patch.object(opportunity_provider, "get_opportunities", return_value=opportunities), \
             _ai_available(True), \
             patch.object(GroqAIClient, "extract_skills_from_text", return_value=([], None)) as mock_extract:
            reco.get_recommendations(db, uuid4(), opportunity_type="internship", limit=50)

        assert mock_extract.call_count == reco.MAX_SKILL_EXTRACTIONS_PER_REQUEST

    def test_expired_opportunities_excluded_by_provider_layer(self):
        db = _make_db([], [])
        # get_opportunities is responsible for filtering expired opportunities;
        # the recommendation service trusts that contract.
        with patch.object(opportunity_provider, "get_opportunities", return_value=[]):
            result = reco.get_recommendations(db, uuid4(), opportunity_type="internship")
        assert result["recommendations"] == []

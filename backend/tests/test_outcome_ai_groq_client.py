import json
from unittest.mock import MagicMock

from app.ai.groq_client import GroqAIClient


def _client_with_mocked_response(content: str) -> GroqAIClient:
    client = GroqAIClient()
    client._client = MagicMock()
    # `is_available` lazily calls `_ensure_initialized()`, which would
    # otherwise clobber this mock with a real `groq.Groq` client the moment
    # GROQ_API_KEY is present in the environment.
    client._initialized = True
    client._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=content))]
    )
    return client


def _unavailable_client() -> GroqAIClient:
    client = GroqAIClient()
    client._client = None
    client._initialized = True
    client._error_message = "AI assessment unavailable: GROQ_API_KEY not configured"
    return client


SAMPLE_EVIDENCE = [
    {"id": "readiness_score", "statement": "Overall placement readiness score: 42%"},
    {"id": "technical_skills", "statement": "Technical skill proficiency is below target: 35%"},
]


class TestAnalyzeNonPlacement:
    def test_valid_output(self):
        client = _client_with_mocked_response(json.dumps({
            "primary_reason": "Technical readiness appears to be the main barrier.",
            "supporting_evidence_ids": ["readiness_score", "technical_skills"],
            "recommended_intervention": "Complete a React Hooks project to build demonstrated proficiency.",
        }))
        result, error = client.analyze_non_placement(SAMPLE_EVIDENCE, target_career="Frontend Developer")
        assert error is None
        assert result.primary_reason == "Technical readiness appears to be the main barrier."
        assert result.supporting_evidence_ids == ["readiness_score", "technical_skills"]
        assert "React Hooks" in result.recommended_intervention

    def test_invalid_json_returns_error(self):
        client = _client_with_mocked_response("This is not JSON at all, just prose explaining things.")
        result, error = client.analyze_non_placement(SAMPLE_EVIDENCE, target_career=None)
        assert result is None
        assert error is not None

    def test_missing_required_fields_returns_error(self):
        """An empty primary_reason (or intervention) is treated as an
        unusable response, not silently accepted as valid."""
        client = _client_with_mocked_response(json.dumps({
            "primary_reason": "",
            "supporting_evidence_ids": ["readiness_score"],
            "recommended_intervention": "",
        }))
        result, error = client.analyze_non_placement(SAMPLE_EVIDENCE, target_career=None)
        assert result is None
        assert error is not None

    def test_ai_unavailable(self):
        client = _unavailable_client()
        result, error = client.analyze_non_placement(SAMPLE_EVIDENCE, target_career=None)
        assert result is None
        assert error is not None

    def test_ignores_hallucinated_looking_extra_fields(self):
        """Any extra keys the model adds (e.g. a fabricated 'confidence') are
        simply ignored — the pydantic schema only extracts the fields it declares."""
        client = _client_with_mocked_response(json.dumps({
            "primary_reason": "Skill gap appears to be a barrier.",
            "supporting_evidence_ids": ["technical_skills"],
            "recommended_intervention": "Build a project.",
            "confidence": "extremely high",  # not part of the schema
            "made_up_fact": "This user was rejected 5 times",  # never trusted
        }))
        result, error = client.analyze_non_placement(SAMPLE_EVIDENCE, target_career=None)
        assert error is None
        assert not hasattr(result, "confidence")
        assert not hasattr(result, "made_up_fact")


class TestAnalyzeAttrition:
    def test_valid_output(self):
        client = _client_with_mocked_response(json.dumps({
            "category": "skill_mismatch",
            "primary_reason": "The role likely required skills beyond what was demonstrated.",
            "supporting_evidence_ids": ["training_relevance"],
            "recommended_intervention": "Pursue targeted upskilling in the missing area.",
        }))
        evidence = [{"id": "training_relevance", "statement": "Training relevance to this role was low."}]
        result, error = client.analyze_attrition(evidence)
        assert error is None
        assert result.category == "skill_mismatch"
        assert result.supporting_evidence_ids == ["training_relevance"]

    def test_invalid_json_returns_error(self):
        client = _client_with_mocked_response("<<not json>>")
        result, error = client.analyze_attrition(SAMPLE_EVIDENCE)
        assert result is None
        assert error is not None

    def test_missing_required_fields_returns_error(self):
        client = _client_with_mocked_response(json.dumps({
            "category": "unknown",
            "primary_reason": "",
            "supporting_evidence_ids": [],
            "recommended_intervention": "",
        }))
        result, error = client.analyze_attrition(SAMPLE_EVIDENCE)
        assert result is None
        assert error is not None

    def test_ai_unavailable(self):
        client = _unavailable_client()
        result, error = client.analyze_attrition(SAMPLE_EVIDENCE)
        assert result is None
        assert error is not None

    def test_out_of_vocabulary_category_passes_through_raw(self):
        """The raw client only parses the JSON shape — enforcing the fixed
        category vocabulary is the service layer's job (see
        app.services.outcome_ai_analysis.ALLOWED_ATTRITION_CATEGORIES)."""
        client = _client_with_mocked_response(json.dumps({
            "category": "the-trainee-moved-to-mars",
            "primary_reason": "Some reason.",
            "supporting_evidence_ids": [],
            "recommended_intervention": "Some action.",
        }))
        result, error = client.analyze_attrition(SAMPLE_EVIDENCE)
        assert error is None
        assert result.category == "the-trainee-moved-to-mars"


class TestExplainTrainingRelevance:
    def test_valid_output(self):
        client = _client_with_mocked_response(json.dumps({
            "explanation": "React and JavaScript from the training directly apply to this Frontend Developer role.",
        }))
        result, error = client.explain_training_relevance(
            level="high",
            training_skills=["JavaScript", "React", "Node.js"],
            job_title="Frontend Developer",
            overlap_skills=["JavaScript", "React"],
            coverage_ratio=0.67,
        )
        assert error is None
        assert "Frontend Developer" in result.explanation

    def test_invalid_json_returns_error(self):
        client = _client_with_mocked_response("not valid json {{{")
        result, error = client.explain_training_relevance(
            level="low", training_skills=["JavaScript"], job_title="Sales Executive",
            overlap_skills=[], coverage_ratio=0.0,
        )
        assert result is None
        assert error is not None

    def test_missing_explanation_returns_error(self):
        client = _client_with_mocked_response(json.dumps({"explanation": ""}))
        result, error = client.explain_training_relevance(
            level="medium", training_skills=["SQL"], job_title="Data Entry Clerk",
            overlap_skills=["SQL"], coverage_ratio=0.3,
        )
        assert result is None
        assert error is not None

    def test_ai_unavailable(self):
        client = _unavailable_client()
        result, error = client.explain_training_relevance(
            level="high", training_skills=[], job_title="", overlap_skills=[], coverage_ratio=0.0,
        )
        assert result is None
        assert error is not None

    def test_response_schema_has_no_level_field(self):
        """Architectural guarantee: the AI has no field through which it
        could override the deterministic level, even if it tried to."""
        from app.ai.groq_client import TrainingRelevanceAIExplanation
        assert "level" not in TrainingRelevanceAIExplanation.model_fields
        assert "score" not in TrainingRelevanceAIExplanation.model_fields

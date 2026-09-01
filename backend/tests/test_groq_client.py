import json
from unittest.mock import MagicMock

from app.ai.groq_client import GroqAIClient, _is_placeholder_skill


class TestIsPlaceholderSkill:
    def test_matches_bare_placeholder(self):
        assert _is_placeholder_skill("skill1") is True
        assert _is_placeholder_skill("skill2") is True
        assert _is_placeholder_skill("Skill1") is True
        assert _is_placeholder_skill("  skill1  ") is True

    def test_matches_bare_word_skill(self):
        assert _is_placeholder_skill("skill") is True

    def test_does_not_match_real_skill_names(self):
        assert _is_placeholder_skill("React") is False
        assert _is_placeholder_skill("Skill Development") is False
        assert _is_placeholder_skill("Skillet Design") is False
        assert _is_placeholder_skill("JavaScript") is False


def _client_with_mocked_response(content: str) -> GroqAIClient:
    client = GroqAIClient()
    client._client = MagicMock()
    # `is_available` lazily calls `_ensure_initialized()`, which would
    # otherwise clobber this mock with a real `groq.Groq` client the moment
    # GROQ_API_KEY is present in the environment (e.g. once any other test
    # in the suite has imported app.main and triggered its load_dotenv()).
    client._initialized = True
    client._client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=content))]
    )
    return client


class TestExtractSkillsFromText:
    def test_filters_out_echoed_prompt_placeholder(self):
        """Regression guard: under load the model can echo the extraction
        prompt's own JSON example ("skill1"/"skill2") verbatim instead of
        extracting real skills — this must never reach the matching engine
        as a fake "required skill"."""
        client = _client_with_mocked_response(json.dumps({"skills": ["skill1", "skill2"]}))
        skills, error = client.extract_skills_from_text("Some job description text.")
        assert skills == []
        assert error is None

    def test_filters_placeholder_while_keeping_real_skills(self):
        client = _client_with_mocked_response(json.dumps({"skills": ["React", "skill1", "TypeScript"]}))
        skills, error = client.extract_skills_from_text("Build UI with React and TypeScript.")
        assert skills == ["React", "TypeScript"]

    def test_real_skills_pass_through_unfiltered(self):
        client = _client_with_mocked_response(json.dumps({"skills": ["Python", "Django", "PostgreSQL"]}))
        skills, error = client.extract_skills_from_text("Backend role using Python, Django, PostgreSQL.")
        assert skills == ["Python", "Django", "PostgreSQL"]

import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.coach_service import (
    _build_context_string,
    _build_suggestions,
    _build_fallback_response,
    _trim_conversation,
    ask_coach,
)


class TestBuildContextString:
    def test_includes_user_name(self):
        context = {"name": "Alice", "skills": [], "interests": []}
        result = _build_context_string(context)
        assert "Alice" in result

    def test_includes_skills(self):
        context = {
            "name": "Bob",
            "skills": [
                {"name": "Python", "category": "Programming", "proficiency": 4, "level_name": "Advanced", "confidence": "HIGH"},
                {"name": "SQL", "category": "Data", "proficiency": 2, "level_name": "Basic", "confidence": "LOW"},
            ],
            "interests": [],
        }
        result = _build_context_string(context)
        assert "Python: 4/5 (HIGH confidence)" in result
        assert "SQL: 2/5 (LOW confidence)" in result

    def test_includes_career(self):
        context = {
            "name": "Bob",
            "skills": [],
            "interests": [],
            "selected_career": {"name": "Data Scientist", "category": "Data", "description": "Analyze data", "required_skills": ["Python"], "optional_skills": []},
            "career_match": {"match_score": 0.75, "confidence": "High", "missing_skills": ["Machine Learning"]},
        }
        result = _build_context_string(context)
        assert "Data Scientist" in result
        assert "75%" in result
        assert "Machine Learning" in result

    def test_includes_skill_gaps(self):
        context = {
            "name": "Bob",
            "skills": [],
            "interests": [],
            "skill_gaps": {
                "gaps": [
                    {"skill": "Machine Learning", "current_level": 1, "gap_size": 4, "importance": 0.95, "priority_score": 3.8},
                ]
            },
        }
        result = _build_context_string(context)
        assert "Machine Learning" in result
        assert "current 1/5" in result

    def test_includes_roadmap(self):
        context = {
            "name": "Bob",
            "skills": [],
            "interests": [],
            "roadmap": {
                "summary": "Learning roadmap for Data Scientist",
                "total_phases": 4,
                "completed_phases": 1,
                "current_phase": {"phase_number": 2, "title": "ML Fundamentals", "objective": "Learn ML", "skills": ["Machine Learning"], "duration_weeks": 4, "adaptation_mode": "full"},
                "completed_phase_titles": ["Python Basics"],
            },
        }
        result = _build_context_string(context)
        assert "ML Fundamentals" in result
        assert "1/4 phases completed" in result

    def test_missing_data_not_invented(self):
        context = {
            "name": "Bob",
            "skills": [],
            "interests": [],
            "selected_career": None,
            "career_match": None,
            "skill_gaps": None,
            "roadmap": None,
            "assessment": None,
        }
        result = _build_context_string(context)
        assert "None selected" in result
        assert "No gap analysis" in result
        assert "No roadmap" in result
        assert "Not completed" in result

    def test_includes_next_best_action(self):
        context = {
            "name": "Bob",
            "skills": [],
            "interests": [],
            "next_best_action": {
                "action": "ASSESS_SKILL",
                "title": "Assess Machine Learning",
                "why": "Largest gap",
                "skill_name": "Machine Learning",
            },
        }
        result = _build_context_string(context)
        assert "Assess Machine Learning" in result
        assert "Largest gap" in result


class TestBuildSuggestions:
    def test_no_skills(self):
        context = {"skills": [], "assessment": None, "selected_career": None, "roadmap": None, "projects": {}}
        suggestions = _build_suggestions(context)
        assert any("add my skills" in s.lower() for s in suggestions)

    def test_has_skills_no_assessment(self):
        context = {
            "skills": [{"name": "Python", "proficiency": 3}],
            "assessment": None,
            "selected_career": None,
            "roadmap": None,
            "projects": {},
        }
        suggestions = _build_suggestions(context)
        assert any("assessment" in s.lower() for s in suggestions)

    def test_has_career_no_roadmap(self):
        context = {
            "skills": [{"name": "Python", "proficiency": 3}],
            "assessment": {"scores": {}},
            "selected_career": {"name": "Data Scientist"},
            "roadmap": None,
            "projects": {},
        }
        suggestions = _build_suggestions(context)
        assert any("roadmap" in s.lower() for s in suggestions)

    def test_all_complete(self):
        context = {
            "skills": [{"name": "Python", "proficiency": 4}],
            "assessment": {"scores": {"technical": 0.8}},
            "selected_career": {"name": "Data Scientist"},
            "roadmap": {"total_phases": 4, "completed_phases": 2},
            "projects": {"completed": 2},
            "next_best_action": {"action": "BUILD_PROJECT", "title": "Build project"},
            "skill_gaps": {"gaps": [{"skill": "ML", "gap_size": 3}]},
        }
        suggestions = _build_suggestions(context)
        assert len(suggestions) > 0
        assert len(suggestions) <= 3


class TestBuildFallbackResponse:
    def test_what_to_learn_next_with_gaps(self):
        context = {
            "name": "Alice",
            "skills": [{"name": "Python", "proficiency": 3}],
            "selected_career": {"name": "Data Scientist"},
            "skill_gaps": {
                "gaps": [
                    {"skill": "Machine Learning", "current_level": 1, "gap_size": 4, "importance": 0.95, "priority_score": 3.8},
                    {"skill": "SQL", "current_level": 2, "gap_size": 3, "importance": 0.8, "priority_score": 2.4},
                ]
            },
            "roadmap": {"current_phase": {"phase_number": 1, "title": "ML Basics", "objective": "Learn ML", "skills": ["Machine Learning"], "duration_weeks": 4}},
            "next_best_action": {"action": "ASSESS_SKILL", "title": "Assess Machine Learning", "why": "Largest gap"},
        }
        response = _build_fallback_response(context, "What should I learn next?")
        assert "Machine Learning" in response
        assert "SQL" in response
        # Response should NOT start with a greeting
        assert not response.startswith("Hi ")
        assert not response.startswith("Hello ")

    def test_progress_question(self):
        context = {
            "name": "Bob",
            "skills": [{"name": "Python", "proficiency": 3}, {"name": "SQL", "proficiency": 2}],
            "selected_career": {"name": "Data Scientist"},
            "career_match": {"match_score": 0.65},
            "roadmap": {"completed_phases": 2, "total_phases": 5},
            "projects": {"completed": 3},
            "next_best_action": {},
        }
        response = _build_fallback_response(context, "How am I doing?")
        assert "65%" in response
        assert "2/5 phases completed" in response
        # Response should NOT start with a greeting
        assert not response.startswith("Hi ")
        assert not response.startswith("Hello ")

    def test_no_skills_fallback(self):
        context = {"name": "Charlie", "skills": [], "selected_career": None, "skill_gaps": None, "roadmap": None, "next_best_action": {}}
        response = _build_fallback_response(context, "What should I learn next?")
        assert "haven't added any skills" in response

    def test_never_invents_data(self):
        context = {"name": "Dave", "skills": [], "selected_career": None, "skill_gaps": None, "roadmap": None, "next_best_action": {}}
        response = _build_fallback_response(context, "Tell me about my Python skills")
        assert "3/5" not in response
        assert "4/5" not in response
        assert "5/5" not in response

    def test_project_question(self):
        context = {
            "name": "Eve",
            "skills": [{"name": "Python", "proficiency": 3}],
            "selected_career": {"name": "Data Scientist"},
            "projects": {"recommended": 2, "in_progress": 1, "completed": 0},
            "next_best_action": {"action": "BUILD_PROJECT", "title": "Build Data Pipeline", "why": "Practical experience needed"},
        }
        response = _build_fallback_response(context, "What project should I build?")
        assert "Build Data Pipeline" in response

    def test_skill_question(self):
        context = {
            "name": "Frank",
            "skills": [
                {"name": "Python", "proficiency": 4, "confidence": "HIGH"},
                {"name": "SQL", "proficiency": 2, "confidence": "LOW"},
            ],
            "selected_career": {"name": "Data Scientist"},
            "skill_gaps": {"gaps": [{"skill": "Machine Learning", "current_level": 0, "gap_size": 5, "importance": 0.95}]},
            "next_best_action": {},
        }
        response = _build_fallback_response(context, "What are my skills?")
        assert "Python" in response
        assert "SQL" in response
        # Response should NOT start with a greeting
        assert not response.startswith("Hi ")
        assert not response.startswith("Hello ")

    def test_default_summary(self):
        context = {
            "name": "Grace",
            "skills": [{"name": "Python", "proficiency": 3}],
            "selected_career": {"name": "Data Scientist"},
            "career_match": {"match_score": 0.7},
            "projects": {"completed": 1},
            "next_best_action": {"action": "ASSESS_SKILL", "title": "Assess ML", "why": "Gap"},
        }
        response = _build_fallback_response(context, "Hello coach")
        assert "Python" in response
        assert "70%" in response
        assert "Assess ML" in response

    def test_react_improvement_question(self):
        """Test that React improvement question provides personalized roadmap."""
        context = {
            "name": "Aarav",
            "skills": [
                {"name": "Python", "proficiency": 1, "category": "Programming", "level_name": "Beginner", "confidence": "LOW"},
                {"name": "JavaScript", "proficiency": 1, "category": "Frontend", "level_name": "Beginner", "confidence": "LOW"},
                {"name": "React", "proficiency": 0, "category": "Frontend", "level_name": "None", "confidence": "LOW"},
            ],
            "selected_career": None,
            "skill_gaps": {
                "gaps": [
                    {"skill": "React", "current_level": 0, "gap_size": 5, "importance": 0.95, "priority_score": 4.75},
                ]
            },
            "next_best_action": {},
        }
        response = _build_fallback_response(context, "How do I improve my React skills?")
        # Should mention React level
        assert "React" in response
        # Should mention JavaScript as prerequisite
        assert "JavaScript" in response
        # Should NOT dump all skills (Python shouldn't be mentioned)
        assert "Python" not in response
        # Should NOT start with greeting
        assert not response.startswith("Hi ")
        assert not response.startswith("Hello ")
        # Should provide actionable roadmap
        assert "Step" in response
        assert "project" in response.lower()

    def test_no_repeated_greeting(self):
        """Test that follow-up messages don't start with greetings."""
        context = {
            "name": "TestUser",
            "skills": [{"name": "Python", "proficiency": 3}],
            "selected_career": None,
            "next_best_action": {},
        }
        response = _build_fallback_response(context, "How am I doing?")
        assert not response.startswith("Hi ")
        assert not response.startswith("Hello ")
        assert not response.startswith("Hey ")

    def test_job_match_question(self):
        """Test job-related question handling."""
        context = {
            "name": "TestUser",
            "skills": [{"name": "Python", "proficiency": 3}],
            "selected_career": {"name": "Data Scientist"},
            "career_match": {"match_score": 0.75, "missing_skills": ["Machine Learning", "Deep Learning"]},
            "next_best_action": {},
        }
        response = _build_fallback_response(context, "What skills am I missing for this job?")
        assert "Machine Learning" in response
        assert "Deep Learning" in response
        # Should NOT dump entire profile
        assert "Python" not in response or response.count("Python") < 2

    def test_general_question(self):
        """Test general question handling."""
        context = {
            "name": "TestUser",
            "skills": [{"name": "Python", "proficiency": 3}],
            "selected_career": {"name": "Data Scientist"},
            "career_match": {"match_score": 0.7},
            "projects": {"completed": 1},
            "next_best_action": {"action": "ASSESS_SKILL", "title": "Assess ML", "why": "Gap"},
        }
        response = _build_fallback_response(context, "Hello")
        # Should provide helpful response
        assert len(response) > 0
        # Should not dump entire profile
        assert response.count("Python") <= 1

    def test_project_count_question(self):
        """Test project count question returns actual count."""
        context = {
            "name": "TestUser",
            "skills": [{"name": "Python", "proficiency": 3}],
            "selected_career": {"name": "Data Scientist"},
            "projects": {"completed": 5, "in_progress": 2, "recommended": 3},
            "next_best_action": {},
        }
        response = _build_fallback_response(context, "How many projects have I built?")
        assert "5" in response
        assert "completed" in response.lower()
        # Should NOT start with greeting
        assert not response.startswith("Hi ")
        assert not response.startswith("Hello ")

    def test_project_count_zero(self):
        """Test project count when no projects completed."""
        context = {
            "name": "TestUser",
            "skills": [{"name": "Python", "proficiency": 3}],
            "selected_career": None,
            "projects": {"completed": 0, "in_progress": 0, "recommended": 2},
            "next_best_action": {},
        }
        response = _build_fallback_response(context, "How many projects done?")
        assert "0" in response
        assert "Start building" in response


class TestTrimConversation:
    def test_keeps_only_user_and_assistant_roles(self):
        conversation = [
            {"role": "system", "content": "should be dropped"},
            {"role": "user", "content": "What should I learn next?"},
            {"role": "assistant", "content": "Node.js."},
        ]
        result = _trim_conversation(conversation)
        assert result == [
            {"role": "user", "content": "What should I learn next?"},
            {"role": "assistant", "content": "Node.js."},
        ]

    def test_limits_to_max_messages(self):
        conversation = [{"role": "user", "content": f"msg {i}"} for i in range(30)]
        result = _trim_conversation(conversation)
        assert len(result) <= 10
        assert result[-1]["content"] == "msg 29"

    def test_handles_none_and_empty(self):
        assert _trim_conversation(None) == []
        assert _trim_conversation([]) == []

    def test_drops_malformed_entries(self):
        conversation = [
            {"role": "user", "content": ""},
            {"role": "user"},
            "not a dict",
            {"role": "user", "content": "real question"},
        ]
        result = _trim_conversation(conversation)
        assert result == [{"role": "user", "content": "real question"}]


class TestAskCoachGroqWiring:
    """Verifies ask_coach actually calls the Groq client with fresh DB context,
    rather than silently falling back to the deterministic template response."""

    @pytest.mark.asyncio
    async def test_uses_groq_when_available(self):
        db = MagicMock()
        user_id = uuid4()
        fake_context = {
            "name": "Alice",
            "skills": [{"name": "Node.js", "proficiency": 2, "confidence": "MEDIUM"}],
            "selected_career": None,
            "skill_gaps": None,
            "roadmap": None,
            "projects": {"completed": 0},
            "evidence": {},
            "next_best_action": {},
        }
        with patch("app.services.coach_service._gather_user_context", return_value=fake_context), \
             patch("app.ai.groq_client.groq_client") as mock_groq:
            mock_groq.is_available = True
            mock_groq.generate_coaching_response.return_value = ("Focus on Node.js next.", None)

            result = await ask_coach(db, user_id, "What should I learn next?", conversation=[])

            assert result["source"] == "ai"
            assert result["response"] == "Focus on Node.js next."
            mock_groq.generate_coaching_response.assert_called_once()
            call_args = mock_groq.generate_coaching_response.call_args[0]
            # system_prompt, context_string, conversation, question
            assert "Node.js" in call_args[1]
            assert call_args[3] == "What should I learn next?"

    @pytest.mark.asyncio
    async def test_passes_trimmed_conversation_for_followups(self):
        db = MagicMock()
        user_id = uuid4()
        fake_context = {"name": "Bob", "skills": [], "next_best_action": {}, "evidence": {}, "projects": {}}
        history = [
            {"role": "user", "content": "What should I learn next?"},
            {"role": "assistant", "content": "Node.js."},
        ]
        with patch("app.services.coach_service._gather_user_context", return_value=fake_context), \
             patch("app.ai.groq_client.groq_client") as mock_groq:
            mock_groq.is_available = True
            mock_groq.generate_coaching_response.return_value = ("Because it's your largest gap.", None)

            result = await ask_coach(db, user_id, "Why?", conversation=history)

            assert result["response"] == "Because it's your largest gap."
            call_args = mock_groq.generate_coaching_response.call_args[0]
            assert call_args[2] == history

    @pytest.mark.asyncio
    async def test_falls_back_when_groq_unavailable(self):
        db = MagicMock()
        user_id = uuid4()
        fake_context = {
            "name": "Charlie",
            "skills": [],
            "selected_career": None,
            "skill_gaps": None,
            "roadmap": None,
            "projects": {},
            "evidence": {},
            "next_best_action": {},
        }
        with patch("app.services.coach_service._gather_user_context", return_value=fake_context), \
             patch("app.ai.groq_client.groq_client") as mock_groq:
            mock_groq.is_available = False

            result = await ask_coach(db, user_id, "What should I learn next?", conversation=[])

            assert result["source"] == "fallback"
            assert "haven't added any skills" in result["response"]

import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.database.migrations import run_migrations
from app.services.skill_assessment_service import (
    calculate_score,
    determine_proficiency,
    _generate_fallback_questions,
    start_assessment,
    submit_assessment,
    DIFFICULTY_WEIGHTS,
)


def _make_skill(skill_id=None, name="JavaScript", category="Programming"):
    skill = MagicMock()
    skill.id = skill_id or uuid4()
    skill.name = name
    skill.category = category
    return skill


def _make_user(user_id=None):
    user = MagicMock()
    user.id = user_id or uuid4()
    return user


def _make_session(session_id=None, user_id=None, skill_id=None, status="in_progress"):
    session = MagicMock()
    session.id = session_id or uuid4()
    session.user_id = user_id
    session.skill_id = skill_id
    session.status = status
    session.questions_json = None
    session.answers_json = None
    session.score_percentage = None
    session.proficiency = None
    session.level_name = None
    session.created_at = datetime.utcnow()
    session.completed_at = None
    return session


def _make_user_skill(user_id=None, skill_id=None, proficiency=3):
    us = MagicMock()
    us.id = uuid4()
    us.user_id = user_id
    us.skill_id = skill_id
    us.proficiency = proficiency
    us.level_name = None
    us.confidence = "LOW"
    return us


def _make_fallback_questions():
    return _generate_fallback_questions("JavaScript")


class TestCalculateScore:
    def test_all_correct(self):
        questions = _make_fallback_questions()
        answers = {q["id"]: q["correct_answer"] for q in questions}
        score = calculate_score(questions, answers)
        assert score == 100.0

    def test_all_wrong(self):
        questions = _make_fallback_questions()
        wrong_answers = {}
        for q in questions:
            wrong = [o for o in ["A", "B", "C", "D"] if o != q["correct_answer"]]
            wrong_answers[q["id"]] = wrong[0]
        score = calculate_score(questions, wrong_answers)
        assert score == 0.0

    def test_half_correct(self):
        questions = _make_fallback_questions()
        answers = {}
        for i, q in enumerate(questions):
            if i % 2 == 0:
                answers[q["id"]] = q["correct_answer"]
            else:
                wrong = [o for o in ["A", "B", "C", "D"] if o != q["correct_answer"]]
                answers[q["id"]] = wrong[0]
        score = calculate_score(questions, answers)
        assert 40 < score < 60

    def test_empty_answers(self):
        questions = _make_fallback_questions()
        score = calculate_score(questions, {})
        assert score == 0.0

    def test_weighted_scoring(self):
        questions = [
            {"id": 1, "difficulty": "beginner", "correct_answer": "A"},
            {"id": 2, "difficulty": "advanced", "correct_answer": "A"},
        ]
        answers = {1: "A", 2: "A"}
        score = calculate_score(questions, answers)
        assert score == 100.0

        answers_wrong_advanced = {1: "A", 2: "B"}
        score2 = calculate_score(questions, answers_wrong_advanced)
        expected = (0.2 / 0.5) * 100
        assert abs(score2 - expected) < 0.01


class TestDetermineProficiency:
    def test_beginner(self):
        level, name = determine_proficiency(10)
        assert level == 1
        assert name == "Beginner"

    def test_basic(self):
        level, name = determine_proficiency(30)
        assert level == 2
        assert name == "Basic"

    def test_intermediate(self):
        level, name = determine_proficiency(50)
        assert level == 3
        assert name == "Intermediate"

    def test_advanced(self):
        level, name = determine_proficiency(70)
        assert level == 4
        assert name == "Advanced"

    def test_expert(self):
        level, name = determine_proficiency(90)
        assert level == 5
        assert name == "Expert"

    def test_boundary_low(self):
        level, name = determine_proficiency(20)
        assert level == 1

    def test_boundary_high(self):
        level, name = determine_proficiency(100)
        assert level == 5


class TestFallbackQuestions:
    def test_javascript_fallback(self):
        questions = _generate_fallback_questions("JavaScript")
        assert len(questions) == 10

    def test_python_fallback(self):
        questions = _generate_fallback_questions("Python")
        assert len(questions) == 10

    def test_unknown_skill_fallback(self):
        questions = _generate_fallback_questions("Kubernetes")
        assert len(questions) == 10

    def test_difficulty_distribution(self):
        questions = _generate_fallback_questions("JavaScript")
        counts = {}
        for q in questions:
            counts[q["difficulty"]] = counts.get(q["difficulty"], 0) + 1
        assert counts.get("beginner", 0) == 3
        assert counts.get("intermediate", 0) == 3
        assert counts.get("advanced", 0) == 2
        assert counts.get("practical", 0) == 2

    def test_all_have_options(self):
        questions = _generate_fallback_questions("JavaScript")
        for q in questions:
            assert len(q["options"]) == 4
            assert q["correct_answer"] in ["A", "B", "C", "D"]


class TestStartAssessment:
    @patch("app.services.skill_assessment_service.groq_client")
    def test_start_with_ai(self, mock_groq):
        mock_groq.is_available = True
        question_dicts = [
            {"id": 1, "difficulty": "beginner", "type": "mcq", "question": "Q1", "options": ["A", "B", "C", "D"], "correct_answer": "A", "explanation": "E1"},
            {"id": 2, "difficulty": "beginner", "type": "mcq", "question": "Q2", "options": ["A", "B", "C", "D"], "correct_answer": "B", "explanation": "E2"},
            {"id": 3, "difficulty": "beginner", "type": "mcq", "question": "Q3", "options": ["A", "B", "C", "D"], "correct_answer": "C", "explanation": "E3"},
            {"id": 4, "difficulty": "intermediate", "type": "mcq", "question": "Q4", "options": ["A", "B", "C", "D"], "correct_answer": "A", "explanation": "E4"},
            {"id": 5, "difficulty": "intermediate", "type": "mcq", "question": "Q5", "options": ["A", "B", "C", "D"], "correct_answer": "B", "explanation": "E5"},
            {"id": 6, "difficulty": "intermediate", "type": "mcq", "question": "Q6", "options": ["A", "B", "C", "D"], "correct_answer": "C", "explanation": "E6"},
            {"id": 7, "difficulty": "advanced", "type": "mcq", "question": "Q7", "options": ["A", "B", "C", "D"], "correct_answer": "A", "explanation": "E7"},
            {"id": 8, "difficulty": "advanced", "type": "mcq", "question": "Q8", "options": ["A", "B", "C", "D"], "correct_answer": "B", "explanation": "E8"},
            {"id": 9, "difficulty": "practical", "type": "mcq", "question": "Q9", "options": ["A", "B", "C", "D"], "correct_answer": "A", "explanation": "E9"},
            {"id": 10, "difficulty": "practical", "type": "mcq", "question": "Q10", "options": ["A", "B", "C", "D"], "correct_answer": "B", "explanation": "E10"},
        ]
        mock_questions = MagicMock()
        mock_questions.questions = []
        for d in question_dicts:
            m = MagicMock()
            m.model_dump.return_value = d
            mock_questions.questions.append(m)
        mock_groq.generate_questions.return_value = (mock_questions, None)

        db = MagicMock()
        skill = _make_skill()
        db.query.return_value.filter.return_value.first.return_value = skill
        db.query.return_value.filter.return_value.all.return_value = []

        user = _make_user()
        result = start_assessment(db, user.id, skill.id)

        assert "assessment_id" in result
        assert result["skill"]["name"] == "JavaScript"
        assert len(result["questions"]) == 10
        for q in result["questions"]:
            assert "correct_answer" not in q
            assert "explanation" not in q

    @patch("app.services.skill_assessment_service.groq_client")
    def test_start_without_ai(self, mock_groq):
        mock_groq.is_available = False
        mock_groq.generate_questions.return_value = (None, "AI service not available")

        db = MagicMock()
        skill = _make_skill()
        db.query.return_value.filter.return_value.first.return_value = skill
        db.query.return_value.filter.return_value.all.return_value = []

        user = _make_user()
        result = start_assessment(db, user.id, skill.id)

        assert len(result["questions"]) == 10
        assert result["skill"]["name"] == "JavaScript"

    def test_start_skill_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        user = _make_user()
        with pytest.raises(ValueError, match="Skill not found"):
            start_assessment(db, user.id, uuid4())


class TestSubmitAssessment:
    @patch("app.services.skill_assessment_service.create_assessment_evidence")
    @patch("app.services.skill_assessment_service.groq_client")
    def test_submit_and_update_skill(self, mock_groq, mock_create_evidence):
        mock_groq.analyze_results.return_value = (
            MagicMock(
                strengths=["Good basics"],
                weaknesses=["Needs more practice"],
                recommended_topics=["Async/Await", "Promises"],
                summary="Solid foundation.",
            ),
            None,
        )
        mock_create_evidence.return_value = MagicMock()

        user_id = uuid4()
        skill_id = uuid4()
        session = _make_session(user_id=user_id, skill_id=skill_id)

        questions = _make_fallback_questions()
        session.get_questions.return_value = questions

        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [
            session,
            _make_skill(skill_id=skill_id, name="JavaScript"),
            None,
        ]

        answers = [{"question_id": q["id"], "answer": q["correct_answer"]} for q in questions]
        result = submit_assessment(db, user_id, session.id, answers)

        assert result["proficiency"] == 5
        assert result["level_name"] == "Expert"
        assert result["score_percentage"] == 100
        assert len(result["strengths"]) > 0
        assert "confidence" in result
        assert result["confidence"] == "LOW"
        mock_create_evidence.assert_called_once()

    @patch("app.services.skill_assessment_service.create_assessment_evidence")
    @patch("app.services.skill_assessment_service.groq_client")
    def test_submit_updates_existing_skill(self, mock_groq, mock_create_evidence):
        mock_groq.analyze_results.return_value = (None, "AI analysis error")
        mock_create_evidence.return_value = MagicMock()

        user_id = uuid4()
        skill_id = uuid4()
        session = _make_session(user_id=user_id, skill_id=skill_id)
        session.get_questions.return_value = _make_fallback_questions()

        existing_skill = _make_user_skill(user_id=user_id, skill_id=skill_id, proficiency=2)

        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [
            session,
            _make_skill(skill_id=skill_id),
            existing_skill,
        ]

        answers = [{"question_id": q["id"], "answer": "A"} for q in _make_fallback_questions()]
        result = submit_assessment(db, user_id, session.id, answers)

        assert existing_skill.proficiency == result["proficiency"]
        assert existing_skill.level_name is not None
        mock_create_evidence.assert_called_once()

    def test_submit_unauthorized(self):
        user_id = uuid4()
        other_user_id = uuid4()
        session = _make_session(user_id=other_user_id, skill_id=uuid4())
        session.get_questions.return_value = _make_fallback_questions()

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = session

        answers = [{"question_id": 1, "answer": "A"}]
        with pytest.raises(ValueError, match="Unauthorized"):
            submit_assessment(db, user_id, session.id, answers)

    def test_submit_already_completed(self):
        user_id = uuid4()
        session = _make_session(user_id=user_id, skill_id=uuid4(), status="completed")

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = session

        answers = [{"question_id": 1, "answer": "A"}]
        with pytest.raises(ValueError, match="already completed"):
            submit_assessment(db, user_id, session.id, answers)

    def test_submit_session_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="not found"):
            submit_assessment(db, uuid4(), uuid4(), [])


class TestDifficultyDistribution:
    def test_fallback_distribution_matches_spec(self):
        for skill in ["JavaScript", "Python", "SQL", "React"]:
            questions = _generate_fallback_questions(skill)
            counts = {}
            for q in questions:
                counts[q["difficulty"]] = counts.get(q["difficulty"], 0) + 1
            assert counts.get("beginner", 0) == 3, f"{skill} beginner mismatch"
            assert counts.get("intermediate", 0) == 3, f"{skill} intermediate mismatch"
            assert counts.get("advanced", 0) == 2, f"{skill} advanced mismatch"
            assert counts.get("practical", 0) == 2, f"{skill} practical mismatch"
            assert len(questions) == 10, f"{skill} total mismatch"

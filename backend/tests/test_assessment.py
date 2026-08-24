import pytest
from uuid import uuid4
from unittest.mock import MagicMock

from app.services.assessment_service import score_assessment, DIMENSIONS


def _make_mock_question(qid, category, options, scoring):
    q = MagicMock()
    q.id = qid
    q.question_text = f"Test question {qid}"
    q.category = category
    q.options = options
    q.scoring = scoring
    return q


class TestAssessmentScoring:
    def test_all_high_scores(self):
        q1 = _make_mock_question("q1", "technical_interest", ["A", "B", "C", "D"], {"0": 0.9, "1": 0.7, "2": 0.4, "3": 0.2})
        q2 = _make_mock_question("q2", "problem_solving", ["A", "B", "C", "D"], {"0": 0.9, "1": 0.7, "2": 0.4, "3": 0.2})

        db = MagicMock()
        db.query.return_value.all.return_value = [q1, q2]

        answers = {"q1": 0, "q2": 0}
        result = score_assessment(db, uuid4(), answers)

        assert result["scores"]["technical_interest"] == 0.9
        assert result["scores"]["problem_solving"] == 0.9

    def test_mixed_scores(self):
        q1 = _make_mock_question("q1", "technical_interest", ["A", "B"], {"0": 0.9, "1": 0.3})

        db = MagicMock()
        db.query.return_value.all.return_value = [q1]

        answers = {"q1": 1}
        result = score_assessment(db, uuid4(), answers)

        assert result["scores"]["technical_interest"] == 0.3

    def test_empty_answers(self):
        q1 = _make_mock_question("q1", "technical_interest", ["A", "B"], {"0": 0.9, "1": 0.3})

        db = MagicMock()
        db.query.return_value.all.return_value = [q1]

        result = score_assessment(db, uuid4(), {})

        assert result["scores"]["technical_interest"] == 0.5  # default

    def test_unknown_question_ignored(self):
        q1 = _make_mock_question("q1", "technical_interest", ["A", "B"], {"0": 0.9, "1": 0.3})

        db = MagicMock()
        db.query.return_value.all.return_value = [q1]

        answers = {"unknown_q": 0}
        result = score_assessment(db, uuid4(), answers)

        assert result["scores"]["technical_interest"] == 0.5  # no answer for this dimension

    def test_top_interests_identified(self):
        q1 = _make_mock_question("q1", "technical_interest", ["A"], {"0": 0.9})
        q2 = _make_mock_question("q2", "problem_solving", ["A"], {"0": 0.5})
        q3 = _make_mock_question("q3", "creativity", ["A"], {"0": 0.7})

        db = MagicMock()
        db.query.return_value.all.return_value = [q1, q2, q3]

        result = score_assessment(db, uuid4(), {"q1": 0, "q2": 0, "q3": 0})

        assert result["top_interests"][0] == "technical_interest"
        assert len(result["top_interests"]) == 3

    def test_interpretation_generated(self):
        q1 = _make_mock_question("q1", "technical_interest", ["A"], {"0": 0.9})

        db = MagicMock()
        db.query.return_value.all.return_value = [q1]

        result = score_assessment(db, uuid4(), {"q1": 0})

        assert "technical_interest" in result["interpretation"]
        assert len(result["interpretation"]["technical_interest"]) > 0

    def test_all_dimensions_have_defaults(self):
        db = MagicMock()
        db.query.return_value.all.return_value = []

        result = score_assessment(db, uuid4(), {})

        for dim in DIMENSIONS:
            assert dim in result["scores"]
            assert result["scores"][dim] == 0.5

    def test_average_of_multiple_questions_per_category(self):
        q1 = _make_mock_question("q1", "technical_interest", ["A"], {"0": 0.8})
        q2 = _make_mock_question("q2", "technical_interest", ["A"], {"0": 0.6})

        db = MagicMock()
        db.query.return_value.all.return_value = [q1, q2]

        result = score_assessment(db, uuid4(), {"q1": 0, "q2": 0})

        expected = (0.8 + 0.6) / 2
        assert abs(result["scores"]["technical_interest"] - expected) < 0.01

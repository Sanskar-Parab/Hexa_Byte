import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.evidence_service import (
    compute_confidence_from_evidence,
    create_evidence,
    create_assessment_evidence,
    create_manual_evidence,
    CONFIDENCE_RULES,
    CONFIDENCE_PRIORITY,
)


def _make_evidence(source_type="manual", confidence="LOW", score=None):
    ev = MagicMock()
    ev.id = uuid4()
    ev.source_type = source_type
    ev.confidence = confidence
    ev.score = score
    ev.created_at = datetime.utcnow()
    return ev


class TestConfidenceRules:
    def test_assessment_is_high(self):
        assert CONFIDENCE_RULES["assessment"] == "HIGH"

    def test_project_is_high(self):
        assert CONFIDENCE_RULES["project"] == "HIGH"

    def test_resume_is_medium(self):
        assert CONFIDENCE_RULES["resume"] == "MEDIUM"

    def test_manual_is_low(self):
        assert CONFIDENCE_RULES["manual"] == "LOW"

    def test_practical_is_medium(self):
        assert CONFIDENCE_RULES["practical"] == "MEDIUM"


class TestConfidencePriority:
    def test_high_beats_low(self):
        assert CONFIDENCE_PRIORITY["HIGH"] > CONFIDENCE_PRIORITY["LOW"]

    def test_medium_between_low_and_high(self):
        assert CONFIDENCE_PRIORITY["LOW"] < CONFIDENCE_PRIORITY["MEDIUM"] < CONFIDENCE_PRIORITY["HIGH"]


class TestComputeConfidence:
    def test_empty_evidence_returns_low(self):
        assert compute_confidence_from_evidence([]) == "LOW"

    def test_single_low(self):
        ev = [_make_evidence(confidence="LOW")]
        assert compute_confidence_from_evidence(ev) == "LOW"

    def test_single_high(self):
        ev = [_make_evidence(confidence="HIGH")]
        assert compute_confidence_from_evidence(ev) == "HIGH"

    def test_mixed_returns_highest(self):
        ev = [
            _make_evidence(confidence="LOW"),
            _make_evidence(confidence="MEDIUM"),
            _make_evidence(confidence="HIGH"),
        ]
        assert compute_confidence_from_evidence(ev) == "HIGH"

    def test_medium_and_low_returns_medium(self):
        ev = [
            _make_evidence(confidence="LOW"),
            _make_evidence(confidence="MEDIUM"),
        ]
        assert compute_confidence_from_evidence(ev) == "MEDIUM"


class TestCreateEvidence:
    @patch("app.services.evidence_service._recompute_user_skill_confidence")
    def test_creates_evidence_with_correct_confidence(self, mock_recompute):
        db = MagicMock()
        user_id = uuid4()
        skill_id = uuid4()

        ev = create_evidence(
            db=db,
            user_id=user_id,
            skill_id=skill_id,
            source_type="assessment",
            title="Test Assessment",
            score=75.0,
        )

        assert ev.source_type == "assessment"
        assert ev.confidence == "HIGH"
        assert ev.score == 75.0
        assert ev.title == "Test Assessment"
        db.add.assert_called_once()
        db.flush.assert_called_once()
        mock_recompute.assert_called_once_with(db, user_id, skill_id)

    @patch("app.services.evidence_service._recompute_user_skill_confidence")
    def test_manual_evidence_is_low_confidence(self, mock_recompute):
        db = MagicMock()
        ev = create_evidence(
            db=db,
            user_id=uuid4(),
            skill_id=uuid4(),
            source_type="manual",
            title="Manual",
        )
        assert ev.confidence == "LOW"

    @patch("app.services.evidence_service._recompute_user_skill_confidence")
    def test_metadata_serialized(self, mock_recompute):
        db = MagicMock()
        ev = create_evidence(
            db=db,
            user_id=uuid4(),
            skill_id=uuid4(),
            source_type="assessment",
            title="Test",
            metadata={"foo": "bar"},
        )
        assert ev.metadata_json is not None

    @patch("app.services.evidence_service._recompute_user_skill_confidence")
    def test_confidence_override(self, mock_recompute):
        db = MagicMock()
        ev = create_evidence(
            db=db,
            user_id=uuid4(),
            skill_id=uuid4(),
            source_type="manual",
            title="Test",
            confidence_override="MEDIUM",
        )
        assert ev.confidence == "MEDIUM"

    @patch("app.services.evidence_service._recompute_user_skill_confidence")
    def test_no_confidence_override_uses_default(self, mock_recompute):
        db = MagicMock()
        ev = create_evidence(
            db=db,
            user_id=uuid4(),
            skill_id=uuid4(),
            source_type="manual",
            title="Test",
        )
        assert ev.confidence == "LOW"


class TestCreateAssessmentEvidence:
    @patch("app.services.evidence_service._recompute_user_skill_confidence")
    def test_assessment_evidence_fields(self, mock_recompute):
        db = MagicMock()
        user_id = uuid4()
        skill_id = uuid4()
        session_id = uuid4()

        ev = create_assessment_evidence(
            db=db,
            user_id=user_id,
            skill_id=skill_id,
            session_id=session_id,
            score_percentage=62.0,
            level_name="Intermediate",
            proficiency=3,
        )

        assert ev.source_type == "assessment"
        assert ev.confidence == "HIGH"
        assert ev.score == 62.0
        assert ev.source_id == session_id
        assert "62%" in ev.description
        assert "Intermediate" in ev.description


class TestCreateManualEvidence:
    @patch("app.services.evidence_service._recompute_user_skill_confidence")
    def test_manual_evidence_fields(self, mock_recompute):
        db = MagicMock()
        user_id = uuid4()
        skill_id = uuid4()

        ev = create_manual_evidence(
            db=db,
            user_id=user_id,
            skill_id=skill_id,
            proficiency=3,
        )

        assert ev.source_type == "manual"
        assert ev.confidence == "LOW"
        assert ev.title == "Manual Declaration"
        assert "Intermediate" in ev.description
        assert "3/5" in ev.description

    @patch("app.services.evidence_service._recompute_user_skill_confidence")
    def test_manual_evidence_high_proficiency_gets_medium_confidence(self, mock_recompute):
        db = MagicMock()
        user_id = uuid4()
        skill_id = uuid4()

        ev = create_manual_evidence(
            db=db,
            user_id=user_id,
            skill_id=skill_id,
            proficiency=5,
        )

        assert ev.source_type == "manual"
        assert ev.confidence == "MEDIUM"
        assert "Expert" in ev.description

    @patch("app.services.evidence_service._recompute_user_skill_confidence")
    def test_manual_evidence_advanced_gets_medium_confidence(self, mock_recompute):
        db = MagicMock()
        user_id = uuid4()
        skill_id = uuid4()

        ev = create_manual_evidence(
            db=db,
            user_id=user_id,
            skill_id=skill_id,
            proficiency=4,
        )

        assert ev.source_type == "manual"
        assert ev.confidence == "MEDIUM"
        assert "Advanced" in ev.description


class TestRecomputeUserSkillConfidence:
    def test_recomputes_confidence_from_evidence(self):
        db = MagicMock()
        user_id = uuid4()
        skill_id = uuid4()

        ev1 = _make_evidence(confidence="LOW")
        ev2 = _make_evidence(confidence="HIGH")
        db.query.return_value.filter.return_value.all.return_value = [ev1, ev2]

        user_skill = MagicMock()
        user_skill.confidence = "LOW"
        db.query.return_value.filter.return_value.first.return_value = user_skill

        from app.services.evidence_service import _recompute_user_skill_confidence
        _recompute_user_skill_confidence(db, user_id, skill_id)

        assert user_skill.confidence == "HIGH"

import pytest
from unittest.mock import MagicMock, patch
from app.services.roadmap_service import (
    _evaluate_phase_adaptation,
    _adapt_phase_content,
    _get_user_skill_proficiency_map,
    _generate_adaptive_roadmap,
    _preserve_phase_progress,
)
from app.api.roadmap import _validate_status_transition


class TestAdaptationEvaluation:
    def test_skip_when_all_skills_proficient(self):
        proficiency_map = {"Python": 5, "JavaScript": 4}
        mode = _evaluate_phase_adaptation(["Python", "JavaScript"], proficiency_map)
        assert mode == "skipped"

    def test_skip_when_average_above_threshold(self):
        proficiency_map = {"Python": 4, "JavaScript": 4}
        mode = _evaluate_phase_adaptation(["Python", "JavaScript"], proficiency_map)
        assert mode == "skipped"

    def test_adapt_when_mixed_proficiency(self):
        proficiency_map = {"Python": 3, "JavaScript": 2}
        mode = _evaluate_phase_adaptation(["Python", "JavaScript"], proficiency_map)
        assert mode == "adapted"

    def test_adapt_when_average_in_range(self):
        proficiency_map = {"Python": 2, "JavaScript": 3}
        mode = _evaluate_phase_adaptation(["Python", "JavaScript"], proficiency_map)
        assert mode == "adapted"

    def test_full_when_low_proficiency(self):
        proficiency_map = {"Python": 1, "JavaScript": 1}
        mode = _evaluate_phase_adaptation(["Python", "JavaScript"], proficiency_map)
        assert mode == "full"

    def test_full_when_no_skills_in_map(self):
        proficiency_map = {}
        mode = _evaluate_phase_adaptation(["Python", "JavaScript"], proficiency_map)
        assert mode == "full"

    def test_full_when_empty_skills(self):
        proficiency_map = {"Python": 5}
        mode = _evaluate_phase_adaptation([], proficiency_map)
        assert mode == "full"

    def test_skip_with_single_proficient_skill(self):
        proficiency_map = {"Python": 5}
        mode = _evaluate_phase_adaptation(["Python"], proficiency_map)
        assert mode == "skipped"


class TestPhaseAdaptation:
    def test_adapted_reduces_duration(self):
        phase_data = {
            "title": "Test Phase",
            "duration_weeks": 8,
            "activities": ["Activity 1", "Activity 2", "Activity 3"],
            "completion_criteria": ["Criteria 1", "Criteria 2", "Criteria 3"],
        }
        result = _adapt_phase_content(phase_data, "adapted")
        assert result["duration_weeks"] == 4
        assert len(result["activities"]) == 2
        assert len(result["completion_criteria"]) == 2

    def test_adapted_minimum_duration(self):
        phase_data = {
            "title": "Test Phase",
            "duration_weeks": 1,
            "activities": ["Activity 1"],
            "completion_criteria": ["Criteria 1"],
        }
        result = _adapt_phase_content(phase_data, "adapted")
        assert result["duration_weeks"] == 1

    def test_adapted_adds_quick_review_prefix(self):
        phase_data = {
            "title": "Test Phase",
            "duration_weeks": 4,
            "activities": ["Learn Python", "Practice coding"],
            "completion_criteria": ["Pass quiz"],
        }
        result = _adapt_phase_content(phase_data, "adapted")
        assert result["activities"][0].startswith("Quick review:")

    def test_full_mode_no_changes(self):
        phase_data = {
            "title": "Test Phase",
            "duration_weeks": 4,
            "activities": ["Activity 1"],
            "completion_criteria": ["Criteria 1"],
        }
        result = _adapt_phase_content(phase_data, "full")
        assert result == phase_data


class TestAdaptiveRoadmapGeneration:
    def _make_mock_career(self, learning_sequence=None):
        career = MagicMock()
        career.name = "Software Engineer"
        career.learning_sequence = learning_sequence or [
            {"title": "Python Basics", "skills": ["Python"], "project": "Build a script"},
            {"title": "Web Dev", "skills": ["HTML", "CSS", "JavaScript"], "project": "Build a website"},
        ]
        return career

    def test_skips_proficient_phases(self):
        career = self._make_mock_career()
        skill_gaps = {"gaps": [{"skill": "HTML", "gap_size": 3, "importance": 1.0}]}
        proficiency_map = {"Python": 5}

        result = _generate_adaptive_roadmap(career, skill_gaps, "Test", proficiency_map)
        assert len(result["phases"]) == 1
        assert result["phases"][0]["title"] == "Web Dev"

    def test_adapts_partial_proficient_phases(self):
        career = self._make_mock_career()
        skill_gaps = {"gaps": [{"skill": "Python", "gap_size": 2, "importance": 1.0}]}
        proficiency_map = {"Python": 3}

        result = _generate_adaptive_roadmap(career, skill_gaps, "Test", proficiency_map)
        assert len(result["phases"]) == 2
        adapted_phase = next(p for p in result["phases"] if p["title"] == "Python Basics")
        assert adapted_phase["adaptation_mode"] == "adapted"

    def test_includes_full_phases_for_beginners(self):
        career = self._make_mock_career()
        skill_gaps = {"gaps": [{"skill": "Python", "gap_size": 5, "importance": 1.0}]}
        proficiency_map = {"Python": 0}

        result = _generate_adaptive_roadmap(career, skill_gaps, "Test", proficiency_map)
        assert len(result["phases"]) == 2
        assert all(p["adaptation_mode"] == "full" for p in result["phases"])

    def test_summary_includes_skip_count(self):
        career = self._make_mock_career()
        skill_gaps = {"gaps": [{"skill": "Python", "gap_size": 5, "importance": 1.0}]}
        proficiency_map = {"Python": 5}

        result = _generate_adaptive_roadmap(career, skill_gaps, "Test", proficiency_map)
        assert "1 phases skipped" in result["summary"]

    def test_groups_skills_when_no_learning_sequence(self):
        career = self._make_mock_career(learning_sequence=[])
        skill_gaps = {
            "gaps": [
                {"skill": "Python", "gap_size": 5, "importance": 1.0},
                {"skill": "JavaScript", "gap_size": 4, "importance": 0.9},
                {"skill": "React", "gap_size": 3, "importance": 0.8},
                {"skill": "Node.js", "gap_size": 2, "importance": 0.7},
            ]
        }
        proficiency_map = {}

        result = _generate_adaptive_roadmap(career, skill_gaps, "Test", proficiency_map)
        assert len(result["phases"]) > 0
        assert all(p["adaptation_mode"] == "full" for p in result["phases"])


class TestStatusTransitionValidation:
    def test_not_started_to_in_progress(self):
        assert _validate_status_transition("not_started", "in_progress") is True

    def test_not_started_to_completed_invalid(self):
        assert _validate_status_transition("not_started", "completed") is False

    def test_in_progress_to_completed(self):
        assert _validate_status_transition("in_progress", "completed") is True

    def test_in_progress_to_not_started_reopen(self):
        assert _validate_status_transition("in_progress", "not_started") is True

    def test_completed_to_not_started_reopen(self):
        assert _validate_status_transition("completed", "not_started") is True

    def test_completed_to_in_progress_reopen(self):
        assert _validate_status_transition("completed", "in_progress") is True

    def test_completed_to_completed_invalid(self):
        assert _validate_status_transition("completed", "completed") is False


class TestProgressPreservation:
    def test_preserves_completed_status(self):
        db = MagicMock()
        user_id = MagicMock()

        old_phase = MagicMock()
        old_phase.id = "old-phase-id"
        old_phase.title = "Python Basics"
        old_phase.status = "completed"

        db.query.return_value.filter.return_value.all.return_value = [old_phase]

        progress = MagicMock()
        progress.status = "completed"
        db.query.return_value.filter.return_value.first.return_value = progress

        new_phases = [{"title": "Python Basics", "skills": ["Python"]}]

        result = _preserve_phase_progress(db, user_id, "old-roadmap-id", new_phases)
        assert result["Python Basics"] == "completed"

    def test_preserves_in_progress_status(self):
        db = MagicMock()
        user_id = MagicMock()

        old_phase = MagicMock()
        old_phase.id = "old-phase-id"
        old_phase.title = "Web Dev"
        old_phase.status = "not_started"

        db.query.return_value.filter.return_value.all.return_value = [old_phase]

        progress = MagicMock()
        progress.status = "in_progress"
        db.query.return_value.filter.return_value.first.return_value = progress

        new_phases = [{"title": "Web Dev", "skills": ["HTML"]}]

        result = _preserve_phase_progress(db, user_id, "old-roadmap-id", new_phases)
        assert result["Web Dev"] == "in_progress"

    def test_no_preservation_for_new_phases(self):
        db = MagicMock()
        user_id = MagicMock()

        old_phase = MagicMock()
        old_phase.id = "old-phase-id"
        old_phase.title = "Old Phase"
        old_phase.status = "completed"

        db.query.return_value.filter.return_value.all.return_value = [old_phase]

        new_phases = [{"title": "New Phase", "skills": ["New Skill"]}]

        result = _preserve_phase_progress(db, user_id, "old-roadmap-id", new_phases)
        assert "New Phase" not in result

from app.services.opportunity_matching import match_opportunity_skills


class TestMatchOpportunitySkills:
    def test_no_required_skills_returns_zero(self):
        result = match_opportunity_skills([], {"Python": 5})
        assert result["match_score"] == 0
        assert result["matched_skills"] == []
        assert result["partial_skills"] == []
        assert result["missing_skills"] == []

    def test_strong_full_match(self):
        required = ["JavaScript", "React", "Git"]
        user_skills = {"JavaScript": 4, "React": 3, "Git": 3}
        result = match_opportunity_skills(required, user_skills)

        matched_names = {m["skill"] for m in result["matched_skills"]}
        assert matched_names == {"JavaScript", "React", "Git"}
        assert result["missing_skills"] == []
        assert result["match_score"] >= 75

    def test_mixed_matched_partial_missing(self):
        required = ["JavaScript", "React", "Node.js", "Git"]
        user_skills = {"JavaScript": 4, "React": 3, "Git": 2}
        result = match_opportunity_skills(required, user_skills)

        matched_names = {m["skill"] for m in result["matched_skills"]}
        partial_names = {m["skill"] for m in result["partial_skills"]}

        assert "JavaScript" in matched_names
        assert "React" in matched_names
        assert "Git" in partial_names
        assert "Node.js" in result["missing_skills"]

    def test_alias_resolution_used_for_matching(self):
        required = ["JavaScript Development", "React.js", "Node JS"]
        user_skills = {"JavaScript": 5, "React": 5}
        result = match_opportunity_skills(required, user_skills)

        matched_names = {m["skill"] for m in result["matched_skills"]}
        assert "JavaScript Development" in matched_names
        assert "React.js" in matched_names
        assert "Node JS" in result["missing_skills"]

    def test_duplicate_required_skills_counted_once(self):
        required = ["JavaScript", "JavaScript", "CSS", "HTML"]
        user_skills = {"JavaScript": 5, "HTML/CSS": 5}
        result = match_opportunity_skills(required, user_skills)

        # JavaScript de-duped to one requirement; CSS/HTML alias to the same
        # canonical skill so they collapse too.
        total_considered = (
            len(result["matched_skills"]) + len(result["partial_skills"]) + len(result["missing_skills"])
        )
        assert total_considered == 2

    def test_empty_user_profile_all_missing(self):
        required = ["Python", "SQL"]
        result = match_opportunity_skills(required, {})
        assert result["match_score"] == 0
        assert set(result["missing_skills"]) == {"Python", "SQL"}

    def test_proficiency_drives_score_not_just_count(self):
        required = ["Python"]
        low = match_opportunity_skills(required, {"Python": 1})
        high = match_opportunity_skills(required, {"Python": 5})
        assert high["match_score"] > low["match_score"]

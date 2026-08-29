from app.services.skill_normalization import (
    build_alias_index,
    dedupe_skill_names,
    match_skill_to_known,
    normalize_skill_name,
)


class TestNormalizeSkillName:
    def test_known_aliases_collapse_to_same_key(self):
        assert normalize_skill_name("JavaScript") == normalize_skill_name("JS")
        assert normalize_skill_name("JavaScript") == normalize_skill_name("JavaScript Development")
        assert normalize_skill_name("React") == normalize_skill_name("React.js")
        assert normalize_skill_name("React") == normalize_skill_name("React JS")
        assert normalize_skill_name("Node.js") == normalize_skill_name("NodeJS")
        assert normalize_skill_name("Node.js") == normalize_skill_name("Node")
        assert normalize_skill_name("Git") == normalize_skill_name("Git/GitHub")
        assert normalize_skill_name("HTML/CSS") == normalize_skill_name("HTML")
        assert normalize_skill_name("HTML/CSS") == normalize_skill_name("CSS")

    def test_unknown_skill_falls_back_to_cleaned_lowercase(self):
        assert normalize_skill_name("  Some Rare Ability  ") == "some rare ability"

    def test_generic_qualifier_words_stripped_before_fallback(self):
        # "skill" is treated as a generic qualifier so "X Skill" and "X" normalize alike.
        assert normalize_skill_name("Some Rare Skill") == normalize_skill_name("Some Rare")

    def test_empty_input(self):
        assert normalize_skill_name("") == ""
        assert normalize_skill_name(None) == ""


class TestDedupeSkillNames:
    def test_removes_exact_and_alias_duplicates(self):
        result = dedupe_skill_names(["JavaScript", "JavaScript", "JS", "React"])
        assert len(result) == 2
        assert "JavaScript" in result
        assert "React" in result

    def test_ignores_non_string_entries(self):
        result = dedupe_skill_names(["Python", None, 123, "Python"])
        assert result == ["Python"]


class TestAliasIndexMatching:
    def test_exact_alias_match(self):
        index = build_alias_index(["JavaScript", "React", "Git"])
        assert match_skill_to_known("JS", index) == "JavaScript"
        assert match_skill_to_known("React.js", index) == "React"
        assert match_skill_to_known("GitHub", index) == "Git"

    def test_no_match_returns_none(self):
        index = build_alias_index(["Python"])
        assert match_skill_to_known("Kubernetes", index) is None

    def test_case_and_whitespace_insensitive(self):
        index = build_alias_index(["Node.js"])
        assert match_skill_to_known("  nodejs  ", index) == "Node.js"

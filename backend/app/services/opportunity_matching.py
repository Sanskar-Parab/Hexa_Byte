"""Deterministic, explainable skill matching between a user profile and an opportunity.

This is intentionally free of any AI calls — it is the ground truth score that
AI contextual analysis (app.ai.groq_client.analyze_opportunity_match) is only
allowed to nudge, never override (see app.services.opportunity_recommendation).
"""
from typing import Any

from app.services.skill_normalization import (
    build_alias_index,
    dedupe_skill_names,
    match_skill_to_known,
)

# Proficiency (1-5, matching UserSkill.proficiency) -> contribution toward a
# required skill being "covered". Existing product proficiency semantics:
# 1=Beginner, 2=Basic, 3=Intermediate, 4=Advanced, 5=Expert.
PROFICIENCY_WEIGHTS: dict[int, float] = {
    0: 0.0,
    1: 0.35,
    2: 0.55,
    3: 0.75,
    4: 0.9,
    5: 1.0,
}

# A required skill counts as fully "matched" once the user is at least
# Intermediate (3/5); Beginner/Basic (1-2) counts as "partial" progress.
MATCHED_PROFICIENCY_THRESHOLD = 3


def match_opportunity_skills(
    required_skills: list[str],
    user_skill_map: dict[str, int],
) -> dict[str, Any]:
    """Score how well a user's skills cover an opportunity's required skills.

    Args:
        required_skills: raw required-skill strings from the opportunity
            (may contain duplicates/near-duplicates — deduped internally).
        user_skill_map: the authenticated user's skill display name -> proficiency (1-5).

    Returns a dict with a 0-100 `match_score` plus matched/partial/missing
    breakdowns, each explainable back to the specific user proficiency.
    """
    deduped_requirements = dedupe_skill_names(required_skills)

    if not deduped_requirements:
        return {
            "match_score": 0,
            "matched_skills": [],
            "partial_skills": [],
            "missing_skills": [],
        }

    known_index = build_alias_index(list(user_skill_map.keys()))

    matched: list[dict[str, Any]] = []
    partial: list[dict[str, Any]] = []
    missing: list[str] = []

    total_weight = len(deduped_requirements)
    earned_weight = 0.0

    for req in deduped_requirements:
        resolved_name = match_skill_to_known(req, known_index)
        proficiency = user_skill_map.get(resolved_name, 0) if resolved_name else 0
        earned_weight += PROFICIENCY_WEIGHTS.get(proficiency, 0.0)

        if proficiency >= MATCHED_PROFICIENCY_THRESHOLD:
            matched.append({
                "skill": req,
                "user_proficiency": proficiency,
                "requirement": "required",
            })
        elif proficiency >= 1:
            partial.append({
                "skill": req,
                "user_proficiency": proficiency,
                "requirement": "required",
            })
        else:
            missing.append(req)

    score = round((earned_weight / total_weight) * 100) if total_weight else 0

    return {
        "match_score": max(0, min(100, score)),
        "matched_skills": matched,
        "partial_skills": partial,
        "missing_skills": missing,
    }

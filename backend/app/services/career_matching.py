from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.profile import Profile
from app.models.skill import Skill, UserSkill
from app.models.interest import Interest, UserInterest
from app.models.assessment import UserAssessment
from app.models.career import Career


WEIGHTS = {
    "skill_alignment": 0.50,
    "interest_alignment": 0.20,
    "assessment_alignment": 0.20,
    "experience_alignment": 0.10,
}


def _compute_skill_score(user_skills: list[UserSkill], career: Career, all_skills: dict[UUID, Skill]) -> float:
    if not career.required_skills:
        return 0.0

    required = career.required_skills
    importance = career.skill_importance or {}

    total_weight = 0.0
    weighted_score = 0.0

    for skill_name in required:
        weight = importance.get(skill_name, 1.0)
        total_weight += weight

        user_level = 0
        for us in user_skills:
            s = all_skills.get(us.skill_id)
            if s and s.name == skill_name:
                user_level = us.proficiency
                break

        normalized = min(user_level / 5.0, 1.0)
        weighted_score += normalized * weight

    if total_weight == 0:
        return 0.0
    return weighted_score / total_weight


def _compute_interest_score(user_interests: list[UserInterest], career: Career, all_interests: dict[UUID, Interest]) -> float:
    if not user_interests:
        return 0.0

    career_category = (career.category or "").lower()
    matched = 0
    for ui in user_interests:
        interest = all_interests.get(ui.interest_id)
        if interest and interest.category.lower() == career_category:
            matched += 1

    return matched / len(user_interests) if user_interests else 0.0


def _compute_assessment_score(assessments: list[UserAssessment], career: Career) -> float:
    if not assessments:
        return 0.5

    latest = max(assessments, key=lambda a: a.created_at)
    scores = latest.scores or {}

    career_name_lower = (career.name or "").lower()
    category = (career.category or "").lower()

    score_map: dict[str, float] = {}

    if "software" in category or "engineer" in career_name_lower or "developer" in career_name_lower:
        score_map = {
            "technical_interest": 0.3,
            "problem_solving": 0.3,
            "analytical_ability": 0.2,
            "technology_interest": 0.2,
        }
    elif "data" in category or "analyst" in career_name_lower or "scientist" in career_name_lower:
        score_map = {
            "analytical_ability": 0.3,
            "problem_solving": 0.25,
            "technology_interest": 0.25,
            "research_interest": 0.2,
        }
    elif "design" in category or "ux" in career_name_lower or "ui" in career_name_lower:
        score_map = {
            "creativity": 0.35,
            "communication": 0.25,
            "technology_interest": 0.2,
            "problem_solving": 0.2,
        }
    elif "business" in category or "manager" in career_name_lower or "product" in career_name_lower:
        score_map = {
            "business_interest": 0.3,
            "communication": 0.25,
            "problem_solving": 0.25,
            "analytical_ability": 0.2,
        }
    elif "marketing" in category or "content" in career_name_lower:
        score_map = {
            "creativity": 0.3,
            "communication": 0.3,
            "business_interest": 0.2,
            "analytical_ability": 0.2,
        }
    else:
        score_map = {
            "technical_interest": 0.25,
            "problem_solving": 0.25,
            "analytical_ability": 0.25,
            "creativity": 0.25,
        }

    total = 0.0
    for dim, weight in score_map.items():
        val = scores.get(dim, 0.5)
        total += val * weight

    return min(max(total, 0.0), 1.0)


def _compute_experience_score(profile: Profile | None) -> float:
    if not profile:
        return 0.2

    score = 0.2

    if profile.internship_experience and profile.internship_experience.strip():
        score += 0.25
    if profile.work_experience and profile.work_experience.strip():
        score += 0.25
    if profile.projects_count and profile.projects_count > 0:
        score += min(profile.projects_count * 0.1, 0.3)

    return min(score, 1.0)


def _compute_match_confidence(skill_score: float, interest_score: float, assessment_score: float) -> str:
    avg = (skill_score + interest_score + assessment_score) / 3
    if avg >= 0.7:
        return "High"
    elif avg >= 0.4:
        return "Medium"
    return "Low"


def _build_why_matches(user_skills: list[UserSkill], career: Career, all_skills: dict[UUID, Skill]) -> list[str]:
    reasons = []
    if not career.required_skills:
        return reasons

    matched_names = set()
    for us in user_skills:
        s = all_skills.get(us.skill_id)
        if s and s.name in career.required_skills:
            matched_names.add(s.name)

    if matched_names:
        reasons.append(f"You have {len(matched_names)} of the required skills: {', '.join(sorted(matched_names)[:5])}")

    if career.category:
        reasons.append(f"Your interests align with the {career.category} domain")

    return reasons


def _build_strengths(user_skills: list[UserSkill], career: Career, all_skills: dict[UUID, Skill]) -> list[str]:
    strengths = []
    for us in user_skills:
        s = all_skills.get(us.skill_id)
        if s and s.name in (career.required_skills or []) and us.proficiency >= 4:
            strengths.append(f"{s.name} (proficiency: {us.proficiency}/5)")
    return strengths[:5]


def _build_missing_skills(user_skills: list[UserSkill], career: Career, all_skills: dict[UUID, Skill]) -> list[str]:
    user_skill_names = set()
    for us in user_skills:
        s = all_skills.get(us.skill_id)
        if s:
            user_skill_names.add(s.name)

    missing = []
    for skill_name in (career.required_skills or []):
        if skill_name not in user_skill_names:
            importance = (career.skill_importance or {}).get(skill_name, 1.0)
            missing.append({"skill": skill_name, "importance": importance})

    missing.sort(key=lambda x: x["importance"], reverse=True)
    return [m["skill"] for m in missing[:5]]


def compute_career_recommendations(
    db: Session,
    user: User,
    top_n: int = 5,
) -> list[dict[str, Any]]:
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user.id).all()
    user_interests = db.query(UserInterest).filter(UserInterest.user_id == user.id).all()
    assessments = db.query(UserAssessment).filter(UserAssessment.user_id == user.id).all()

    all_skills = {s.id: s for s in db.query(Skill).all()}
    all_interests = {i.id: i for i in db.query(Interest).all()}
    careers = db.query(Career).all()

    results = []
    for career in careers:
        skill_score = _compute_skill_score(user_skills, career, all_skills)
        interest_score = _compute_interest_score(user_interests, career, all_interests)
        assessment_score = _compute_assessment_score(assessments, career)
        experience_score = _compute_experience_score(profile)

        match_score = (
            skill_score * WEIGHTS["skill_alignment"]
            + interest_score * WEIGHTS["interest_alignment"]
            + assessment_score * WEIGHTS["assessment_alignment"]
            + experience_score * WEIGHTS["experience_alignment"]
        )

        confidence = _compute_match_confidence(skill_score, interest_score, assessment_score)
        why_matches = _build_why_matches(user_skills, career, all_skills)
        strengths = _build_strengths(user_skills, career, all_skills)
        missing_skills = _build_missing_skills(user_skills, career, all_skills)

        results.append({
            "career_id": career.id,
            "career_name": career.name,
            "match_score": round(match_score, 4),
            "confidence": confidence,
            "why_matches": why_matches,
            "strengths": strengths,
            "missing_skills": missing_skills,
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:top_n]

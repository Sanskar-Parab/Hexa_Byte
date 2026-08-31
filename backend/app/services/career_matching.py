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

# A required skill counts as already a "strength" once the user is at least
# Intermediate (3/5) — kept in sync with _build_strengths. Skill-gap/blocker
# logic below must exclude skills at or above this threshold, otherwise the
# same skill can show up simultaneously as a "Why it fits" strength and a
# "Skill gap"/"Biggest blocker", which is contradictory in the UI.
STRENGTH_PROFICIENCY_THRESHOLD = 3


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


def _build_why_matches(
    user_skills: list[UserSkill],
    career: Career,
    all_skills: dict[UUID, Skill],
    interest_score: float = 0.0,
    assessment_score: float = 0.0,
) -> list[str]:
    reasons = []
    if not career.required_skills:
        return reasons

    importance = career.skill_importance or {}
    matched_strong = []
    matched_developing = []

    for us in user_skills:
        s = all_skills.get(us.skill_id)
        if s and s.name in career.required_skills:
            if us.proficiency >= 4:
                matched_strong.append(s.name)
            elif us.proficiency >= 2:
                matched_developing.append(s.name)

    total_required = len(career.required_skills)
    total_matched = len(matched_strong) + len(matched_developing)

    if matched_strong:
        reasons.append(
            f"You have strong proficiency in {len(matched_strong)} key skills: "
            f"{', '.join(sorted(matched_strong)[:5])}"
        )

    if matched_developing:
        reasons.append(
            f"You have foundational knowledge in {len(matched_developing)} skills: "
            f"{', '.join(sorted(matched_developing)[:5])}"
        )

    if total_matched == 0 and total_required > 0:
        reasons.append(f"This career requires {total_required} skills you haven't listed yet")

    if career.category:
        reasons.append(f"Your interests align with the {career.category} domain")

    if assessment_score > 0.6:
        reasons.append("Your assessment results show strong aptitude for this career path")

    return reasons[:5]


def _build_strengths(
    user_skills: list[UserSkill],
    career: Career,
    all_skills: dict[UUID, Skill],
) -> list[str]:
    importance = career.skill_importance or {}
    strengths = []

    for us in user_skills:
        s = all_skills.get(us.skill_id)
        if s and s.name in (career.required_skills or []) and us.proficiency >= STRENGTH_PROFICIENCY_THRESHOLD:
            skill_importance = importance.get(s.name, 1.0)
            weighted = us.proficiency * skill_importance
            level_name = _get_level_name(us.proficiency)
            strengths.append({
                "text": f"{s.name} — {level_name} ({us.proficiency}/5)",
                "weighted": weighted,
            })

    strengths.sort(key=lambda x: x["weighted"], reverse=True)
    return [item["text"] for item in strengths[:5]]


def _get_level_name(proficiency: int) -> str:
    levels = {1: "Beginner", 2: "Basic", 3: "Intermediate", 4: "Advanced", 5: "Expert"}
    return levels.get(proficiency, "Unknown")


def _build_missing_skills(
    user_skills: list[UserSkill],
    career: Career,
    all_skills: dict[UUID, Skill],
) -> list[str]:
    user_skill_map: dict[str, int] = {}
    for us in user_skills:
        s = all_skills.get(us.skill_id)
        if s:
            user_skill_map[s.name] = us.proficiency

    importance = career.skill_importance or {}
    gaps = []

    for skill_name in (career.required_skills or []):
        current = user_skill_map.get(skill_name, 0)
        if current >= STRENGTH_PROFICIENCY_THRESHOLD:
            # Already a demonstrated strength for this career — not a gap.
            continue
        gap_size = 5 - current
        skill_importance = importance.get(skill_name, 1.0)
        priority_score = gap_size * skill_importance
        severity = _gap_severity(gap_size)

        gaps.append({
            "skill": skill_name,
            "current_level": current,
            "gap_size": gap_size,
            "severity": severity,
            "importance": skill_importance,
            "priority_score": priority_score,
        })

    gaps.sort(key=lambda x: x["priority_score"], reverse=True)
    return [g["skill"] for g in gaps[:5]]


def _gap_severity(gap_size: int) -> str:
    if gap_size <= 1:
        return "Low"
    elif gap_size <= 3:
        return "Medium"
    return "High"


def _build_biggest_blocker(
    user_skills: list[UserSkill],
    career: Career,
    all_skills: dict[UUID, Skill],
) -> str | None:
    if not career.required_skills:
        return None

    user_skill_map: dict[str, int] = {}
    for us in user_skills:
        s = all_skills.get(us.skill_id)
        if s:
            user_skill_map[s.name] = us.proficiency

    importance = career.skill_importance or {}
    best_gap = None
    best_priority = -1.0

    for skill_name in career.required_skills:
        current = user_skill_map.get(skill_name, 0)
        if current >= STRENGTH_PROFICIENCY_THRESHOLD:
            # Already a demonstrated strength for this career — not a blocker.
            continue
        gap_size = 5 - current
        skill_importance = importance.get(skill_name, 1.0)
        priority = gap_size * skill_importance

        if priority > best_priority:
            best_priority = priority
            best_gap = skill_name

    if best_gap and user_skill_map.get(best_gap, 0) < 5:
        current = user_skill_map.get(best_gap, 0)
        return f"{best_gap} (current: {current}/5, importance: {importance.get(best_gap, 1.0):.0%})"
    return None


def _build_recommended_action(
    user_skills: list[UserSkill],
    career: Career,
    all_skills: dict[UUID, Skill],
) -> str:
    biggest = _build_biggest_blocker(user_skills, career, all_skills)
    if not biggest:
        return "You have all required skills. Focus on gaining practical experience through projects."

    blocker_skill = biggest.split(" (")[0]
    learning_sequence = career.learning_sequence or []

    for phase in learning_sequence:
        phase_skills = phase.get("skills", [])
        if blocker_skill in phase_skills:
            return f"Start with \"{phase.get('title', 'Phase 1')}\" — {phase.get('objective', 'Build foundational skills')}"

    return f"Focus on developing {blocker_skill} — it is the highest-priority skill gap for this career."


def _build_skill_details(
    user_skills: list[UserSkill],
    career: Career,
    all_skills: dict[UUID, Skill],
) -> list[dict[str, Any]]:
    if not career.required_skills:
        return []

    importance = career.skill_importance or {}
    user_skill_map: dict[str, tuple[int, str]] = {}

    for us in user_skills:
        s = all_skills.get(us.skill_id)
        if s:
            user_skill_map[s.name] = (us.proficiency, us.confidence or "LOW")

    details = []
    for skill_name in career.required_skills:
        proficiency, confidence = user_skill_map.get(skill_name, (0, "LOW"))
        skill_importance = importance.get(skill_name, 1.0)
        gap = 5 - proficiency

        if proficiency >= 4:
            status = "strong"
        elif proficiency >= 2:
            status = "developing"
        else:
            status = "gap"

        details.append({
            "skill_name": skill_name,
            "importance": skill_importance,
            "user_proficiency": proficiency,
            "evidence_confidence": confidence,
            "gap": gap,
            "status": status,
        })

    details.sort(key=lambda x: x["importance"], reverse=True)
    return details


def _build_user_current_skills(
    user_skills: list[UserSkill],
    career: Career,
    all_skills: dict[UUID, Skill],
) -> list[dict[str, str]]:
    current = []
    for us in user_skills:
        s = all_skills.get(us.skill_id)
        if s and s.name in (career.required_skills or []):
            current.append({
                "name": s.name,
                "proficiency": str(us.proficiency),
                "confidence": us.confidence or "LOW",
            })
    current.sort(key=lambda x: int(x["proficiency"]), reverse=True)
    return current


def compute_career_recommendations(
    db: Session,
    user: User,
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
        why_matches = _build_why_matches(user_skills, career, all_skills, interest_score, assessment_score)
        strengths = _build_strengths(user_skills, career, all_skills)
        missing_skills = _build_missing_skills(user_skills, career, all_skills)
        biggest_blocker = _build_biggest_blocker(user_skills, career, all_skills)
        recommended_action = _build_recommended_action(user_skills, career, all_skills)

        results.append({
            "career_id": career.id,
            "career_name": career.name,
            "match_score": round(match_score, 4),
            "confidence": confidence,
            "why_matches": why_matches,
            "strengths": strengths,
            "missing_skills": missing_skills,
            "biggest_blocker": biggest_blocker,
            "recommended_action": recommended_action,
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results


def compute_career_intelligence(
    db: Session,
    user: User,
    career_id: UUID,
) -> dict[str, Any] | None:
    career = db.query(Career).filter(Career.id == career_id).first()
    if not career:
        return None

    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user.id).all()
    user_interests = db.query(UserInterest).filter(UserInterest.user_id == user.id).all()
    assessments = db.query(UserAssessment).filter(UserAssessment.user_id == user.id).all()

    all_skills = {s.id: s for s in db.query(Skill).all()}
    all_interests = {i.id: i for i in db.query(Interest).all()}

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
    why_matches = _build_why_matches(user_skills, career, all_skills, interest_score, assessment_score)
    strengths = _build_strengths(user_skills, career, all_skills)
    missing_skills = _build_missing_skills(user_skills, career, all_skills)
    biggest_blocker = _build_biggest_blocker(user_skills, career, all_skills)
    recommended_action = _build_recommended_action(user_skills, career, all_skills)
    skill_details = _build_skill_details(user_skills, career, all_skills)
    user_current_skills = _build_user_current_skills(user_skills, career, all_skills)

    return {
        "career_id": career.id,
        "career_name": career.name,
        "match_score": round(match_score, 4),
        "confidence": confidence,
        "why_matches": why_matches,
        "strengths": strengths,
        "skill_gaps": missing_skills,
        "biggest_blocker": biggest_blocker,
        "recommended_action": recommended_action,
        "skill_details": skill_details,
        "user_current_skills": user_current_skills,
        "learning_sequence": career.learning_sequence or [],
        "description": career.description,
        "required_skills": career.required_skills or [],
        "optional_skills": career.optional_skills or [],
    }

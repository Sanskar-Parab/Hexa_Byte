from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.skill import UserSkill, Skill
from app.models.profile import Profile
from app.models.assessment import UserAssessment
from app.models.progress import UserProgress
from app.models.career import Career


def calculate_readiness(
    db: Session,
    user_id: UUID,
    career_id: UUID | None = None,
) -> dict[str, Any]:
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    assessments = db.query(UserAssessment).filter(UserAssessment.user_id == user_id).all()
    progress_items = db.query(UserProgress).filter(UserProgress.user_id == user_id).all()
    all_skills = {s.id: s for s in db.query(Skill).all()}

    technical_skills_score = 0.0
    if user_skills:
        avg = sum(us.proficiency for us in user_skills) / len(user_skills)
        technical_skills_score = min(avg / 5.0, 1.0)

    project_items = [p for p in progress_items if p.item_type == "project"]
    completed_projects = [p for p in project_items if p.status == "completed"]
    project_completion = 0.0
    if project_items:
        project_completion = len(completed_projects) / len(project_items)

    core_knowledge = 0.0
    if assessments:
        latest = max(assessments, key=lambda a: a.created_at)
        scores = latest.scores or {}
        vals = list(scores.values())
        if vals:
            core_knowledge = sum(vals) / len(vals)

    communication_skills = 0.0
    if assessments:
        latest = max(assessments, key=lambda a: a.created_at)
        scores = latest.scores or {}
        communication_skills = scores.get("communication", 0.5)

    overall = (
        technical_skills_score * 0.35
        + project_completion * 0.25
        + core_knowledge * 0.25
        + communication_skills * 0.15
    )

    breakdown = {
        "technical_skills": {
            "score": round(technical_skills_score * 100, 1),
            "weight": 0.35,
            "details": f"{len(user_skills)} skills tracked, avg proficiency: {technical_skills_score * 5:.1f}/5",
        },
        "project_completion": {
            "score": round(project_completion * 100, 1),
            "weight": 0.25,
            "details": f"{len(completed_projects)}/{len(project_items)} projects completed",
        },
        "core_knowledge": {
            "score": round(core_knowledge * 100, 1),
            "weight": 0.25,
            "details": f"Assessment scores across {len(core_knowledge) if isinstance(core_knowledge, dict) else 8} dimensions",
        },
        "communication": {
            "score": round(communication_skills * 100, 1),
            "weight": 0.15,
            "details": "Based on assessment communication score",
        },
    }

    career_specific = None
    if career_id:
        career = db.query(Career).filter(Career.id == career_id).first()
        if career:
            required = career.required_skills or []
            user_skill_names = set()
            for us in user_skills:
                s = all_skills.get(us.skill_id)
                if s:
                    user_skill_names.add(s.name)

            matched = [sk for sk in required if sk in user_skill_names]
            missing = [sk for sk in required if sk not in user_skill_names]

            career_specific = {
                "career_name": career.name,
                "required_skills_count": len(required),
                "matched_skills_count": len(matched),
                "missing_skills_count": len(missing),
                "match_percentage": round(len(matched) / len(required) * 100, 1) if required else 0,
                "missing_skills": missing[:10],
            }

    return {
        "overall_readiness": round(overall * 100, 1),
        "breakdown": breakdown,
        "career_specific": career_specific,
        "recommendations": _generate_recommendations(technical_skills_score, project_completion, core_knowledge, communication_skills),
    }


def _generate_recommendations(
    technical: float,
    projects: float,
    knowledge: float,
    communication: float,
) -> list[str]:
    recs = []
    if technical < 0.4:
        recs.append("Focus on building fundamental technical skills through structured learning")
    if projects < 0.3:
        recs.append("Complete more hands-on projects to build practical experience")
    if knowledge < 0.4:
        recs.append("Take the career assessment to identify your strengths and interests")
    if communication < 0.4:
        recs.append("Practice presenting your work and explaining technical concepts")
    if not recs:
        recs.append("You're on track! Continue building skills and completing projects")
    return recs

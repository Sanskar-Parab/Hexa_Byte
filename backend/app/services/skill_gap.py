from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.skill import Skill, UserSkill
from app.models.career import Career


def analyze_skill_gaps(
    db: Session,
    user_id: UUID,
    career_id: UUID,
) -> dict[str, Any]:
    career = db.query(Career).filter(Career.id == career_id).first()
    if not career:
        return {"error": "Career not found"}

    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    all_skills = {s.name: s for s in db.query(Skill).all()}

    user_skill_map: dict[str, int] = {}
    for us in user_skills:
        skill = all_skills.get(
            next((sn for sn, s in all_skills.items() if s.id == us.skill_id), None)
        )
        if skill:
            user_skill_map[skill.name] = us.proficiency

    required_skills = career.required_skills or []
    skill_importance = career.skill_importance or {}
    optional_skills = career.optional_skills or []

    gaps = []
    for skill_name in required_skills:
        current_level = user_skill_map.get(skill_name, 0)
        target_level = 5
        gap_size = target_level - current_level
        importance = skill_importance.get(skill_name, 1.0)

        if gap_size <= 1:
            gap_severity = "Low"
        elif gap_size <= 3:
            gap_severity = "Medium"
        else:
            gap_severity = "High"

        priority_score = gap_size * importance

        gaps.append({
            "skill": skill_name,
            "current_level": current_level,
            "target_level": target_level,
            "gap_size": gap_size,
            "gap_severity": gap_severity,
            "importance": importance,
            "priority_score": round(priority_score, 2),
        })

    for skill_name in optional_skills:
        if skill_name not in [g["skill"] for g in gaps]:
            current_level = user_skill_map.get(skill_name, 0)
            gap_size = 5 - current_level
            if gap_size > 0:
                gaps.append({
                    "skill": skill_name,
                    "current_level": current_level,
                    "target_level": 5,
                    "gap_size": gap_size,
                    "gap_severity": "Low" if gap_size <= 2 else "Medium",
                    "importance": 0.5,
                    "priority_score": round(gap_size * 0.5, 2),
                })

    gaps.sort(key=lambda x: x["priority_score"], reverse=True)

    high_gaps = [g for g in gaps if g["gap_severity"] == "High"]
    medium_gaps = [g for g in gaps if g["gap_severity"] == "Medium"]
    low_gaps = [g for g in gaps if g["gap_severity"] == "Low"]

    skills_with_data = [g for g in gaps if g["current_level"] > 0]
    overall_gap = sum(g["gap_size"] for g in gaps) / len(gaps) if gaps else 0

    return {
        "career_name": career.name,
        "career_id": str(career.id),
        "total_skills_required": len(required_skills),
        "skills_with_data": len(skills_with_data),
        "overall_gap_score": round(overall_gap, 2),
        "gaps": gaps,
        "high_priority": high_gaps,
        "medium_priority": medium_gaps,
        "low_priority": low_gaps,
        "summary": {
            "total_gaps": len(gaps),
            "high_count": len(high_gaps),
            "medium_count": len(medium_gaps),
            "low_count": len(low_gaps),
        },
    }

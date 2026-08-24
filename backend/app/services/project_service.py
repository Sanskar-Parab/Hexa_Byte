from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.project import Project, RecommendedProject
from app.services.skill_gap import analyze_skill_gaps


def get_project_recommendations(
    db: Session,
    user_id: UUID,
    career_id: UUID,
    top_n: int = 3,
) -> list[dict[str, Any]]:
    skill_gaps = analyze_skill_gaps(db, user_id, career_id)
    gaps = skill_gaps.get("gaps", [])
    gap_skills = {g["skill"] for g in gaps if g["gap_size"] > 0}

    all_projects = db.query(Project).all()
    existing = {
        rp.project_id
        for rp in db.query(RecommendedProject).filter(
            RecommendedProject.user_id == user_id,
            RecommendedProject.career_id == career_id,
        ).all()
    }

    scored_projects = []
    for project in all_projects:
        if project.id in existing:
            continue

        project_skills = set(project.skills_developed or [])
        overlap = project_skills & gap_skills
        coverage = len(overlap) / len(gap_skills) if gap_skills else 0
        difficulty_bonus = {"beginner": 0.3, "intermediate": 0.5, "advanced": 0.7}.get(
            project.difficulty, 0.4
        )
        score = coverage * 0.7 + difficulty_bonus * 0.3

        scored_projects.append({
            "project": project,
            "score": round(score, 4),
            "covers_skills": list(overlap),
        })

    scored_projects.sort(key=lambda x: x["score"], reverse=True)
    return scored_projects[:top_n]


def save_project_recommendations(
    db: Session,
    user_id: UUID,
    career_id: UUID,
    project_ids: list[UUID],
) -> list[RecommendedProject]:
    saved = []
    for pid in project_ids:
        existing = db.query(RecommendedProject).filter(
            RecommendedProject.user_id == user_id,
            RecommendedProject.project_id == pid,
            RecommendedProject.career_id == career_id,
        ).first()
        if not existing:
            rec = RecommendedProject(
                user_id=user_id,
                project_id=pid,
                career_id=career_id,
                status="recommended",
            )
            db.add(rec)
            saved.append(rec)
    db.commit()
    return saved

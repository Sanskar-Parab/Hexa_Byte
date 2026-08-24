from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.models.project import Project, RecommendedProject
from app.schemas.project import ProjectResponse, RecommendedProjectResponse
from app.services.project_service import get_project_recommendations, save_project_recommendations
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/recommendations")
def list_recommendations(
    career_id: UUID = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not career_id:
        raise HTTPException(status_code=400, detail="career_id is required")

    results = get_project_recommendations(db, current_user.id, career_id)

    saved = save_project_recommendations(
        db, current_user.id, career_id, [r["project"].id for r in results]
    )

    return [
        {
            "id": str(saved[i].id) if i < len(saved) else None,
            "project": {
                "id": str(r["project"].id),
                "title": r["project"].title,
                "description": r["project"].description,
                "difficulty": r["project"].difficulty,
                "skills_developed": r["project"].skills_developed,
                "expected_outcome": r["project"].expected_outcome,
                "estimated_duration_weeks": r["project"].estimated_duration_weeks,
                "portfolio_value": r["project"].portfolio_value,
            },
            "career_id": str(career_id),
            "match_score": r["score"],
            "covers_skills": r["covers_skills"],
            "status": "recommended",
        }
        for i, r in enumerate(results)
    ]


@router.post("/{project_id}/status")
def update_project_status(
    project_id: UUID,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if status not in ("recommended", "in_progress", "completed"):
        raise HTTPException(status_code=400, detail="Invalid status")

    rec = db.query(RecommendedProject).filter(
        RecommendedProject.id == project_id,
        RecommendedProject.user_id == current_user.id,
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommended project not found")

    rec.status = status
    db.commit()
    return {"message": "Project status updated", "status": status}

from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.models.roadmap import Roadmap, RoadmapPhase
from app.models.progress import UserProgress
from app.schemas.roadmap import RoadmapResponse, RoadmapCreate, RoadmapPhaseResponse
from app.services.roadmap_service import generate_roadmap
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/roadmap", tags=["roadmap"])

VALID_TRANSITIONS = {
    "not_started": ["in_progress"],
    "in_progress": ["completed", "not_started"],
    "completed": ["not_started", "in_progress"],
}


def _validate_status_transition(current_status: str, new_status: str) -> bool:
    allowed = VALID_TRANSITIONS.get(current_status, [])
    return new_status in allowed


@router.post("/generate")
async def generate_roadmap_endpoint(
    request: RoadmapCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await generate_roadmap(
        db=db,
        user_id=current_user.id,
        career_id=request.career_id,
        user_name=current_user.name,
        use_ai=False,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("", response_model=RoadmapResponse)
def get_current_roadmap(
    career_id: UUID = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Roadmap).filter(Roadmap.user_id == current_user.id)
    if career_id:
        query = query.filter(Roadmap.career_id == career_id)

    roadmap = query.order_by(Roadmap.created_at.desc()).first()
    if not roadmap:
        raise HTTPException(status_code=404, detail="No roadmap found")

    phases = sorted(roadmap.phases, key=lambda x: x.phase_number)
    career = roadmap.career

    return RoadmapResponse(
        id=roadmap.id,
        career_id=roadmap.career_id,
        career_name=career.name if career else None,
        summary=roadmap.summary,
        phases=[
            RoadmapPhaseResponse(
                id=p.id,
                phase_number=p.phase_number,
                title=p.title,
                objective=p.objective,
                skills=p.skills,
                activities=p.activities,
                project=p.project,
                duration_weeks=p.duration_weeks,
                completion_criteria=p.completion_criteria,
                status=p.status,
                adaptation_mode=p.adaptation_mode,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in phases
        ],
        created_at=roadmap.created_at,
        updated_at=roadmap.updated_at,
    )


@router.put("/phase/{phase_id}/status")
def update_phase_status(
    phase_id: UUID,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if status not in ("not_started", "in_progress", "completed"):
        raise HTTPException(status_code=400, detail="Invalid status")

    phase = db.query(RoadmapPhase).filter(RoadmapPhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")

    roadmap = db.query(Roadmap).filter(
        Roadmap.id == phase.roadmap_id,
        Roadmap.user_id == current_user.id,
    ).first()
    if not roadmap:
        raise HTTPException(status_code=403, detail="Not authorized")

    if phase.adaptation_mode == "skipped" and status != "not_started":
        raise HTTPException(status_code=400, detail="Cannot update status of skipped phase")

    if not _validate_status_transition(phase.status, status):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{phase.status}' to '{status}'",
        )

    phase.status = status

    now = datetime.utcnow()
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.item_type == "phase",
        UserProgress.item_id == str(phase.id),
    ).first()

    if progress:
        progress.status = status
        if status == "in_progress" and not progress.started_at:
            progress.started_at = now
        if status == "completed" and not progress.completed_at:
            progress.completed_at = now
    else:
        progress = UserProgress(
            user_id=current_user.id,
            item_type="phase",
            item_id=str(phase.id),
            status=status,
            started_at=now if status == "in_progress" else None,
            completed_at=now if status == "completed" else None,
        )
        db.add(progress)

    db.commit()
    return {"message": "Phase status updated", "status": status}

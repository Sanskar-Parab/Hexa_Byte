from uuid import UUID
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.services.skill_gap import analyze_skill_gaps
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/skill-gap", tags=["skill-gap"])


class SkillGapRequest(BaseModel):
    career_id: UUID


@router.post("/analyze")
def analyze_gaps(
    request: SkillGapRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = analyze_skill_gaps(db, current_user.id, request.career_id)
    return result

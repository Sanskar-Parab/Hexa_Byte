from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.services.next_best_action import compute_next_best_action
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/next-best-action", tags=["next-best-action"])


class NextBestActionRequest(BaseModel):
    career_id: Optional[UUID] = None


@router.post("")
def get_next_best_action(
    request: NextBestActionRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    career_id = request.career_id if request else None
    result = compute_next_best_action(db, current_user.id, career_id)
    return result

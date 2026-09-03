from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.services.outcome_timeline import build_outcome_timeline
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/outcomes", tags=["outcome-timeline"])


@router.get("/timeline")
def get_outcome_timeline(
    training_enrollment_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The authenticated user's post-training outcome timeline: training,
    placement, employment, check-ins, retention, salary progression, and
    training relevance over time. With no training_enrollment_id given, uses
    the user's most recent training enrollment (if any)."""
    result = build_outcome_timeline(db, current_user.id, training_enrollment_id=training_enrollment_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Training enrollment not found")
    return result

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.schemas.progress import ProgressUpdate
from app.services.progress_service import update_progress, get_progress_dashboard
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_progress_dashboard(db, current_user.id)


@router.post("/update")
def update(
    data: ProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_progress(db, current_user.id, data.item_type, data.item_id, data.status)

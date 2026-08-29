from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.career import Career
from app.models.user import User
from app.schemas.opportunity import OpportunityRecommendationsResponse
from app.services.opportunity_recommendation import get_recommendations
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])


@router.get("/recommendations", response_model=OpportunityRecommendationsResponse)
def list_opportunity_recommendations(
    type: str = Query("all", pattern="^(all|internship|job)$"),
    limit: int = Query(10, ge=1, le=50),
    min_match: int = Query(0, ge=0, le=100),
    career_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Personalized job/internship recommendations from live provider data
    (RapidAPI "Internships API" — Career Site + Job Board endpoints).

    The user is always derived from the authenticated JWT (`current_user`) —
    never from a client-supplied user_id — so this endpoint can only ever
    return recommendations based on the caller's own demonstrated skills.
    """
    target_career = None
    if career_id:
        career = db.query(Career).filter(Career.id == career_id).first()
        if career:
            target_career = career.name

    return get_recommendations(
        db=db,
        user_id=current_user.id,
        opportunity_type=type,
        limit=limit,
        min_match=min_match,
        target_career=target_career,
    )

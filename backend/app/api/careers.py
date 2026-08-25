from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.models.career import Career, CareerRecommendation
from app.models.skill import UserSkill, Skill
from app.models.interest import UserInterest, Interest
from app.schemas.career import CareerResponse, CareerRecommendationResponse, CareerIntelligenceResponse
from app.services.career_matching import compute_career_recommendations, compute_career_intelligence
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/careers", tags=["careers"])


@router.get("", response_model=list[CareerResponse])
def list_careers(db: Session = Depends(get_db)):
    return db.query(Career).all()


@router.post("/recommend", response_model=list[CareerRecommendationResponse])
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    raw = compute_career_recommendations(db, current_user)

    results = []
    for rec in raw:
        career_id = rec["career_id"]
        existing = db.query(CareerRecommendation).filter(
            CareerRecommendation.user_id == current_user.id,
            CareerRecommendation.career_id == career_id,
        ).first()

        if existing:
            existing.match_score = rec["match_score"]
            existing.confidence = rec["confidence"]
            existing.why_matches = rec["why_matches"]
            existing.strengths = rec["strengths"]
            existing.missing_skills = rec["missing_skills"]
            db_obj = existing
        else:
            db_obj = CareerRecommendation(
                user_id=current_user.id,
                career_id=career_id,
                match_score=rec["match_score"],
                confidence=rec["confidence"],
                why_matches=rec["why_matches"],
                strengths=rec["strengths"],
                missing_skills=rec["missing_skills"],
            )
            db.add(db_obj)

        db.flush()
        db.refresh(db_obj)

        career = db.query(Career).filter(Career.id == career_id).first()
        results.append(CareerRecommendationResponse(
            id=db_obj.id,
            career_id=career_id,
            career_name=career.name if career else None,
            match_score=db_obj.match_score,
            confidence=db_obj.confidence,
            why_it_matches=db_obj.why_matches,
            strengths=db_obj.strengths,
            skill_gaps=db_obj.missing_skills,
            biggest_blocker=rec.get("biggest_blocker"),
            recommended_action=rec.get("recommended_action"),
            created_at=db_obj.created_at,
        ))

    db.commit()
    return results


@router.get("/recommendations", response_model=list[CareerRecommendationResponse])
def get_stored_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recs = db.query(CareerRecommendation).filter(
        CareerRecommendation.user_id == current_user.id
    ).order_by(CareerRecommendation.match_score.desc()).all()

    results = []
    for rec in recs:
        career = db.query(Career).filter(Career.id == rec.career_id).first()
        results.append(CareerRecommendationResponse(
            id=rec.id,
            career_id=rec.career_id,
            career_name=career.name if career else None,
            match_score=rec.match_score,
            confidence=rec.confidence,
            why_it_matches=rec.why_matches,
            strengths=rec.strengths,
            skill_gaps=rec.missing_skills,
            biggest_blocker=None,
            recommended_action=None,
            created_at=rec.created_at,
        ))
    return results


@router.get("/{career_id}", response_model=CareerResponse)
def get_career(career_id: UUID, db: Session = Depends(get_db)):
    career = db.query(Career).filter(Career.id == career_id).first()
    if not career:
        raise HTTPException(status_code=404, detail="Career not found")
    return career


@router.get("/{career_id}/intelligence", response_model=CareerIntelligenceResponse)
def get_career_intelligence(
    career_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = compute_career_intelligence(db, current_user, career_id)
    if not result:
        raise HTTPException(status_code=404, detail="Career not found")
    return result

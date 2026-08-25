from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.skill import Skill, UserSkill
from app.models.interest import Interest, UserInterest
from app.schemas.profile import ProfileCreate, ProfileResponse, OnboardingData
from app.services.evidence_service import create_manual_evidence
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.post("", response_model=ProfileResponse)
def create_or_update_profile(
    profile_data: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if existing:
        for field, value in profile_data.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    profile = Profile(user_id=current_user.id, **profile_data.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("", response_model=ProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.post("/onboarding")
def complete_onboarding(
    onboarding_data: OnboardingData,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if existing:
        for field, value in onboarding_data.profile.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
    else:
        profile = Profile(user_id=current_user.id, **onboarding_data.profile.model_dump())
        db.add(profile)
    db.flush()

    level_names = {1: "Beginner", 2: "Basic", 3: "Intermediate", 4: "Advanced", 5: "Expert"}
    for skill_data in onboarding_data.skills:
        skill_name = skill_data.get("name", "")
        proficiency = skill_data.get("proficiency", 3)
        skill = db.query(Skill).filter(Skill.name == skill_name).first()
        if skill:
            existing_us = db.query(UserSkill).filter(
                UserSkill.user_id == current_user.id,
                UserSkill.skill_id == skill.id,
            ).first()
            if existing_us:
                existing_us.proficiency = proficiency
                existing_us.level_name = level_names.get(proficiency)
            else:
                us = UserSkill(
                    user_id=current_user.id,
                    skill_id=skill.id,
                    proficiency=proficiency,
                    level_name=level_names.get(proficiency),
                )
                db.add(us)
            db.flush()
            create_manual_evidence(
                db=db,
                user_id=current_user.id,
                skill_id=skill.id,
                proficiency=proficiency,
            )

    for interest_name in onboarding_data.interests:
        interest = db.query(Interest).filter(Interest.name == interest_name).first()
        if interest:
            existing_ui = db.query(UserInterest).filter(
                UserInterest.user_id == current_user.id,
                UserInterest.interest_id == interest.id,
            ).first()
            if not existing_ui:
                db.add(UserInterest(user_id=current_user.id, interest_id=interest.id))

    db.commit()
    return {"message": "Onboarding completed successfully"}

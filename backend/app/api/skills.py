from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.models.skill import Skill, UserSkill
from app.schemas.skill import SkillResponse, UserSkillCreate, UserSkillResponse
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("", response_model=list[SkillResponse])
def list_all_skills(db: Session = Depends(get_db)):
    return db.query(Skill).all()


@router.get("/user", response_model=list[UserSkillResponse])
def list_user_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == current_user.id).all()
    all_skills = {s.id: s for s in db.query(Skill).all()}
    result = []
    for us in user_skills:
        skill = all_skills.get(us.skill_id)
        result.append(UserSkillResponse(
            id=us.id,
            skill_id=us.skill_id,
            skill_name=skill.name if skill else None,
            proficiency=us.proficiency,
            created_at=us.created_at,
        ))
    return result


@router.post("", response_model=UserSkillResponse)
def add_user_skill(
    skill_data: UserSkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skill = db.query(Skill).filter(Skill.id == skill_data.skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    existing = db.query(UserSkill).filter(
        UserSkill.user_id == current_user.id,
        UserSkill.skill_id == skill_data.skill_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Skill already added")

    user_skill = UserSkill(
        user_id=current_user.id,
        skill_id=skill_data.skill_id,
        proficiency=skill_data.proficiency,
    )
    db.add(user_skill)
    db.commit()
    db.refresh(user_skill)

    return UserSkillResponse(
        id=user_skill.id,
        skill_id=user_skill.skill_id,
        skill_name=skill.name,
        proficiency=user_skill.proficiency,
        created_at=user_skill.created_at,
    )


@router.put("/{skill_id}", response_model=UserSkillResponse)
def update_user_skill(
    skill_id: UUID,
    skill_data: UserSkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_skill = db.query(UserSkill).filter(
        UserSkill.id == skill_id,
        UserSkill.user_id == current_user.id,
    ).first()
    if not user_skill:
        raise HTTPException(status_code=404, detail="User skill not found")

    user_skill.proficiency = skill_data.proficiency
    db.commit()
    db.refresh(user_skill)

    skill = db.query(Skill).filter(Skill.id == user_skill.skill_id).first()
    return UserSkillResponse(
        id=user_skill.id,
        skill_id=user_skill.skill_id,
        skill_name=skill.name if skill else None,
        proficiency=user_skill.proficiency,
        created_at=user_skill.created_at,
    )


@router.delete("/{skill_id}")
def delete_user_skill(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_skill = db.query(UserSkill).filter(
        UserSkill.id == skill_id,
        UserSkill.user_id == current_user.id,
    ).first()
    if not user_skill:
        raise HTTPException(status_code=404, detail="User skill not found")

    db.delete(user_skill)
    db.commit()
    return {"message": "Skill removed"}

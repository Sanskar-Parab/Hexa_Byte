import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.models.skill import Skill, UserSkill
from app.models.skill_evidence import SkillEvidence
from app.schemas.skill_evidence import EvidenceResponse, SkillEvidenceResponse
from app.services.evidence_service import get_evidence_for_skill, get_all_evidence_for_user
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/evidence", tags=["evidence"])


@router.get("", response_model=list[SkillEvidenceResponse])
def list_all_evidence(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    evidence_records = get_all_evidence_for_user(db, current_user.id)

    evidence_by_skill: dict[str, list[SkillEvidence]] = {}
    for ev in evidence_records:
        key = str(ev.skill_id)
        if key not in evidence_by_skill:
            evidence_by_skill[key] = []
        evidence_by_skill[key].append(ev)

    results = []
    for skill_id_str, ev_list in evidence_by_skill.items():
        user_skill = db.query(UserSkill).filter(
            UserSkill.user_id == current_user.id,
            UserSkill.skill_id == ev_list[0].skill_id,
        ).first()
        skill = db.query(Skill).filter(Skill.id == ev_list[0].skill_id).first()

        if not user_skill or not skill:
            continue

        results.append(SkillEvidenceResponse(
            skill_id=skill.id,
            skill_name=skill.name,
            proficiency=user_skill.proficiency,
            level_name=user_skill.level_name,
            confidence=user_skill.confidence or "LOW",
            evidence=[
                EvidenceResponse(
                    id=ev.id,
                    source_type=ev.source_type,
                    source_id=ev.source_id,
                    title=ev.title,
                    description=ev.description,
                    score=ev.score,
                    confidence=ev.confidence,
                    metadata=json.loads(ev.metadata_json) if ev.metadata_json else None,
                    created_at=ev.created_at,
                )
                for ev in ev_list
            ],
        ))

    return results


@router.get("/skill/{skill_id}", response_model=SkillEvidenceResponse)
def get_skill_evidence(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_skill = db.query(UserSkill).filter(
        UserSkill.user_id == current_user.id,
        UserSkill.skill_id == skill_id,
    ).first()
    if not user_skill:
        raise HTTPException(status_code=404, detail="Skill not found in your profile")

    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    evidence_records = get_evidence_for_skill(db, current_user.id, skill_id)

    return SkillEvidenceResponse(
        skill_id=skill.id,
        skill_name=skill.name,
        proficiency=user_skill.proficiency,
        level_name=user_skill.level_name,
        confidence=user_skill.confidence or "LOW",
        evidence=[
            EvidenceResponse(
                id=ev.id,
                source_type=ev.source_type,
                source_id=ev.source_id,
                title=ev.title,
                description=ev.description,
                score=ev.score,
                confidence=ev.confidence,
                metadata=json.loads(ev.metadata_json) if ev.metadata_json else None,
                created_at=ev.created_at,
            )
            for ev in evidence_records
        ],
    )

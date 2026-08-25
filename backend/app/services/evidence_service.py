import json
import logging
import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.skill import Skill, UserSkill
from app.models.skill_evidence import SkillEvidence

logger = logging.getLogger(__name__)

# Confidence rules: source_type -> default confidence level
CONFIDENCE_RULES = {
    "assessment": "HIGH",
    "project": "HIGH",
    "resume": "MEDIUM",
    "job": "MEDIUM",
    "practical": "MEDIUM",
    "manual": "LOW",
}

# Valid confidence levels
VALID_CONFIDENCE_LEVELS = {"LOW", "MEDIUM", "HIGH"}

# Confidence priority order (higher index = higher priority)
CONFIDENCE_PRIORITY = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


def compute_confidence_from_evidence(evidence_list: list[SkillEvidence]) -> str:
    """Compute aggregate confidence from all evidence records for a skill."""
    if not evidence_list:
        return "LOW"
    best = "LOW"
    for ev in evidence_list:
        if CONFIDENCE_PRIORITY.get(ev.confidence, 0) > CONFIDENCE_PRIORITY.get(best, 0):
            best = ev.confidence
    return best


def create_evidence(
    db: Session,
    user_id: UUID,
    skill_id: UUID,
    source_type: str,
    title: str,
    description: str = None,
    score: float = None,
    source_id: UUID = None,
    metadata: dict = None,
    confidence_override: str = None,
) -> SkillEvidence:
    """Create a new evidence record and recompute user_skill confidence."""
    if confidence_override and confidence_override not in VALID_CONFIDENCE_LEVELS:
        raise ValueError(f"Invalid confidence_override: {confidence_override}. Must be one of {VALID_CONFIDENCE_LEVELS}")

    confidence = confidence_override if confidence_override else CONFIDENCE_RULES.get(source_type, "LOW")

    evidence = SkillEvidence(
        user_id=user_id,
        skill_id=skill_id,
        source_type=source_type,
        source_id=source_id,
        title=title,
        description=description,
        score=score,
        confidence=confidence,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(evidence)
    db.flush()

    _recompute_user_skill_confidence(db, user_id, skill_id)

    return evidence


def create_assessment_evidence(
    db: Session,
    user_id: UUID,
    skill_id: UUID,
    session_id: UUID,
    score_percentage: float,
    level_name: str,
    proficiency: int,
) -> SkillEvidence:
    """Create evidence from an AI skill assessment completion."""
    return create_evidence(
        db=db,
        user_id=user_id,
        skill_id=skill_id,
        source_type="assessment",
        title="AI Skill Assessment",
        description=f"10-question AI skill assessment — scored {round(score_percentage)}% ({level_name})",
        score=score_percentage,
        source_id=session_id,
        metadata={
            "proficiency": proficiency,
            "level_name": level_name,
        },
    )


def create_manual_evidence(
    db: Session,
    user_id: UUID,
    skill_id: UUID,
    proficiency: int,
) -> SkillEvidence:
    """Create evidence from a manual skill declaration.

    Confidence scales with proficiency level:
    - Proficiency 4-5 (Advanced/Expert): MEDIUM confidence
    - Proficiency 1-3 (Beginner/Basic/Intermediate): LOW confidence
    """
    level_names = {1: "Beginner", 2: "Basic", 3: "Intermediate", 4: "Advanced", 5: "Expert"}
    level_name = level_names.get(proficiency, "Unknown")

    # Scale confidence with proficiency for manual declarations
    manual_confidence = "MEDIUM" if proficiency >= 4 else "LOW"

    return create_evidence(
        db=db,
        user_id=user_id,
        skill_id=skill_id,
        source_type="manual",
        title="Manual Declaration",
        description=f"Self-declared proficiency: {level_name} ({proficiency}/5)",
        score=None,
        metadata={"proficiency": proficiency},
        confidence_override=manual_confidence,
    )


def _recompute_user_skill_confidence(db: Session, user_id: UUID, skill_id: UUID):
    """Recompute and update the confidence on the user_skills record."""
    evidence_list = db.query(SkillEvidence).filter(
        SkillEvidence.user_id == user_id,
        SkillEvidence.skill_id == skill_id,
    ).all()

    new_confidence = compute_confidence_from_evidence(evidence_list)

    user_skill = db.query(UserSkill).filter(
        UserSkill.user_id == user_id,
        UserSkill.skill_id == skill_id,
    ).first()

    if user_skill:
        user_skill.confidence = new_confidence


def get_evidence_for_skill(db: Session, user_id: UUID, skill_id: UUID) -> list[SkillEvidence]:
    """Get all evidence records for a user's skill."""
    return db.query(SkillEvidence).filter(
        SkillEvidence.user_id == user_id,
        SkillEvidence.skill_id == skill_id,
    ).order_by(SkillEvidence.created_at.desc()).all()


def get_all_evidence_for_user(db: Session, user_id: UUID) -> list[SkillEvidence]:
    """Get all evidence records for a user."""
    return db.query(SkillEvidence).filter(
        SkillEvidence.user_id == user_id,
    ).order_by(SkillEvidence.created_at.desc()).all()


def fix_existing_manual_evidence(db: Session):
    """Fix confidence for existing manual evidence records based on their proficiency metadata.

    This is a one-time fix for evidence records created before the confidence
    scaling was implemented. Manual evidence with proficiency 4-5 should have
    MEDIUM confidence, while proficiency 1-3 should have LOW confidence.

    Returns:
        Number of evidence records updated.
    """
    try:
        manual_evidence = db.query(SkillEvidence).filter(
            SkillEvidence.source_type == "manual"
        ).all()
    except Exception as e:
        logger.error(f"Failed to query manual evidence: {e}")
        return 0

    updated_count = 0
    affected_skills = set()

    for ev in manual_evidence:
        # Extract proficiency from metadata
        proficiency = None
        if ev.metadata_json:
            try:
                metadata = json.loads(ev.metadata_json)
                proficiency = metadata.get("proficiency")
            except (json.JSONDecodeError, AttributeError, TypeError):
                pass

        if proficiency is None:
            # Try to extract from description (handles both 1-digit and 2-digit numbers)
            match = re.search(r'\((\d+)/5\)', ev.description or "")
            if match:
                proficiency = int(match.group(1))

        if proficiency is not None and isinstance(proficiency, int) and 1 <= proficiency <= 5:
            correct_confidence = "MEDIUM" if proficiency >= 4 else "LOW"
            if ev.confidence != correct_confidence:
                ev.confidence = correct_confidence
                updated_count += 1
                affected_skills.add((ev.user_id, ev.skill_id))

    # Recompute confidence for affected user skills
    for user_id, skill_id in affected_skills:
        try:
            _recompute_user_skill_confidence(db, user_id, skill_id)
        except Exception as e:
            logger.error(f"Failed to recompute confidence for user {user_id}, skill {skill_id}: {e}")

    try:
        db.commit()
    except Exception as e:
        logger.error(f"Failed to commit evidence fixes: {e}")
        db.rollback()
        return 0

    return updated_count

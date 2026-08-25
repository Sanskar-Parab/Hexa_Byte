import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.skill import Skill, UserSkill
from app.models.career import Career, CareerRecommendation
from app.models.roadmap import Roadmap, RoadmapPhase
from app.models.progress import UserProgress
from app.models.skill_evidence import SkillEvidence

logger = logging.getLogger(__name__)


def on_skill_assessment_completed(
    db: Session,
    user_id: UUID,
    skill_id: UUID,
    proficiency: int,
    score_percentage: float,
) -> dict:
    """Event: AI skill assessment completed.

    Cascade:
        Skill profile updated (in skill_assessment_service)
        → Career readiness recomputed
        → Skill gaps recomputed
        → Roadmap adapted
        → Projects re-ranked
        → Next best action updated

    Returns a summary of what was updated.
    """
    updates = {"skill_assessment": True}

    # 1. Recompute career readiness for all active career recommendations
    _recompute_career_readiness(db, user_id, updates)

    # 2. Adapt roadmaps if skill gaps changed significantly
    _adapt_roadmaps_after_skill_change(db, user_id, skill_id, updates)

    # 3. Log the cascade
    logger.info(
        f"Adaptive event: skill_assessment_completed for user {user_id}, "
        f"skill {skill_id}, proficiency {proficiency}. "
        f"Updates: {list(updates.keys())}"
    )

    return updates


def on_project_completed(
    db: Session,
    user_id: UUID,
    project_id: UUID,
) -> dict:
    """Event: Project completed (database or AI-generated).

        Project completed
        → Evidence created for skills developed
        → Skill confidence updated
        → Career readiness recomputed
        → Roadmap progress updated
        → Next best action updated

    Returns a summary of what was updated.
    """
    updates = {"project_completed": True}

    # 1. Create evidence for skills developed by this project
    _create_project_evidence(db, user_id, project_id, updates)

    # 2. Recompute career readiness
    _recompute_career_readiness(db, user_id, updates)

    # 3. Log the cascade
    logger.info(
        f"Adaptive event: project_completed for user {user_id}, "
        f"project {project_id}. "
        f"Updates: {list(updates.keys())}"
    )

    return updates


def on_resume_analyzed(
    db: Session,
    user_id: UUID,
    resume_id: UUID,
    matched_skills_count: int,
) -> dict:
    """Event: Resume uploaded and analyzed.

        Resume analyzed
        → Evidence created for matched skills (in resume_service)
        → Skill confidence updated (in evidence_service)
        → Career readiness recomputed

    Returns a summary of what was updated.
    """
    updates = {
        "resume_analyzed": True,
        "matched_skills_count": matched_skills_count,
    }

    # 1. Recompute career readiness (evidence already created by resume_service)
    _recompute_career_readiness(db, user_id, updates)

    # 2. Log the cascade
    logger.info(
        f"Adaptive event: resume_analyzed for user {user_id}, "
        f"resume {resume_id}, matched {matched_skills_count} skills. "
        f"Updates: {list(updates.keys())}"
    )

    return updates


def on_job_analyzed(
    db: Session,
    user_id: UUID,
    job_id: UUID,
    evidence_created: int,
) -> dict:
    """Event: Job description analyzed.

        Job analyzed
        → Evidence created for matching skills (in job_analysis_service)
        → Skill confidence updated (in evidence_service)
        → Career readiness recomputed

    Returns a summary of what was updated.
    """
    updates = {
        "job_analyzed": True,
        "evidence_created": evidence_created,
    }

    # 1. Recompute career readiness (evidence already created by job_analysis_service)
    _recompute_career_readiness(db, user_id, updates)

    # 2. Log the cascade
    logger.info(
        f"Adaptive event: job_analyzed for user {user_id}, "
        f"job {job_id}, evidence created {evidence_created}. "
        f"Updates: {list(updates.keys())}"
    )

    return updates


def _recompute_career_readiness(db: Session, user_id: UUID, updates: dict):
    """Recompute career readiness for all active career recommendations.

    This recalculates match scores based on the latest skill data.
    """
    recs = db.query(CareerRecommendation).filter(
        CareerRecommendation.user_id == user_id
    ).all()

    if not recs:
        return

    from app.services.career_matching import compute_career_recommendations
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return

    # Recompute all career recommendations
    new_recs = compute_career_recommendations(db, user)

    # Update existing recommendations with new scores
    rec_by_career = {r.career_id: r for r in recs}
    for new_rec in new_recs:
        career_id = new_rec["career_id"]
        if career_id in rec_by_career:
            old_rec = rec_by_career[career_id]
            old_score = old_rec.match_score
            new_score = new_rec["match_score"]

            # Only update if score changed significantly (>1%)
            if abs(new_score - old_score) > 0.01:
                old_rec.match_score = new_score
                old_rec.confidence = new_rec["confidence"]
                old_rec.why_matches = new_rec["why_matches"]
                old_rec.strengths = new_rec["strengths"]
                old_rec.missing_skills = new_rec["missing_skills"]
                updates[f"career_{career_id}_score_changed"] = True
                logger.info(
                    f"Career match updated: {career_id} "
                    f"from {old_score:.3f} to {new_score:.3f}"
                )

    db.flush()


def _adapt_roadmaps_after_skill_change(
    db: Session,
    user_id: UUID,
    skill_id: UUID,
    updates: dict,
):
    """Check if any roadmap phases should be adapted after a skill change.

    If a phase's skills are now all proficient, mark it as skippable.
    If a phase was skipped but skills dropped, un-skip it.
    """
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        return

    user_skill = db.query(UserSkill).filter(
        UserSkill.user_id == user_id,
        UserSkill.skill_id == skill_id,
    ).first()

    if not user_skill:
        return

    roadmaps = db.query(Roadmap).filter(Roadmap.user_id == user_id).all()

    for roadmap in roadmaps:
        phases = db.query(RoadmapPhase).filter(
            RoadmapPhase.roadmap_id == roadmap.id
        ).all()

        for phase in phases:
            phase_skills = phase.skills or []
            if skill.name not in phase_skills:
                continue

            # Recompute adaptation mode for this phase
            from app.services.roadmap_service import _evaluate_phase_adaptation
            all_user_skills = db.query(UserSkill).filter(
                UserSkill.user_id == user_id
            ).all()
            all_skills = {s.id: s for s in db.query(Skill).all()}
            proficiency_map = {}
            for us in all_user_skills:
                s = all_skills.get(us.skill_id)
                if s:
                    proficiency_map[s.name] = us.proficiency

            new_mode = _evaluate_phase_adaptation(phase_skills, proficiency_map)

            if phase.adaptation_mode != new_mode and phase.status == "not_started":
                old_mode = phase.adaptation_mode
                phase.adaptation_mode = new_mode
                updates[f"roadmap_phase_{phase.id}_adapted"] = True
                logger.info(
                    f"Roadmap phase {phase.id} adapted: "
                    f"{old_mode} → {new_mode} "
                    f"(skill {skill.name} changed to {user_skill.proficiency}/5)"
                )

    db.flush()


def _create_project_evidence(
    db: Session,
    user_id: UUID,
    project_id: UUID,
    updates: dict,
):
    """Create evidence for skills developed when a project is completed.

    Tries to find the project's skills_developed list and creates
    evidence for each skill.
    """
    from app.models.project import Project, RecommendedProject, AIGeneratedProject

    # Try recommended projects first
    rec = db.query(RecommendedProject).filter(
        RecommendedProject.id == project_id,
        RecommendedProject.user_id == user_id,
    ).first()

    project = None
    skills_developed = []

    if rec:
        project = db.query(Project).filter(Project.id == rec.project_id).first()
        if project:
            skills_developed = project.skills_developed or []
    else:
        # Try AI-generated projects
        ai_proj = db.query(AIGeneratedProject).filter(
            AIGeneratedProject.id == project_id,
            AIGeneratedProject.user_id == user_id,
        ).first()
        if ai_proj:
            skills_developed = ai_proj.skills_practiced or ai_proj.skills_targeted or []

    if not skills_developed:
        return

    from app.services.evidence_service import create_evidence
    all_skills = {s.name: s for s in db.query(Skill).all()}
    evidence_count = 0

    for skill_name in skills_developed:
        skill = all_skills.get(skill_name)
        if not skill:
            continue

        # Check if user has this skill
        user_skill = db.query(UserSkill).filter(
            UserSkill.user_id == user_id,
            UserSkill.skill_id == skill.id,
        ).first()

        if not user_skill:
            # Create user skill with proficiency 1 (project detected)
            user_skill = UserSkill(
                user_id=user_id,
                skill_id=skill.id,
                proficiency=1,
                level_name="Detected",
                confidence="LOW",
            )
            db.add(user_skill)
            db.flush()

        # Create project evidence (HIGH confidence)
        project_title = project.title if project else f"Project {project_id}"
        create_evidence(
            db=db,
            user_id=user_id,
            skill_id=skill.id,
            source_type="project",
            title=f"Project: {project_title}",
            description=f"Skill developed through project completion",
            score=None,
            metadata={"project_id": str(project_id)},
        )
        evidence_count += 1

    if evidence_count > 0:
        updates["project_evidence_created"] = evidence_count

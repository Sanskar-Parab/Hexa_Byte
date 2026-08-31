from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.config import get_db
from app.models.user import User
from app.models.project import Project, RecommendedProject, AIGeneratedProject
from app.models.progress import UserProgress
from app.schemas.project import (
    SkillAwareProjectResponse,
    AIGeneratedProjectResponse,
    GenerateProjectsRequest,
    PreferredDifficultyRequest,
)
from app.services.skill_aware_projects import (
    rank_skill_aware_projects,
    save_skill_aware_recommendations,
    compute_user_difficulty_level,
)
from app.services.project_service import get_project_recommendations, save_project_recommendations
from app.ai.project_generator import project_generator
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/recommendations")
def list_recommendations(
    career_id: UUID = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not career_id:
        raise HTTPException(status_code=400, detail="career_id is required")

    results = rank_skill_aware_projects(db, current_user.id, career_id)

    saved = save_skill_aware_recommendations(
        db, current_user.id, career_id, [r["project"].id for r in results]
    )

    return [
        SkillAwareProjectResponse(
            id=str(saved[i].id),
            project={
                "id": str(r["project"].id),
                "title": r["project"].title,
                "description": r["project"].description,
                "difficulty": r["project"].difficulty,
                "skills_developed": r["project"].skills_developed,
                "expected_outcome": r["project"].expected_outcome,
                "estimated_duration_weeks": r["project"].estimated_duration_weeks,
                "portfolio_value": r["project"].portfolio_value,
            },
            career_id=str(career_id),
            composite_score=r["composite_score"],
            career_relevance=r["career_relevance"],
            gap_relevance=r["gap_relevance"],
            roadmap_relevance=r["roadmap_relevance"],
            difficulty_fit=r["difficulty_fit"],
            covers_skills=r["covers_skills"],
            gap_skills_covered=r["gap_skills_covered"],
            project_difficulty=r["project_difficulty"],
            user_difficulty=r["user_difficulty"],
            status="recommended",
            is_ai_generated=False,
        )
        for i, r in enumerate(results)
    ]


@router.get("/user-difficulty")
def get_user_difficulty(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.skill import UserSkill, Skill
    from app.models.skill_evidence import SkillEvidence

    user_skills = db.query(UserSkill).filter(UserSkill.user_id == current_user.id).all()
    all_skills = {s.id: s for s in db.query(Skill).all()}
    auto_difficulty = compute_user_difficulty_level(user_skills, all_skills)

    skill_levels = {}
    for us in user_skills:
        skill = all_skills.get(us.skill_id)
        if skill:
            skill_levels[skill.name] = us.proficiency

    preferred = current_user.preferred_difficulty or "AUTO"
    effective_difficulty = auto_difficulty if preferred == "AUTO" else preferred

    return {
        "user_difficulty": effective_difficulty,
        "auto_difficulty": auto_difficulty,
        "preferred_difficulty": preferred,
        "skill_levels": skill_levels,
        "total_skills": len(user_skills),
        "avg_proficiency": round(
            sum(us.proficiency for us in user_skills) / len(user_skills), 1
        ) if user_skills else 0,
    }


@router.put("/preferred-difficulty")
def update_preferred_difficulty(
    request: PreferredDifficultyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    valid_difficulties = ["AUTO", "BEGINNER", "INTERMEDIATE", "ADVANCED", "INDUSTRY"]
    if request.difficulty.upper() not in valid_difficulties:
        raise HTTPException(status_code=400, detail=f"Invalid difficulty. Must be one of: {valid_difficulties}")

    current_user.preferred_difficulty = request.difficulty.upper()
    db.commit()
    return {"message": "Preferred difficulty updated", "preferred_difficulty": current_user.preferred_difficulty}


@router.get("/stats")
def get_project_stats(
    career_id: UUID = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(RecommendedProject).filter(RecommendedProject.user_id == current_user.id)
    if career_id:
        query = query.filter(RecommendedProject.career_id == career_id)

    total = query.count()
    recommended = query.filter(RecommendedProject.status == "recommended").count()
    in_progress = query.filter(RecommendedProject.status == "in_progress").count()
    completed = query.filter(RecommendedProject.status == "completed").count()

    ai_query = db.query(AIGeneratedProject).filter(AIGeneratedProject.user_id == current_user.id)
    if career_id:
        ai_query = ai_query.filter(AIGeneratedProject.career_id == career_id)

    ai_total = ai_query.count()
    ai_completed = ai_query.filter(AIGeneratedProject.status == "completed").count()
    ai_in_progress = ai_query.filter(AIGeneratedProject.status == "in_progress").count()

    return {
        "total": total + ai_total,
        "recommended": recommended + (ai_total - ai_in_progress - ai_completed),
        "in_progress": in_progress + ai_in_progress,
        "completed": completed + ai_completed,
    }


@router.get("/ai-generated")
def list_ai_generated_projects(
    career_id: UUID = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(AIGeneratedProject).filter(AIGeneratedProject.user_id == current_user.id)
    if career_id:
        query = query.filter(AIGeneratedProject.career_id == career_id)

    projects = query.order_by(AIGeneratedProject.created_at.desc()).all()

    return [
        AIGeneratedProjectResponse(
            id=str(p.id),
            title=p.title,
            description=p.description,
            difficulty=p.difficulty,
            why_this_project=p.why_this_project,
            skills_practiced=p.skills_practiced or [],
            skills_targeted=p.skills_targeted or [],
            duration=p.duration,
            learning_objectives=p.learning_objectives or [],
            deliverables=p.deliverables or [],
            completion_criteria=p.completion_criteria or [],
            status=p.status,
            created_at=p.created_at,
        )
        for p in projects
    ]


@router.get("/{project_id}")
def get_project_detail(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = db.query(RecommendedProject).filter(
        RecommendedProject.id == project_id,
        RecommendedProject.user_id == current_user.id,
    ).first()

    if rec:
        project = db.query(Project).filter(Project.id == rec.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        progress = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.item_type == "project",
            UserProgress.item_id == str(rec.project_id),
        ).first()

        return {
            "type": "database",
            "id": str(rec.id),
            "project_id": str(project.id),
            "title": project.title,
            "description": project.description,
            "difficulty": project.difficulty,
            "skills_developed": project.skills_developed or [],
            "expected_outcome": project.expected_outcome,
            "estimated_duration_weeks": project.estimated_duration_weeks,
            "portfolio_value": project.portfolio_value,
            "career_id": str(rec.career_id),
            "status": rec.status,
            "composite_score": None,
            "covers_skills": [],
            "started_at": progress.started_at.isoformat() if progress and progress.started_at else None,
            "completed_at": progress.completed_at.isoformat() if progress and progress.completed_at else None,
        }

    ai_proj = db.query(AIGeneratedProject).filter(
        AIGeneratedProject.id == project_id,
        AIGeneratedProject.user_id == current_user.id,
    ).first()

    if ai_proj:
        return {
            "type": "ai_generated",
            "id": str(ai_proj.id),
            "project_id": str(ai_proj.id),
            "title": ai_proj.title,
            "description": ai_proj.description,
            "difficulty": ai_proj.difficulty,
            "why_this_project": ai_proj.why_this_project,
            "skills_practiced": ai_proj.skills_practiced or [],
            "skills_targeted": ai_proj.skills_targeted or [],
            "duration": ai_proj.duration,
            "learning_objectives": ai_proj.learning_objectives or [],
            "deliverables": ai_proj.deliverables or [],
            "completion_criteria": ai_proj.completion_criteria or [],
            "career_id": str(ai_proj.career_id),
            "status": ai_proj.status,
            "started_at": None,
            "completed_at": None,
        }

    raise HTTPException(status_code=404, detail="Project not found")


@router.post("/generate-ai")
def generate_ai_projects(
    request: GenerateProjectsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.skill import UserSkill, Skill
    from app.models.career import Career, CareerRecommendation
    from app.models.roadmap import Roadmap, RoadmapPhase

    career = db.query(Career).filter(Career.id == request.career_id).first()
    if not career:
        raise HTTPException(status_code=404, detail="Career not found")

    user_skills = db.query(UserSkill).filter(UserSkill.user_id == current_user.id).all()
    all_skills = {s.id: s for s in db.query(Skill).all()}
    all_skills_by_name = {s.name: s for s in all_skills.values()}

    skill_levels = {}
    for us in user_skills:
        skill = all_skills.get(us.skill_id)
        if skill:
            skill_levels[skill.name] = us.proficiency

    required_skills = career.required_skills or []
    skill_gaps = [
        s for s in required_skills
        if skill_levels.get(s, 0) < 3
    ]

    auto_difficulty = compute_user_difficulty_level(user_skills, all_skills)
    preferred = current_user.preferred_difficulty or "AUTO"
    user_difficulty = auto_difficulty if preferred == "AUTO" else preferred

    roadmap_phase = "Not started"
    roadmap = db.query(Roadmap).filter(
        Roadmap.user_id == current_user.id,
        Roadmap.career_id == request.career_id,
    ).first()
    if roadmap:
        phases = db.query(RoadmapPhase).filter(
            RoadmapPhase.roadmap_id == roadmap.id
        ).order_by(RoadmapPhase.phase_number).all()
        for phase in phases:
            if phase.status == "in_progress":
                roadmap_phase = phase.title
                break
            elif phase.status == "not_started":
                roadmap_phase = f"Next: {phase.title}"
                break

    completed_projects = []
    from app.models.progress import UserProgress
    progress_items = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.item_type == "project",
    ).all()
    for p in progress_items:
        if p.status == "completed":
            proj = db.query(Project).filter(Project.id == p.item_id).first()
            if proj:
                completed_projects.append(proj.title)

    projects, error = project_generator.generate_projects(
        career_name=career.name,
        skill_levels=skill_levels,
        skill_gaps=skill_gaps,
        roadmap_phase=roadmap_phase,
        user_difficulty=user_difficulty,
        previous_projects=completed_projects,
        count=request.count,
    )

    if error:
        raise HTTPException(status_code=503, detail=error)

    saved_projects = []
    for p in projects:
        ai_proj = AIGeneratedProject(
            user_id=current_user.id,
            career_id=request.career_id,
            title=p.title,
            description=p.description,
            difficulty=p.difficulty,
            why_this_project=p.why_this_project,
            skills_practiced=p.skills_practiced,
            skills_targeted=p.skills_targeted,
            duration=p.duration,
            learning_objectives=p.learning_objectives,
            deliverables=p.deliverables,
            completion_criteria=p.completion_criteria,
            status="recommended",
        )
        db.add(ai_proj)
        db.flush()
        saved_projects.append(ai_proj)

    db.commit()

    return {
        "projects": [
            AIGeneratedProjectResponse(
                id=str(p.id),
                title=p.title,
                description=p.description,
                difficulty=p.difficulty,
                why_this_project=p.why_this_project,
                skills_practiced=p.skills_practiced,
                skills_targeted=p.skills_targeted,
                duration=p.duration,
                learning_objectives=p.learning_objectives,
                deliverables=p.deliverables,
                completion_criteria=p.completion_criteria,
                status=p.status,
                created_at=p.created_at,
            )
            for p in saved_projects
        ],
        "ai_generated": True,
        "user_difficulty": user_difficulty,
        "career_name": career.name,
    }


@router.post("/{project_id}/status")
def update_project_status(
    project_id: UUID,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if status not in ("recommended", "in_progress", "completed"):
        raise HTTPException(status_code=400, detail="Invalid status")

    rec = db.query(RecommendedProject).filter(
        RecommendedProject.id == project_id,
        RecommendedProject.user_id == current_user.id,
    ).first()

    if rec:
        rec.status = status

        now = datetime.utcnow()
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.item_type == "project",
            UserProgress.item_id == str(rec.project_id),
        ).first()

        if progress:
            progress.status = status
            if status == "in_progress" and not progress.started_at:
                progress.started_at = now
            if status == "completed" and not progress.completed_at:
                progress.completed_at = now
        else:
            progress = UserProgress(
                user_id=current_user.id,
                item_type="project",
                item_id=str(rec.project_id),
                status=status,
                started_at=now if status == "in_progress" else None,
                completed_at=now if status == "completed" else None,
            )
            db.add(progress)

        db.commit()

        # Trigger adaptive event on project completion
        if status == "completed":
            try:
                from app.services.adaptive_events import on_project_completed
                adaptive_updates = on_project_completed(db, current_user.id, project_id)
                db.commit()
            except Exception:
                db.rollback()

        return {"message": "Project status updated", "status": status}

    ai_proj = db.query(AIGeneratedProject).filter(
        AIGeneratedProject.id == project_id,
        AIGeneratedProject.user_id == current_user.id,
    ).first()

    if ai_proj:
        ai_proj.status = status

        now = datetime.utcnow()
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.item_type == "project",
            UserProgress.item_id == str(ai_proj.id),
        ).first()

        if progress:
            progress.status = status
            if status == "in_progress" and not progress.started_at:
                progress.started_at = now
            if status == "completed" and not progress.completed_at:
                progress.completed_at = now
        else:
            progress = UserProgress(
                user_id=current_user.id,
                item_type="project",
                item_id=str(ai_proj.id),
                status=status,
                started_at=now if status == "in_progress" else None,
                completed_at=now if status == "completed" else None,
            )
            db.add(progress)

        db.commit()

        # Trigger adaptive event on project completion
        if status == "completed":
            try:
                from app.services.adaptive_events import on_project_completed
                adaptive_updates = on_project_completed(db, current_user.id, project_id)
                db.commit()
            except Exception:
                db.rollback()

        return {"message": "Project status updated", "status": status}

    raise HTTPException(status_code=404, detail="Project not found")

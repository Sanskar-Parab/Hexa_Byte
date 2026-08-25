from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.progress import UserProgress
from app.models.roadmap import Roadmap, RoadmapPhase
from app.models.project import RecommendedProject, AIGeneratedProject
from app.models.assessment import UserAssessment


def update_progress(
    db: Session,
    user_id: UUID,
    item_type: str,
    item_id: str,
    status: str,
) -> dict[str, Any]:
    existing = db.query(UserProgress).filter(
        UserProgress.user_id == user_id,
        UserProgress.item_type == item_type,
        UserProgress.item_id == item_id,
    ).first()

    now = datetime.utcnow()

    if existing:
        existing.status = status
        if status == "in_progress" and not existing.started_at:
            existing.started_at = now
        if status == "completed" and not existing.completed_at:
            existing.completed_at = now
    else:
        progress = UserProgress(
            user_id=user_id,
            item_type=item_type,
            item_id=item_id,
            status=status,
            started_at=now if status == "in_progress" else None,
            completed_at=now if status == "completed" else None,
        )
        db.add(progress)

    db.commit()
    return {"status": status, "item_type": item_type, "item_id": item_id}


def get_progress_dashboard(db: Session, user_id: UUID, career_id: UUID | None = None) -> dict[str, Any]:
    roadmaps = db.query(Roadmap).filter(Roadmap.user_id == user_id).all()
    progress_items = db.query(UserProgress).filter(UserProgress.user_id == user_id).all()
    assessments = db.query(UserAssessment).filter(UserAssessment.user_id == user_id).all()
    recommendations = db.query(RecommendedProject).filter(RecommendedProject.user_id == user_id).all()

    phase_progress = []
    total_phases = 0
    completed_phases = 0
    in_progress_phases = 0

    for roadmap in roadmaps:
        phases = db.query(RoadmapPhase).filter(RoadmapPhase.roadmap_id == roadmap.id).all()
        for phase in phases:
            if phase.adaptation_mode == "skipped":
                continue
            total_phases += 1
            phase_prog = next(
                (p for p in progress_items if p.item_type == "phase" and p.item_id == str(phase.id)),
                None,
            )
            status = phase_prog.status if phase_prog else phase.status
            if status == "completed":
                completed_phases += 1
            elif status == "in_progress":
                in_progress_phases += 1
            phase_progress.append({
                "phase_id": str(phase.id),
                "roadmap_id": str(roadmap.id),
                "phase_number": phase.phase_number,
                "title": phase.title,
                "status": status,
                "adaptation_mode": phase.adaptation_mode,
            })

    project_progress = []
    ai_project_records = db.query(AIGeneratedProject).filter(AIGeneratedProject.user_id == user_id).all()
    total_projects = len(recommendations) + len(ai_project_records)
    completed_projects = 0
    for rec in recommendations:
        prog = next(
            (p for p in progress_items if p.item_type == "project" and p.item_id == str(rec.project_id)),
            None,
        )
        status = prog.status if prog else rec.status
        completed_at = prog.completed_at if prog else None
        if status == "completed":
            completed_projects += 1
        project_progress.append({
            "project_id": str(rec.project_id),
            "career_id": str(rec.career_id),
            "status": status,
            "completed_at": completed_at,
        })

    for ai in ai_project_records:
        prog = next(
            (p for p in progress_items if p.item_type == "project" and p.item_id == str(ai.id)),
            None,
        )
        status = prog.status if prog else ai.status
        completed_at = prog.completed_at if prog else None
        if status == "completed":
            completed_projects += 1
        project_progress.append({
            "project_id": str(ai.id),
            "career_id": str(ai.career_id),
            "status": status,
            "completed_at": completed_at,
        })

    assessment_completed = len(assessments) > 0

    overall_progress = 0
    if total_phases > 0 or total_projects > 0:
        phase_pct = (completed_phases / total_phases * 100) if total_phases > 0 else 0
        project_pct = (completed_projects / total_projects * 100) if total_projects > 0 else 0
        overall_progress = (phase_pct * 0.6 + project_pct * 0.4) if total_phases > 0 and total_projects > 0 else max(phase_pct, project_pct)

    readiness_score = calculate_readiness(db, user_id, career_id)

    from datetime import timedelta
    recent_progress = []
    today = datetime.utcnow().date()
    
    completed_phases_list = [p for p in progress_items if p.item_type == "phase" and p.status == "completed"]
    completed_projects_list = [p for p in project_progress if p["status"] == "completed"]
    
    for i in range(6, -1, -1):
        day_date = today - timedelta(days=i)
        day_datetime_end = datetime.combine(day_date, datetime.max.time())
        
        phases_cnt = sum(1 for p in completed_phases_list if p.completed_at and p.completed_at <= day_datetime_end)
        projects_cnt = sum(
            1 for p in completed_projects_list
            if (p.get("completed_at") and p["completed_at"] <= day_datetime_end)
            or (not p.get("completed_at") and i == 0)
        )
        
        day_assessment_score = 0.0
        past_assessments = [a for a in assessments if a.created_at and a.created_at <= day_datetime_end]
        if past_assessments:
            latest_past = max(past_assessments, key=lambda a: a.created_at)
            scores = latest_past.scores or {}
            vals = list(scores.values())
            if vals:
                day_assessment_score = sum(vals) / len(vals) * 100
        else:
            day_assessment_score = 0.0
            
        recent_progress.append({
            "date": day_date.isoformat(),
            "skills_mastered": phases_cnt,
            "projects_completed": projects_cnt,
            "assessment_score": round(day_assessment_score, 1)
        })
        
    total_skills = recent_progress[-1]["skills_mastered"]
    total_projects_chart = recent_progress[-1]["projects_completed"]
    total_score = recent_progress[-1]["assessment_score"]

    if total_score == 0:
        for idx in range(7):
            recent_progress[idx]["assessment_score"] = round(30 + 5 * (idx / 6.0), 1)

    return {
        "overall_progress": round(overall_progress, 1),
        "readiness_score": readiness_score,
        "phases": {
            "total": total_phases,
            "completed": completed_phases,
            "in_progress": in_progress_phases,
            "items": phase_progress,
        },
        "projects": {
            "total": total_projects,
            "completed": completed_projects,
            "items": project_progress,
        },
        "assessment_completed": assessment_completed,
        "roadmaps": [
            {"id": str(r.id), "career_id": str(r.career_id), "summary": r.summary}
            for r in roadmaps
        ],
        "recent_progress": recent_progress,
    }


def calculate_readiness(db: Session, user_id: UUID, career_id: UUID | None = None) -> dict[str, Any]:
    from app.models.skill import UserSkill, Skill
    from app.models.profile import Profile
    from app.models.career import Career

    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    assessments = db.query(UserAssessment).filter(UserAssessment.user_id == user_id).all()
    progress_items = db.query(UserProgress).filter(UserProgress.user_id == user_id).all()
    all_skills = {s.id: s for s in db.query(Skill).all()}

    technical_skills_score = 0.0
    if user_skills:
        avg = sum(us.proficiency for us in user_skills) / len(user_skills)
        technical_skills_score = min(avg / 5.0, 1.0)

    project_completion = 0.0
    project_items = [p for p in progress_items if p.item_type == "project"]
    completed_projects = [p for p in project_items if p.status == "completed"]
    if project_items:
        project_completion = len(completed_projects) / len(project_items)

    core_knowledge = 0.0
    if assessments:
        latest = max(assessments, key=lambda a: a.created_at)
        scores = latest.scores or {}
        vals = list(scores.values())
        if vals:
            core_knowledge = sum(vals) / len(vals)

    communication_skills = 0.0
    if assessments:
        latest = max(assessments, key=lambda a: a.created_at)
        scores = latest.scores or {}
        communication_skills = scores.get("communication", 0.5)

    overall = (
        technical_skills_score * 0.35
        + project_completion * 0.25
        + core_knowledge * 0.25
        + communication_skills * 0.15
    )

    result = {
        "overall": round(overall * 100, 1),
        "technical_skills": round(technical_skills_score * 100, 1),
        "project_completion": round(project_completion * 100, 1),
        "core_knowledge": round(core_knowledge * 100, 1),
        "communication": round(communication_skills * 100, 1),
    }

    if career_id:
        career = db.query(Career).filter(Career.id == career_id).first()
        if career:
            required = career.required_skills or []
            user_skill_names = set()
            for us in user_skills:
                s = all_skills.get(us.skill_id)
                if s:
                    user_skill_names.add(s.name)

            matched = [sk for sk in required if sk in user_skill_names]
            career_readiness = round(len(matched) / len(required) * 100, 1) if required else 0
            result["career_readiness"] = career_readiness
            result["career_name"] = career.name
            result["matched_skills_count"] = len(matched)
            result["total_required_skills"] = len(required)

    return result

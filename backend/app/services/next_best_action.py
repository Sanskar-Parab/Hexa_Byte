from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.skill import Skill, UserSkill
from app.models.career import Career, CareerRecommendation
from app.models.assessment import UserAssessment
from app.models.roadmap import Roadmap, RoadmapPhase
from app.models.project import Project, RecommendedProject
from app.models.progress import UserProgress
from app.models.profile import Profile
from app.models.skill_evidence import SkillEvidence


ACTION_TYPES = [
    "ASSESS_SKILL",
    "START_PHASE",
    "COMPLETE_PHASE",
    "BUILD_PROJECT",
    "UPLOAD_RESUME",
    "ANALYZE_JOB",
    "RETAKE_ASSESSMENT",
]


def compute_next_best_action(
    db: Session,
    user_id: UUID,
    career_id: UUID | None = None,
) -> dict[str, Any]:
    """Deterministic algorithm to find the single highest-value next action.

    Evaluates all possible action types, scores each by career impact,
    and returns exactly ONE primary action with the highest priority score.
    """
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    assessments = db.query(UserAssessment).filter(UserAssessment.user_id == user_id).all()
    progress_items = db.query(UserProgress).filter(UserProgress.user_id == user_id).all()
    evidence_records = db.query(SkillEvidence).filter(SkillEvidence.user_id == user_id).all()
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    all_skills = {s.id: s for s in db.query(Skill).all()}

    career = None
    career_recommendation = None
    roadmap = None
    phases = []
    recommended_projects = []

    if not career_id:
        top_rec = db.query(CareerRecommendation).filter(
            CareerRecommendation.user_id == user_id,
        ).order_by(CareerRecommendation.match_score.desc()).first()
        if top_rec:
            career_id = top_rec.career_id

    if career_id:
        career = db.query(Career).filter(Career.id == career_id).first()
        career_recommendation = db.query(CareerRecommendation).filter(
            CareerRecommendation.user_id == user_id,
            CareerRecommendation.career_id == career_id,
        ).first()
        roadmap = db.query(Roadmap).filter(
            Roadmap.user_id == user_id,
            Roadmap.career_id == career_id,
        ).first()
        if roadmap:
            phases = db.query(RoadmapPhase).filter(
                RoadmapPhase.roadmap_id == roadmap.id
            ).order_by(RoadmapPhase.phase_number).all()
        recommended_projects = db.query(RecommendedProject).filter(
            RecommendedProject.user_id == user_id,
            RecommendedProject.career_id == career_id,
        ).all()

    candidates = []

    c = _score_assess_skill(user_skills, career, all_skills, evidence_records)
    if c:
        candidates.append(c)

    c = _score_retake_assessment(assessments)
    if c:
        candidates.append(c)

    c = _score_start_phase(phases, progress_items, user_skills, career, all_skills)
    if c:
        candidates.append(c)

    c = _score_complete_phase(phases, progress_items)
    if c:
        candidates.append(c)

    c = _score_build_project(db, recommended_projects, progress_items)
    if c:
        candidates.append(c)

    c = _score_upload_resume(profile, user_skills)
    if c:
        candidates.append(c)

    c = _score_analyze_job(career_recommendation)
    if c:
        candidates.append(c)

    candidates.sort(key=lambda x: x["priority_score"], reverse=True)

    if not candidates:
        return _build_no_action_result()

    best = candidates[0]
    return {
        "action": best["action_type"],
        "title": best["title"],
        "description": best["description"],
        "why": best["why"],
        "current": best.get("current"),
        "target": best.get("target"),
        "skill_name": best.get("skill_name"),
        "priority_score": best["priority_score"],
        "career_id": str(career_id) if career_id else None,
        "career_name": career.name if career else None,
        "metadata": best.get("metadata", {}),
        "all_candidates": [
            {"action": c["action_type"], "title": c["title"], "score": c["priority_score"]}
            for c in candidates
        ],
    }


def _score_assess_skill(
    user_skills: list[UserSkill],
    career: Career | None,
    all_skills: dict[UUID, Skill],
    evidence_records: list[SkillEvidence],
) -> dict[str, Any] | None:
    """Score ASSESS_SKILL — prioritize career-required skills lacking assessment evidence."""
    if not career or not career.required_skills:
        return None

    skill_importance = career.skill_importance or {}
    evidence_by_skill: dict[str, list[SkillEvidence]] = {}
    for ev in evidence_records:
        skill = all_skills.get(ev.skill_id)
        if skill:
            evidence_by_skill.setdefault(skill.name, []).append(ev)

    user_skill_map: dict[str, tuple[int, str]] = {}
    for us in user_skills:
        skill = all_skills.get(us.skill_id)
        if skill:
            user_skill_map[skill.name] = (us.proficiency, us.confidence or "LOW")

    best_skill = None
    best_score = -1.0
    best_proficiency = 0

    for skill_name in career.required_skills:
        importance = skill_importance.get(skill_name, 1.0)
        proficiency, confidence = user_skill_map.get(skill_name, (0, "LOW"))
        skill_evidence = evidence_by_skill.get(skill_name, [])

        has_assessment = any(ev.source_type == "assessment" for ev in skill_evidence)
        has_high_confidence = confidence == "HIGH"

        if has_high_confidence and proficiency >= 3:
            continue

        gap_size = 5 - proficiency
        evidence_penalty = 0.0
        if not has_assessment:
            evidence_penalty = 0.3
        elif confidence in ("LOW", None):
            evidence_penalty = 0.15

        score = (gap_size / 5.0) * importance + evidence_penalty

        if score > best_score:
            best_score = score
            best_skill = skill_name
            best_proficiency = proficiency

    if not best_skill or best_score <= 0:
        return None

    level_names = {0: "Not started", 1: "Beginner", 2: "Basic", 3: "Intermediate", 4: "Advanced", 5: "Expert"}
    current_label = level_names.get(best_proficiency, f"{best_proficiency}/5")

    return {
        "action_type": "ASSESS_SKILL",
        "title": f"Assess {best_skill}",
        "description": f"Evaluate your {best_skill} proficiency with an AI-powered assessment.",
        "why": f"Largest career-impacting skill gap. Current: {current_label} ({best_proficiency}/5). Target: 4/5.",
        "current": f"{best_proficiency}/5",
        "target": "4/5",
        "skill_name": best_skill,
        "priority_score": round(best_score, 4),
        "metadata": {"skill_name": best_skill, "current_proficiency": best_proficiency},
    }


def _score_retake_assessment(assessments: list[UserAssessment]) -> dict[str, Any] | None:
    """Score RETAKE_ASSESSMENT — trigger when scores are below threshold."""
    if not assessments:
        return None

    latest = max(assessments, key=lambda a: a.created_at)
    scores = latest.scores or {}
    avg_score = sum(scores.values()) / len(scores) if scores else 0.0

    if avg_score >= 0.7:
        return None

    from datetime import datetime, timezone
    days_old = 0
    if latest.created_at:
        now = datetime.now(timezone.utc)
        created = latest.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        days_old = (now - created).days

    recency_bonus = min(days_old / 30.0, 0.3) if days_old > 14 else 0.0
    score = (1.0 - avg_score) * 0.6 + recency_bonus + 0.1

    return {
        "action_type": "RETAKE_ASSESSMENT",
        "title": "Retake Career Assessment",
        "description": "Update your career fit assessment to refine recommendations.",
        "why": f"Your average assessment score is {avg_score:.0%}. Retaking can improve accuracy.",
        "current": f"{avg_score:.0%}",
        "target": "70%+",
        "priority_score": round(score, 4),
        "metadata": {"average_score": avg_score, "days_old": days_old},
    }


def _score_start_phase(
    phases: list[RoadmapPhase],
    progress_items: list[UserProgress],
    user_skills: list[UserSkill],
    career: Career | None,
    all_skills: dict[UUID, Skill],
) -> dict[str, Any] | None:
    """Score START_PHASE — find the next unstarted roadmap phase."""
    if not phases:
        return None

    progress_map: dict[str, str] = {}
    for p in progress_items:
        if p.item_type == "phase":
            progress_map[p.item_id] = p.status

    next_phase = None
    for phase in phases:
        if phase.adaptation_mode == "skipped":
            continue
        phase_status = progress_map.get(str(phase.id), phase.status)
        if phase_status == "not_started":
            next_phase = phase
            break

    if not next_phase:
        return None

    skill_names = next_phase.skills or []
    if career and career.skill_importance:
        avg_importance = sum(
            career.skill_importance.get(s, 1.0) for s in skill_names
        ) / len(skill_names) if skill_names else 0.5
    else:
        avg_importance = 0.5

    user_skill_map = {}
    for us in user_skills:
        skill = all_skills.get(us.skill_id)
        if skill:
            user_skill_map[skill.name] = us.proficiency

    avg_current = sum(user_skill_map.get(s, 0) for s in skill_names) / len(skill_names) if skill_names else 0
    readiness = avg_current / 5.0

    score = avg_importance * 0.5 + (1.0 - readiness) * 0.3 + 0.2

    return {
        "action_type": "START_PHASE",
        "title": f"Start: {next_phase.title}",
        "description": next_phase.objective or f"Begin phase {next_phase.phase_number} of your learning roadmap.",
        "why": f"Next roadmap phase targeting {len(skill_names)} skills. Estimated {next_phase.duration_weeks} weeks.",
        "current": f"Phase {next_phase.phase_number}",
        "target": "Complete",
        "priority_score": round(score, 4),
        "metadata": {
            "phase_id": str(next_phase.id),
            "phase_number": next_phase.phase_number,
            "skills": skill_names,
            "duration_weeks": next_phase.duration_weeks,
        },
    }


def _score_complete_phase(
    phases: list[RoadmapPhase],
    progress_items: list[UserProgress],
) -> dict[str, Any] | None:
    """Score COMPLETE_PHASE — find a phase currently in progress."""
    if not phases:
        return None

    progress_map: dict[str, str] = {}
    for p in progress_items:
        if p.item_type == "phase":
            progress_map[p.item_id] = p.status

    in_progress_phase = None
    for phase in phases:
        if phase.adaptation_mode == "skipped":
            continue
        phase_status = progress_map.get(str(phase.id), phase.status)
        if phase_status == "in_progress":
            in_progress_phase = phase
            break

    if not in_progress_phase:
        return None

    return {
        "action_type": "COMPLETE_PHASE",
        "title": f"Complete: {in_progress_phase.title}",
        "description": in_progress_phase.objective or f"Finish phase {in_progress_phase.phase_number}.",
        "why": "You have a phase in progress. Completing it builds momentum.",
        "current": "In Progress",
        "target": "Completed",
        "priority_score": 0.65,
        "metadata": {
            "phase_id": str(in_progress_phase.id),
            "phase_number": in_progress_phase.phase_number,
        },
    }


def _score_build_project(
    db: Session,
    recommended_projects: list[RecommendedProject],
    progress_items: list[UserProgress],
) -> dict[str, Any] | None:
    """Score BUILD_PROJECT — prioritize in-progress projects, then highest-scored recommended."""
    if not recommended_projects:
        return None

    project_status_map: dict[str, str] = {}
    for p in progress_items:
        if p.item_type == "project":
            project_status_map[p.item_id] = p.status

    in_progress = None
    best_recommended = None
    best_score = -1.0

    for rec in recommended_projects:
        proj_status = project_status_map.get(str(rec.project_id), rec.status)
        if proj_status == "in_progress":
            in_progress = rec
            break
        if proj_status == "recommended":
            score = getattr(rec, 'match_score', None) or 0.5
            if score > best_score:
                best_score = score
                best_recommended = rec

    target_rec = in_progress or best_recommended
    if not target_rec:
        return None

    project = db.query(Project).filter(Project.id == target_rec.project_id).first()
    if not project:
        return None

    status_label = "In Progress" if in_progress else "Recommended"
    score = 0.60 if in_progress else 0.45 + best_score * 0.15

    return {
        "action_type": "BUILD_PROJECT",
        "title": f"Build: {project.title}",
        "description": project.description or f"Work on the {project.title} project.",
        "why": f"Project {status_label.lower()} targeting your skill gaps. {project.estimated_duration_weeks or '?'} weeks.",
        "current": status_label,
        "target": "Completed",
        "priority_score": round(score, 4),
        "metadata": {
            "project_id": str(target_rec.project_id),
            "difficulty": project.difficulty,
            "skills_developed": project.skills_developed,
        },
    }


def _score_upload_resume(
    profile: Profile | None,
    user_skills: list[UserSkill],
) -> dict[str, Any] | None:
    """Score UPLOAD_RESUME — validate low-confidence skill declarations."""
    if profile and profile.work_experience and profile.work_experience.strip():
        return None

    has_skills = len(user_skills) > 0
    if not has_skills:
        return None

    manual_evidence_count = sum(1 for us in user_skills if us.confidence == "LOW")

    if manual_evidence_count == 0:
        return None

    score = 0.35 + min(manual_evidence_count / 10.0, 0.2)

    return {
        "action_type": "UPLOAD_RESUME",
        "title": "Upload Your Resume",
        "description": "Upload your resume to validate skills with real-world evidence.",
        "why": f"{manual_evidence_count} skills have low-confidence declarations. Resume adds MEDIUM confidence.",
        "current": f"{manual_evidence_count} low-confidence",
        "target": "Validated",
        "priority_score": round(score, 4),
        "metadata": {"low_confidence_skills": manual_evidence_count, "link": "/resume"},
    }


def _score_analyze_job(career_recommendation: CareerRecommendation | None) -> dict[str, Any] | None:
    """Score ANALYZE_JOB — map job-specific requirements to skill gaps."""
    if not career_recommendation:
        return None

    missing = career_recommendation.missing_skills or []
    if not missing:
        return None

    score = 0.30 + min(len(missing) / 10.0, 0.2)

    return {
        "action_type": "ANALYZE_JOB",
        "title": "Analyze a Job Description",
        "description": "Paste a job description to identify specific skill gaps.",
        "why": f"You have {len(missing)} missing skills for your target career. Job analysis pinpoints exact gaps.",
        "current": f"{len(missing)} missing",
        "target": "Mapped",
        "priority_score": round(score, 4),
        "metadata": {"missing_skills_count": len(missing), "link": "/job-analyzer"},
    }


def _build_no_action_result() -> dict[str, Any]:
    """Return when no actionable items remain."""
    return {
        "action": None,
        "title": "All Caught Up",
        "description": "No pending actions. Continue building skills and projects.",
        "why": "You have addressed all prioritized actions.",
        "current": None,
        "target": None,
        "skill_name": None,
        "priority_score": 0,
        "career_id": None,
        "career_name": None,
        "metadata": {},
        "all_candidates": [],
    }

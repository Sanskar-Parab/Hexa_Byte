from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.skill import Skill, UserSkill
from app.models.career import Career
from app.models.project import Project, RecommendedProject
from app.models.roadmap import Roadmap, RoadmapPhase
from app.models.progress import UserProgress
from app.models.skill_evidence import SkillEvidence


DIFFICULTY_LEVELS = ["BEGINNER", "INTERMEDIATE", "ADVANCED", "INDUSTRY"]
DIFFICULTY_ORDER = {d: i for i, d in enumerate(DIFFICULTY_LEVELS)}

DIFFICULTY_MAP = {
    "beginner": "BEGINNER",
    "intermediate": "INTERMEDIATE",
    "advanced": "ADVANCED",
    "industry": "INDUSTRY",
}


def compute_user_difficulty_level(
    user_skills: list[UserSkill],
    all_skills: dict[UUID, Skill],
) -> str:
    """Determine the user's current difficulty level based on their skills."""
    if not user_skills:
        return "BEGINNER"

    avg_proficiency = sum(us.proficiency for us in user_skills) / len(user_skills)
    has_advanced = any(us.proficiency >= 4 for us in user_skills)
    has_expert = any(us.proficiency >= 5 for us in user_skills)

    if has_expert and avg_proficiency >= 4.0:
        return "INDUSTRY"
    elif has_advanced and avg_proficiency >= 3.0:
        return "ADVANCED"
    elif avg_proficiency >= 2.0:
        return "INTERMEDIATE"
    return "BEGINNER"


def rank_skill_aware_projects(
    db: Session,
    user_id: UUID,
    career_id: UUID,
    top_n: int = 6,
) -> list[dict[str, Any]]:
    """Rank projects by career relevance, skill-gap relevance, roadmap relevance,
    difficulty fit, and previous project history.

    Returns projects sorted by composite relevance score.
    """
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    all_skills_list = db.query(Skill).all()
    all_skills = {s.id: s for s in all_skills_list}
    all_skills_by_name = {s.name: s for s in all_skills_list}

    career = db.query(Career).filter(Career.id == career_id).first()
    if not career:
        return []

    user_difficulty = compute_user_difficulty_level(user_skills, all_skills)

    roadmap = db.query(Roadmap).filter(
        Roadmap.user_id == user_id,
        Roadmap.career_id == career_id,
    ).first()
    roadmap_skills = set()
    active_phase_skills = set()
    if roadmap:
        phases = db.query(RoadmapPhase).filter(
            RoadmapPhase.roadmap_id == roadmap.id
        ).all()
        for phase in phases:
            if phase.adaptation_mode == "skipped":
                continue
            for s in (phase.skills or []):
                roadmap_skills.add(s)
            if phase.status == "in_progress":
                for s in (phase.skills or []):
                    active_phase_skills.add(s)

    existing_project_ids = {
        rp.project_id
        for rp in db.query(RecommendedProject).filter(
            RecommendedProject.user_id == user_id,
            RecommendedProject.career_id == career_id,
        ).all()
    }

    completed_project_ids = set()
    in_progress_project_ids = set()
    progress_items = db.query(UserProgress).filter(UserProgress.user_id == user_id).all()
    for p in progress_items:
        if p.item_type == "project":
            if p.status == "completed":
                completed_project_ids.add(str(p.item_id))
            elif p.status == "in_progress":
                in_progress_project_ids.add(str(p.item_id))

    evidence_by_skill: dict[str, list[SkillEvidence]] = {}
    evidence_records = db.query(SkillEvidence).filter(SkillEvidence.user_id == user_id).all()
    for ev in evidence_records:
        skill = all_skills.get(ev.skill_id)
        if skill:
            evidence_by_skill.setdefault(skill.name, []).append(ev)

    user_skill_map: dict[str, int] = {}
    for us in user_skills:
        skill = all_skills.get(us.skill_id)
        if skill:
            user_skill_map[skill.name] = us.proficiency

    required_skills = set(career.required_skills or [])
    skill_importance = career.skill_importance or {}

    all_projects = db.query(Project).all()
    scored_projects = []

    for project in all_projects:
        project_skills = set(project.skills_developed or [])
        project_difficulty = DIFFICULTY_MAP.get(
            (project.difficulty or "").lower(), "BEGINNER"
        )

        career_relevance = _compute_career_relevance(
            project_skills, required_skills, skill_importance
        )

        gap_relevance = _compute_gap_relevance(
            project_skills, user_skill_map, skill_importance
        )

        roadmap_relevance = _compute_roadmap_relevance(
            project_skills, roadmap_skills, active_phase_skills
        )

        difficulty_fit = _compute_difficulty_fit(
            project_difficulty, user_difficulty
        )

        history_penalty = _compute_history_penalty(
            project.id, existing_project_ids, completed_project_ids, in_progress_project_ids
        )

        composite_score = (
            career_relevance * 0.30
            + gap_relevance * 0.30
            + roadmap_relevance * 0.20
            + difficulty_fit * 0.15
            + history_penalty * 0.05
        )

        scored_projects.append({
            "project": project,
            "composite_score": round(composite_score, 4),
            "career_relevance": round(career_relevance, 4),
            "gap_relevance": round(gap_relevance, 4),
            "roadmap_relevance": round(roadmap_relevance, 4),
            "difficulty_fit": round(difficulty_fit, 4),
            "history_penalty": round(history_penalty, 4),
            "covers_skills": list(project_skills & required_skills),
            "gap_skills_covered": list(project_skills & {
                s for s, gap in _get_skill_gaps(user_skill_map, required_skills, skill_importance).items()
                if gap > 0
            }),
            "project_difficulty": project_difficulty,
            "user_difficulty": user_difficulty,
        })

    scored_projects.sort(key=lambda x: x["composite_score"], reverse=True)
    return scored_projects[:top_n]


def _get_skill_gaps(
    user_skill_map: dict[str, int],
    required_skills: set[str],
    skill_importance: dict[str, float],
) -> dict[str, float]:
    """Compute skill gaps as importance-weighted priority scores."""
    gaps = {}
    for skill_name in required_skills:
        current = user_skill_map.get(skill_name, 0)
        gap_size = 5 - current
        importance = skill_importance.get(skill_name, 1.0)
        gaps[skill_name] = gap_size * importance
    return gaps


def _compute_career_relevance(
    project_skills: set[str],
    required_skills: set[str],
    skill_importance: dict[str, float],
) -> float:
    """How well does this project cover career-required skills."""
    if not required_skills:
        return 0.0

    overlap = project_skills & required_skills
    if not overlap:
        return 0.0

    total_importance = sum(skill_importance.get(s, 1.0) for s in overlap)
    max_possible = sum(skill_importance.get(s, 1.0) for s in required_skills)

    return total_importance / max_possible if max_possible > 0 else 0.0


def _compute_gap_relevance(
    project_skills: set[str],
    user_skill_map: dict[str, int],
    skill_importance: dict[str, float],
) -> float:
    """How well does this project address the user's actual skill gaps."""
    if not project_skills:
        return 0.0

    gap_score = 0.0
    count = 0
    for skill_name in project_skills:
        current = user_skill_map.get(skill_name, 0)
        gap = 5 - current
        if gap > 0:
            importance = skill_importance.get(skill_name, 1.0)
            gap_score += (gap / 5.0) * importance
            count += 1

    return gap_score / count if count > 0 else 0.0


def _compute_roadmap_relevance(
    project_skills: set[str],
    roadmap_skills: set[str],
    active_phase_skills: set[str],
) -> float:
    """How aligned is this project with the current roadmap."""
    if active_phase_skills:
        active_overlap = project_skills & active_phase_skills
        if active_overlap:
            return 1.0

    if roadmap_skills:
        overlap = project_skills & roadmap_skills
        return len(overlap) / len(roadmap_skills) if roadmap_skills else 0.0

    return 0.3


def _compute_difficulty_fit(
    project_difficulty: str,
    user_difficulty: str,
) -> float:
    """Score how well the project difficulty matches the user's level.

    Perfect match = 1.0, one level off = 0.6, two levels off = 0.2, etc.
    """
    project_idx = DIFFICULTY_ORDER.get(project_difficulty, 0)
    user_idx = DIFFICULTY_ORDER.get(user_difficulty, 0)

    diff = abs(project_idx - user_idx)
    fit_map = {0: 1.0, 1: 0.6, 2: 0.2, 3: 0.0}
    return fit_map.get(diff, 0.0)


def _compute_history_penalty(
    project_id: UUID,
    existing_ids: set[UUID],
    completed_ids: set[str],
    in_progress_ids: set[str],
) -> float:
    """Penalize projects already seen, bonus for fresh recommendations."""
    pid_str = str(project_id)
    if pid_str in completed_ids:
        return 0.0
    if pid_str in in_progress_ids:
        return 0.8
    if project_id in existing_ids:
        return 0.5
    return 1.0


def save_skill_aware_recommendations(
    db: Session,
    user_id: UUID,
    career_id: UUID,
    project_ids: list[UUID],
) -> list[RecommendedProject]:
    """Save ranked project recommendations to database.

    Returns exactly one record per `project_id`, in the same order — reusing
    an existing recommendation when one is already saved from a previous call
    rather than creating a duplicate. Callers rely on a 1:1, same-order
    correspondence with `project_ids`, so a project that already has a saved
    recommendation must still be included in the result.
    """
    result = []
    for pid in project_ids:
        existing = db.query(RecommendedProject).filter(
            RecommendedProject.user_id == user_id,
            RecommendedProject.project_id == pid,
            RecommendedProject.career_id == career_id,
        ).first()
        if existing:
            result.append(existing)
        else:
            rec = RecommendedProject(
                user_id=user_id,
                project_id=pid,
                career_id=career_id,
                status="recommended",
            )
            db.add(rec)
            result.append(rec)
    db.commit()
    return result

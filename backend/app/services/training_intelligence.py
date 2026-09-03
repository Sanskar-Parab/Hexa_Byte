"""Connects training-outcome tracking (app.services.outcome_service) to the
existing student-intelligence engines, per the architecture:

    TrainingProgram -> Skills Taught -> Student Assessment -> Skill Gap ->
    Roadmap -> Projects -> Job Opportunities -> Placement -> EmploymentOutcome

Nothing here is a new scoring/recommendation engine — every function is thin
orchestration over what already exists:

- app.services.opportunity_matching.match_opportunity_skills — training vs.
  student skill comparison (same deterministic matched/partial/missing logic
  already used for job-opportunity matching).
- app.services.opportunity_recommendation.get_user_skill_map /
  get_recommendations — the user's real demonstrated skills and the live
  job/internship recommendation pipeline.
- app.services.career_matching.compute_career_intelligence — career fit.
- app.services.skill_gap.analyze_skill_gaps — skill-gap severity buckets.
- app.services.progress_service.calculate_readiness — the readiness score
  actually used by the dashboard (technical/project/knowledge/communication).
- app.services.resume_service.get_resumes_for_user — resume-readiness signal.
- app.services.readiness._generate_recommendations — deterministic fallback
  "what to do next" text.

Training relevance (calculate_training_relevance) is intentionally free of
any AI call — it's a deterministic skill-overlap ratio. An AI layer may
narrate *why* later, but it never computes or overrides the level itself.
"""
import re
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.career import Career
from app.models.user import User
from app.services import outcome_service
from app.services import career_matching
from app.services.job_analysis_service import TECH_KEYWORDS
from app.services.opportunity_matching import match_opportunity_skills
from app.services.opportunity_recommendation import get_user_skill_map, get_recommendations
from app.services.progress_service import calculate_readiness as _base_calculate_readiness
from app.services.readiness import _generate_recommendations as _fallback_recommendations
from app.services.resume_service import get_resumes_for_user
from app.services.skill_gap import analyze_skill_gaps
from app.services.skill_normalization import (
    build_alias_index,
    dedupe_skill_names,
    match_skill_to_known,
)

# ---------------------------------------------------------------------------
# 1 & 2. Training <-> student skill comparison
# ---------------------------------------------------------------------------


def compare_training_to_student_skills(
    db: Session,
    user_id: UUID,
    training_program_id: UUID,
) -> dict[str, Any] | None:
    """Compare a training program's taught skills against a student's
    demonstrated skills. Reuses the same deterministic matcher used for
    opportunity matching — matched/partial/missing become strong/developing/gap.

    Returns None if the training program doesn't exist.
    """
    program = outcome_service.get_training_program(db, training_program_id)
    if not program:
        return None

    training_skills = outcome_service.training_program_skill_names(db, program)
    user_skill_map = get_user_skill_map(db, user_id)

    match = match_opportunity_skills(training_skills, user_skill_map)

    skill_breakdown = [
        {"skill": item["skill"], "user_proficiency": item["user_proficiency"], "status": "strong"}
        for item in match["matched_skills"]
    ] + [
        {"skill": item["skill"], "user_proficiency": item["user_proficiency"], "status": "developing"}
        for item in match["partial_skills"]
    ] + [
        {"skill": skill, "user_proficiency": 0, "status": "gap"}
        for skill in match["missing_skills"]
    ]

    return {
        "training_program_id": str(program.id),
        "training_program_name": program.name,
        "skills_taught": training_skills,
        "coverage_score": match["match_score"],
        "strong_skills": [item["skill"] for item in match["matched_skills"]],
        "developing_skills": [item["skill"] for item in match["partial_skills"]],
        "gap_skills": match["missing_skills"],
        "skill_breakdown": skill_breakdown,
    }


# ---------------------------------------------------------------------------
# 3. Training relevance (deterministic, no AI)
# ---------------------------------------------------------------------------

HIGH_RELEVANCE_THRESHOLD = 0.5
MEDIUM_RELEVANCE_THRESHOLD = 0.2
DEMONSTRATED_PROFICIENCY_THRESHOLD = 3  # matches STRENGTH_PROFICIENCY_THRESHOLD elsewhere
DEMONSTRATED_PROFICIENCY_BONUS = 0.1


def _find_matching_career(db: Session, job_title: str) -> Career | None:
    title_lower = job_title.strip().lower()
    if not title_lower:
        return None
    careers = db.query(Career).all()
    for career in careers:
        if career.name.lower() == title_lower:
            return career
    for career in careers:
        name_lower = career.name.lower()
        if name_lower in title_lower or title_lower in name_lower:
            return career
    return None


def _infer_job_skills(db: Session, job_title: str | None) -> list[str] | None:
    """Best-effort deterministic skill set implied by a job title.

    Returns None only when there's no title to work from at all — distinct
    from an empty list, which means "we have a title, it just doesn't
    correlate to any known tech skill set" (e.g. "Sales Executive").
    """
    if not job_title or not job_title.strip():
        return None

    career = _find_matching_career(db, job_title)
    if career:
        return dedupe_skill_names((career.required_skills or []) + (career.optional_skills or []))

    title_lower = job_title.lower()
    return [kw for kw in TECH_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", title_lower)]


def calculate_training_relevance(
    db: Session,
    training_skills: list[str],
    student_skill_map: dict[str, int],
    employment_job_title: str | None = None,
    employment_skills: list[str] | None = None,
) -> dict[str, Any]:
    """Deterministic training-relevance level: high / medium / low / unknown.

    Ground truth is a skill-overlap ratio between the training curriculum and
    the best available signal of what the job actually required —
    `employment_skills` if explicitly given, else the skill set of the
    closest-matching Career catalog entry to the job title, else a
    tech-keyword scan of the title itself. The student's own demonstrated
    proficiency in the overlapping skills only ever nudges the score up
    (never required, never down) — it validates the training transferred
    into real ability, it doesn't gate the base comparison.
    """
    normalized_training = dedupe_skill_names(training_skills)
    if not normalized_training:
        return {
            "level": "unknown",
            "reason": "No skills recorded for this training program.",
            "overlap_skills": [],
            "coverage_ratio": 0.0,
        }

    job_skills = (
        dedupe_skill_names(employment_skills)
        if employment_skills
        else _infer_job_skills(db, employment_job_title)
    )

    if job_skills is None:
        return {
            "level": "unknown",
            "reason": "No employment or job title information available to assess relevance.",
            "overlap_skills": [],
            "coverage_ratio": 0.0,
        }

    job_index = build_alias_index(job_skills)
    overlap_skills = [s for s in normalized_training if match_skill_to_known(s, job_index)]
    overlap_count = len(overlap_skills)
    ratio = overlap_count / len(normalized_training)

    demonstrated = [
        s for s in overlap_skills
        if student_skill_map.get(s, 0) >= DEMONSTRATED_PROFICIENCY_THRESHOLD
    ]
    bonus = (
        DEMONSTRATED_PROFICIENCY_BONUS
        if overlap_count > 0 and len(demonstrated) == overlap_count
        else 0.0
    )
    score = min(ratio + bonus, 1.0)

    if score >= HIGH_RELEVANCE_THRESHOLD:
        level = "high"
    elif score >= MEDIUM_RELEVANCE_THRESHOLD:
        level = "medium"
    else:
        level = "low"

    if overlap_skills:
        reason = (
            f"{overlap_count} of {len(normalized_training)} training skills "
            f"({', '.join(overlap_skills)}) apply to this role."
        )
    else:
        reason = "None of the skills taught in this training program apply to this role."

    return {
        "level": level,
        "reason": reason,
        "overlap_skills": overlap_skills,
        "coverage_ratio": round(ratio, 2),
    }


# ---------------------------------------------------------------------------
# 4. Placement readiness (extends the existing readiness engine)
# ---------------------------------------------------------------------------

READINESS_READY_THRESHOLD = 70


def _explain_readiness(
    base: dict[str, Any],
    resume_ready: bool,
    career_context: dict[str, Any] | None,
    training_context: dict[str, Any] | None,
) -> tuple[list[str], list[str]]:
    why_ready: list[str] = []
    what_is_missing: list[str] = []

    if base["technical_skills"] >= 60:
        why_ready.append(f"Technical skill proficiency is strong ({base['technical_skills']}%).")
    else:
        what_is_missing.append(f"Technical skill proficiency is still developing ({base['technical_skills']}%).")

    if base["project_completion"] >= 50:
        why_ready.append(f"{base['project_completion']}% of assigned projects are completed.")
    else:
        what_is_missing.append(f"Only {base['project_completion']}% of assigned projects are completed.")

    if base["core_knowledge"] >= 60:
        why_ready.append(f"Assessment results show solid core knowledge ({base['core_knowledge']}%).")
    else:
        what_is_missing.append(f"Core knowledge assessment score is below target ({base['core_knowledge']}%).")

    if resume_ready:
        why_ready.append("Resume has been uploaded and skills verified.")
    else:
        what_is_missing.append("No resume uploaded yet.")

    if career_context:
        if career_context.get("strengths"):
            why_ready.append(f"Strong match on: {', '.join(career_context['strengths'][:3])}.")
        if career_context.get("skill_gaps"):
            what_is_missing.append(
                f"Missing skills for target career: {', '.join(career_context['skill_gaps'][:3])}."
            )

    if training_context and training_context.get("skill_coverage"):
        coverage = training_context["skill_coverage"]
        if coverage["strong_skills"]:
            why_ready.append(
                f"Demonstrated strong proficiency in training skills: {', '.join(coverage['strong_skills'][:3])}."
            )
        if coverage["gap_skills"]:
            what_is_missing.append(
                f"Training skills not yet demonstrated: {', '.join(coverage['gap_skills'][:3])}."
            )
        if training_context.get("certificate_status") == "issued":
            why_ready.append("Training program certification has been issued.")

    if not why_ready:
        why_ready.append("Building foundational readiness — keep completing assessments and projects.")

    return why_ready, what_is_missing


def calculate_placement_readiness(
    db: Session,
    user_id: UUID,
    career_id: UUID | None = None,
    training_enrollment_id: UUID | None = None,
) -> dict[str, Any] | None:
    """Placement readiness — pure orchestration over the existing readiness,
    career-matching, skill-gap and resume services; introduces no new scoring
    model of its own.

    Returns None only when a training_enrollment_id is given but doesn't
    belong to this user (ownership check) — callers should treat that as a 404.
    """
    base = _base_calculate_readiness(db, user_id, career_id)
    resume_ready = len(get_resumes_for_user(db, user_id)) > 0

    career_context = None
    skill_gap_context = None
    if career_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            career_context = career_matching.compute_career_intelligence(db, user, career_id)
        gap_result = analyze_skill_gaps(db, user_id, career_id)
        if "error" not in gap_result:
            skill_gap_context = gap_result

    training_context = None
    if training_enrollment_id:
        enrollment = outcome_service.get_enrollment(db, user_id, training_enrollment_id)
        if not enrollment:
            return None
        program = outcome_service.get_training_program(db, enrollment.training_program_id)
        skill_coverage = (
            compare_training_to_student_skills(db, user_id, enrollment.training_program_id)
            if program else None
        )
        training_context = {
            "training_program_id": str(enrollment.training_program_id),
            "training_program_name": program.name if program else None,
            "enrollment_status": enrollment.status,
            "attendance_percentage": enrollment.attendance_percentage,
            "assessment_score": enrollment.assessment_score,
            "certificate_status": enrollment.certificate_status,
            "skill_coverage": skill_coverage,
        }

    why_ready, what_is_missing = _explain_readiness(base, resume_ready, career_context, training_context)

    if career_context and career_context.get("recommended_action"):
        recommended_action = career_context["recommended_action"]
    else:
        recommended_action = _fallback_recommendations(
            base["technical_skills"] / 100,
            base["project_completion"] / 100,
            base["core_knowledge"] / 100,
            base["communication"] / 100,
        )[0]

    return {
        "readiness_score": base["overall"],
        "is_ready": base["overall"] >= READINESS_READY_THRESHOLD,
        "breakdown": base,
        "resume_ready": resume_ready,
        "career": career_context,
        "skill_gap": skill_gap_context,
        "training": training_context,
        "why_ready": why_ready,
        "what_is_missing": what_is_missing,
        "recommended_action": recommended_action,
    }


# ---------------------------------------------------------------------------
# 5. Connect to opportunities (delegates to the existing recommendation engine)
# ---------------------------------------------------------------------------

def get_opportunities_for_training(
    db: Session,
    user_id: UUID,
    training_enrollment_id: UUID | None = None,
    opportunity_type: str = "all",
    limit: int = 10,
    min_match: int = 0,
) -> dict[str, Any] | None:
    """Job/internship recommendations biased toward a training program's
    career domain. This is a thin composition over
    app.services.opportunity_recommendation.get_recommendations — the same
    engine used everywhere else — not a second recommendation pipeline, and
    it makes exactly the same single (primary [+ optional secondary]) live
    provider call that function already makes.

    Returns None when training_enrollment_id is given but isn't owned by
    this user — callers should treat that as a 404.
    """
    target_career = None
    if training_enrollment_id:
        enrollment = outcome_service.get_enrollment(db, user_id, training_enrollment_id)
        if not enrollment:
            return None
        program = outcome_service.get_training_program(db, enrollment.training_program_id)
        if program:
            target_career = program.career_domain or program.name

    return get_recommendations(
        db=db,
        user_id=user_id,
        opportunity_type=opportunity_type,
        limit=limit,
        min_match=min_match,
        target_career=target_career,
    )

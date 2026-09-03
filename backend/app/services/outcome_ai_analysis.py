"""AI-assisted outcome analysis (Phase 4).

Reuses the existing Groq client (app.ai.groq_client) — no new AI client is
introduced. The AI is never allowed to invent outcome facts: every piece of
"evidence" fed to it is a deterministic fact computed by the existing
Phase 1-3 services (training_intelligence, outcome_service, career_matching).
The AI's job is strictly to synthesize an explanation FROM that evidence and
to select which evidence items support it — any evidence id it returns that
isn't in the known set computed here is discarded, never trusted.

Confidence is computed deterministically from evidence strength, not
self-reported by the AI, mirroring the Phase 2 principle that a deterministic
score (there: training relevance) is something the AI may only narrate, never
own or override.
"""
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.groq_client import groq_client
from app.models.career import Career
from app.services import outcome_service, training_intelligence
from app.schemas.outcome_ai import (
    EvidenceItem,
    NonPlacementAnalysisResponse,
    AttritionAnalysisResponse,
    TrainingRelevanceExplanationResponse,
)

MIN_EVIDENCE_FOR_HIGH_CONFIDENCE = 3
EVIDENCE_COUNT_FOR_MEDIUM_CONFIDENCE = 2
ALLOWED_ATTRITION_CATEGORIES = {
    "skill_mismatch", "role_mismatch", "location", "salary", "career_change", "unknown",
}


def _confidence_from_evidence_count(count: int) -> str:
    """Confidence reflects how much verified evidence exists, not how sure
    the model 'feels' — kept deterministic and out of the AI's hands.
    0 -> insufficient, 1 -> low, 2 -> medium, 3+ -> high."""
    if count == 0:
        return "insufficient"
    if count >= MIN_EVIDENCE_FOR_HIGH_CONFIDENCE:
        return "high"
    if count == EVIDENCE_COUNT_FOR_MEDIUM_CONFIDENCE:
        return "medium"
    return "low"


def _resolve_evidence_ids(ai_ids: list[str], evidence_by_id: dict[str, str]) -> list[str]:
    """Cross-validates the AI's cited evidence ids against the real,
    deterministically-computed set — any id the model invents is silently
    dropped, never surfaced as if it were real evidence."""
    return [evidence_by_id[i] for i in ai_ids if i in evidence_by_id]


def _fallback_reason(evidence: list[EvidenceItem]) -> str:
    if not evidence:
        return "Insufficient evidence."
    return f"Based on available data: {evidence[0].statement}"


# ---------------------------------------------------------------------------
# 1. Non-placement analysis
# ---------------------------------------------------------------------------

def _gather_non_placement_evidence(
    db: Session,
    user_id: UUID,
    career_id: UUID | None,
    training_enrollment_id: UUID | None,
) -> tuple[list[EvidenceItem], list[EvidenceItem]]:
    """Returns (context_evidence, signal_evidence).

    context_evidence is always-present background (the overall readiness
    score) that doesn't by itself explain anything. signal_evidence is the
    set of *specific* negative findings that could actually explain
    non-placement — it alone drives confidence and the insufficient-evidence
    gate, so a well-rounded student we simply have no explanatory signal for
    correctly comes back "insufficient evidence" rather than the AI being
    handed a lone readiness percentage and asked to invent a story around it.
    """
    readiness = training_intelligence.calculate_placement_readiness(
        db, user_id, career_id=career_id, training_enrollment_id=training_enrollment_id,
    )
    if readiness is None:  # explicit training_enrollment_id not owned by caller
        return [], []

    breakdown = readiness["breakdown"]
    context: list[EvidenceItem] = [EvidenceItem(
        id="readiness_score",
        statement=f"Overall placement readiness score: {breakdown['overall']}%",
    )]
    signals: list[EvidenceItem] = []

    if breakdown["technical_skills"] < 60:
        signals.append(EvidenceItem(
            id="technical_skills",
            statement=f"Technical skill proficiency is below target: {breakdown['technical_skills']}%",
        ))
    if breakdown["project_completion"] < 50:
        signals.append(EvidenceItem(
            id="project_completion",
            statement=f"Project completion is below target: {breakdown['project_completion']}%",
        ))
    if breakdown["core_knowledge"] < 60:
        signals.append(EvidenceItem(
            id="core_knowledge",
            statement=f"Core knowledge assessment score is below target: {breakdown['core_knowledge']}%",
        ))
    if not readiness["resume_ready"]:
        signals.append(EvidenceItem(id="resume_status", statement="No resume has been uploaded."))

    career = readiness.get("career")
    if career:
        signals.append(EvidenceItem(
            id="career_match",
            statement=f"Career match score for {career['career_name']}: {round(career['match_score'] * 100)}%",
        ))
        for skill in (career.get("skill_gaps") or [])[:3]:
            signals.append(EvidenceItem(
                id=f"career_gap_{skill}", statement=f"Missing skill for target career: {skill}",
            ))

    training = readiness.get("training")
    if training:
        coverage = training.get("skill_coverage")
        if coverage:
            for skill in (coverage.get("gap_skills") or [])[:3]:
                signals.append(EvidenceItem(
                    id=f"training_gap_{skill}",
                    statement=f"Training-taught skill not yet demonstrated: {skill}",
                ))
        attendance = training.get("attendance_percentage")
        if attendance is not None and attendance < 75:
            signals.append(EvidenceItem(
                id="training_attendance",
                statement=f"Training attendance was low: {attendance}%",
            ))

    return context, signals


def analyze_non_placement(
    db: Session,
    user_id: UUID,
    career_id: UUID | None = None,
    training_enrollment_id: UUID | None = None,
) -> NonPlacementAnalysisResponse | None:
    """Returns None only when an explicit training_enrollment_id was given
    but isn't owned by the caller — treat as a 404."""
    if training_enrollment_id and not outcome_service.get_enrollment(db, user_id, training_enrollment_id):
        return None

    context_evidence, signal_evidence = _gather_non_placement_evidence(
        db, user_id, career_id, training_enrollment_id,
    )
    evidence = context_evidence + signal_evidence
    evidence_by_id = {e.id: e.statement for e in evidence}
    confidence = _confidence_from_evidence_count(len(signal_evidence))

    target_career = None
    if career_id:
        career = db.query(Career).filter(Career.id == career_id).first()
        target_career = career.name if career else None

    if not signal_evidence:
        return NonPlacementAnalysisResponse(
            primary_reason="Insufficient evidence.",
            supporting_evidence=[],
            confidence="insufficient",
            recommended_intervention="Complete a skill assessment and add at least one project to build a basis for analysis.",
            source="fallback",
            evidence=evidence,
        )

    ai_result, _ = groq_client.analyze_non_placement(
        evidence=[{"id": e.id, "statement": e.statement} for e in evidence],
        target_career=target_career,
    )

    if ai_result:
        supporting = _resolve_evidence_ids(ai_result.supporting_evidence_ids, evidence_by_id)
        return NonPlacementAnalysisResponse(
            primary_reason=ai_result.primary_reason,
            supporting_evidence=supporting or [e.statement for e in signal_evidence[:2]],
            confidence=confidence,
            recommended_intervention=ai_result.recommended_intervention,
            source="ai",
            evidence=evidence,
        )

    return NonPlacementAnalysisResponse(
        primary_reason=_fallback_reason(signal_evidence),
        supporting_evidence=[e.statement for e in signal_evidence[:3]],
        confidence=confidence,
        recommended_intervention="Review the evidence below with your mentor to identify the next concrete step.",
        source="fallback",
        evidence=evidence,
    )


# ---------------------------------------------------------------------------
# 2. Attrition analysis
# ---------------------------------------------------------------------------

def _gather_attrition_evidence(db: Session, user_id: UUID, employment_outcome_id: UUID):
    """Returns (outcome, context_evidence, signal_evidence).

    outcome is None only when the id isn't owned by the caller. Tenure
    (how long the job lasted) is context, not a signal — it doesn't explain
    *why* employment ended, so on its own it must not count as "we have
    evidence" any more than a bare readiness score does for non-placement.
    signal_evidence is [] both when employment hasn't ended yet and when it
    has ended with nothing else recorded about why.
    """
    outcome = outcome_service.get_employment_outcome(db, user_id, employment_outcome_id)
    if not outcome:
        return None, [], []

    if not outcome.employment_end_date:
        return outcome, [], []

    context: list[EvidenceItem] = []
    if outcome.employment_start_date:
        tenure_days = (outcome.employment_end_date - outcome.employment_start_date).days
        context.append(EvidenceItem(id="tenure", statement=f"Employment lasted {tenure_days} days."))

    signals: list[EvidenceItem] = []

    check_ins = sorted(
        outcome_service.list_check_ins(db, user_id, employment_outcome_id=outcome.id),
        key=lambda c: c.check_in_date,
    )

    check_ins_with_reason = [c for c in check_ins if c.reason_for_leaving]
    if check_ins_with_reason:
        signals.append(EvidenceItem(
            id="reason_for_leaving",
            statement=f"Self-reported reason for leaving: {check_ins_with_reason[-1].reason_for_leaving}",
        ))

    check_ins_with_notes = [c for c in check_ins if c.notes]
    if check_ins_with_notes:
        signals.append(EvidenceItem(
            id="check_in_notes",
            statement=f"Latest check-in notes: {check_ins_with_notes[-1].notes}",
        ))

    salary_points = [outcome.salary] if outcome.salary is not None else []
    salary_points += [c.salary for c in check_ins if c.salary is not None]
    if len(salary_points) >= 2 and salary_points[-1] < salary_points[0]:
        signals.append(EvidenceItem(
            id="salary_decline",
            statement=f"Salary decreased from {salary_points[0]} to {salary_points[-1]} before employment ended.",
        ))

    if outcome.job_title and outcome.training_enrollment_id:
        enrollment = outcome_service.get_enrollment(db, user_id, outcome.training_enrollment_id)
        program = outcome_service.get_training_program(db, enrollment.training_program_id) if enrollment else None
        if program:
            training_skills = outcome_service.training_program_skill_names(db, program)
            student_skill_map = training_intelligence.get_user_skill_map(db, user_id)
            relevance = training_intelligence.calculate_training_relevance(
                db, training_skills, student_skill_map, employment_job_title=outcome.job_title,
            )
            if relevance["level"] in ("low", "unknown"):
                signals.append(EvidenceItem(
                    id="training_relevance",
                    statement=f"Training relevance to this role was {relevance['level']} ({relevance['reason']}).",
                ))

    return outcome, context, signals


def analyze_attrition(
    db: Session,
    user_id: UUID,
    employment_outcome_id: UUID,
) -> AttritionAnalysisResponse | None:
    """Returns None only when employment_outcome_id isn't owned by the
    caller — treat as a 404."""
    outcome, context_evidence, signal_evidence = _gather_attrition_evidence(db, user_id, employment_outcome_id)
    if outcome is None:
        return None

    evidence = context_evidence + signal_evidence
    evidence_by_id = {e.id: e.statement for e in evidence}
    confidence = _confidence_from_evidence_count(len(signal_evidence))

    if not signal_evidence:
        return AttritionAnalysisResponse(
            category="unknown",
            primary_reason="Insufficient evidence.",
            supporting_evidence=[],
            confidence="insufficient",
            recommended_intervention="Encourage a follow-up check-in with a stated reason for leaving to enable analysis.",
            source="fallback",
            evidence=evidence,
        )

    ai_result, _ = groq_client.analyze_attrition(
        evidence=[{"id": e.id, "statement": e.statement} for e in evidence],
    )

    if ai_result:
        category = ai_result.category if ai_result.category in ALLOWED_ATTRITION_CATEGORIES else "unknown"
        supporting = _resolve_evidence_ids(ai_result.supporting_evidence_ids, evidence_by_id)
        return AttritionAnalysisResponse(
            category=category,
            primary_reason=ai_result.primary_reason,
            supporting_evidence=supporting or [e.statement for e in signal_evidence[:2]],
            confidence=confidence,
            recommended_intervention=ai_result.recommended_intervention,
            source="ai",
            evidence=evidence,
        )

    return AttritionAnalysisResponse(
        category="unknown",
        primary_reason=_fallback_reason(signal_evidence),
        supporting_evidence=[e.statement for e in signal_evidence[:3]],
        confidence=confidence,
        recommended_intervention="Review the evidence below with a mentor to identify the next concrete step.",
        source="fallback",
        evidence=evidence,
    )


# ---------------------------------------------------------------------------
# 3. Training relevance explanation (deterministic score, AI narration only)
# ---------------------------------------------------------------------------

def explain_training_relevance(
    db: Session,
    user_id: UUID,
    training_program_id: UUID,
    employment_job_title: str | None = None,
) -> TrainingRelevanceExplanationResponse | None:
    """Returns None only when the training program doesn't exist. The
    `level` on the response always comes from the deterministic calculation
    below — the AI is never given a chance to set or change it."""
    program = outcome_service.get_training_program(db, training_program_id)
    if not program:
        return None

    training_skills = outcome_service.training_program_skill_names(db, program)
    student_skill_map = training_intelligence.get_user_skill_map(db, user_id)

    deterministic = training_intelligence.calculate_training_relevance(
        db, training_skills, student_skill_map, employment_job_title=employment_job_title,
    )

    ai_result, _ = groq_client.explain_training_relevance(
        level=deterministic["level"],
        training_skills=training_skills,
        job_title=employment_job_title or "",
        overlap_skills=deterministic["overlap_skills"],
        coverage_ratio=deterministic["coverage_ratio"],
    )

    return TrainingRelevanceExplanationResponse(
        level=deterministic["level"],
        explanation=ai_result.explanation if ai_result else deterministic["reason"],
        overlap_skills=deterministic["overlap_skills"],
        coverage_ratio=deterministic["coverage_ratio"],
        source="ai" if ai_result else "fallback",
    )

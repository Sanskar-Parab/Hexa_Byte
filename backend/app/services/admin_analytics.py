"""Government/administrator skilling-impact analytics (Phase 5).

A strictly separate, admin-only view from the student-facing app — see
app.utils.auth.get_current_admin_user; nothing here is reachable by a
regular student account.

Every metric is computed directly from stored TrainingEnrollment /
EmploymentOutcome / OutcomeCheckIn rows at request time. Nothing is
fabricated, estimated, or hardcoded — a metric with no supporting data comes
back as `null`, never a made-up 0%. All arithmetic reuses the exact same
deterministic building blocks as the per-student views:

- Retention: app.services.outcome_timeline._retention_at_milestone (Phase 3)
- Training relevance: app.services.training_intelligence.calculate_training_relevance (Phase 2)
- Skill-gap comparison: app.services.training_intelligence.compare_training_to_student_skills (Phase 2)
- Non-placement evidence: app.services.outcome_ai_analysis._gather_non_placement_evidence (Phase 4)
  — the evidence-gathering only; the AI is never called for a dashboard
  aggregate, since it must stay fast and 100% reproducible across requests.

Cohorts below MIN_COHORT_SIZE have their rates and averages suppressed
(only the trainee count and a flag are shown) — both to avoid ranking a
tiny sample as if it were reliable, and because a rate/average computed
over 1-4 people starts to reveal that individual's own data.
"""
from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.outcome import TrainingEnrollment, TrainingProgram, EmploymentOutcome, OutcomeCheckIn
from app.models.user import User
from app.services import outcome_service, training_intelligence, outcome_ai_analysis
from app.services.outcome_timeline import _add_months, _retention_at_milestone, MILESTONE_MONTHS
from app.services.opportunity_recommendation import get_user_skill_map

MIN_COHORT_SIZE = 5
RECURRING_GAP_THRESHOLD_PCT = 30.0

PLACED_STATUSES = {"placed", "employed", "self_employed"}
NOT_PLACED_STATUSES = {"not_employed", "looking_for_work"}
RELEVANT_LEVELS = {"high", "medium"}
TOP_SKILL_GAPS_LIMIT = 10


@dataclass
class AnalyticsFilters:
    start_date: date | None = None
    end_date: date | None = None
    provider_name: str | None = None
    training_program_id: UUID | None = None
    career_domain: str | None = None
    location: str | None = None
    employment_status: str | None = None


@dataclass
class TraineeRecord:
    user_id: UUID
    enrollment: TrainingEnrollment
    program: TrainingProgram
    outcome: EmploymentOutcome | None
    check_ins: list[OutcomeCheckIn] = field(default_factory=list)
    training_skills: list[str] = field(default_factory=list)
    is_demo: bool = False


def _rate(numerator: int, denominator: int) -> float | None:
    """None (not 0.0) when there's no basis to compute a rate at all —
    a missing metric must never be presented as a real zero."""
    if denominator == 0:
        return None
    return round(numerator / denominator * 100, 1)


# ---------------------------------------------------------------------------
# Building the trainee cohort from stored data + filters
# ---------------------------------------------------------------------------

def _build_trainee_records(db: Session, filters: AnalyticsFilters) -> list[TraineeRecord]:
    query = db.query(TrainingEnrollment).join(
        TrainingProgram, TrainingEnrollment.training_program_id == TrainingProgram.id,
    )
    if filters.start_date:
        query = query.filter(TrainingEnrollment.enrollment_date >= filters.start_date)
    if filters.end_date:
        query = query.filter(TrainingEnrollment.enrollment_date <= filters.end_date)
    if filters.provider_name:
        query = query.filter(TrainingProgram.provider_name == filters.provider_name)
    if filters.training_program_id:
        query = query.filter(TrainingEnrollment.training_program_id == filters.training_program_id)
    if filters.career_domain:
        query = query.filter(TrainingProgram.career_domain == filters.career_domain)
    enrollments = query.all()

    programs_by_id = {p.id: p for p in db.query(TrainingProgram).all()}
    outcomes_by_enrollment_id = {
        o.training_enrollment_id: o
        for o in db.query(EmploymentOutcome).all()
        if o.training_enrollment_id is not None
    }
    demo_user_ids = {u.id for u in db.query(User).filter(User.is_demo.is_(True)).all()}

    records: list[TraineeRecord] = []
    for enrollment in enrollments:
        program = programs_by_id.get(enrollment.training_program_id)
        if not program:
            continue
        outcome = outcomes_by_enrollment_id.get(enrollment.id)

        if filters.employment_status:
            if not outcome or outcome.employment_status != filters.employment_status:
                continue
        if filters.location:
            if not outcome or outcome.location != filters.location:
                continue

        check_ins: list[OutcomeCheckIn] = []
        if outcome:
            check_ins = sorted(
                outcome_service.list_check_ins(db, enrollment.user_id, employment_outcome_id=outcome.id),
                key=lambda c: c.check_in_date,
            )

        records.append(TraineeRecord(
            user_id=enrollment.user_id,
            enrollment=enrollment,
            program=program,
            outcome=outcome,
            check_ins=check_ins,
            training_skills=outcome_service.training_program_skill_names(db, program),
            is_demo=enrollment.user_id in demo_user_ids,
        ))

    return records


# ---------------------------------------------------------------------------
# Per-cohort metric calculators (shared by overview / provider / program views)
# ---------------------------------------------------------------------------

def _overall_counts(records: list[TraineeRecord]) -> dict:
    total = len(records)
    completed = sum(1 for r in records if r.enrollment.status == "completed")
    with_outcome = [r for r in records if r.outcome]
    placed = sum(1 for r in with_outcome if r.outcome.employment_status in PLACED_STATUSES)
    employed = sum(1 for r in with_outcome if r.outcome.employment_status == "employed")
    self_employed = sum(1 for r in with_outcome if r.outcome.employment_status == "self_employed")
    not_placed_explicit = sum(1 for r in with_outcome if r.outcome.employment_status in NOT_PLACED_STATUSES)

    return {
        "total": total,
        "completed": completed,
        "placed": placed,
        "employed": employed,
        "self_employed": self_employed,
        "not_placed_explicit": not_placed_explicit,
        "non_placed": total - placed,
    }


def _retention_rates(records: list[TraineeRecord]) -> dict[str, dict]:
    """Retention among the cohort whose milestone status is actually
    *decided* (a real "yes" or "no" on record) — a milestone that hasn't
    been reached yet, or has no check-in, is excluded from both the
    numerator and the denominator rather than counted against the rate."""
    today = date.today()
    result: dict[str, dict] = {}

    for months in MILESTONE_MONTHS:
        yes = no = 0
        for r in records:
            if not r.outcome or not r.outcome.employment_start_date:
                continue
            milestone_date = _add_months(r.outcome.employment_start_date, months)
            reached = today >= milestone_date
            status = _retention_at_milestone(r.outcome, r.check_ins, milestone_date, reached)["status"]
            if status == "yes":
                yes += 1
            elif status == "no":
                no += 1

        decided = yes + no
        result[f"{months}_month"] = {
            "retained": yes,
            "not_retained": no,
            "decided_count": decided,
            "rate": _rate(yes, decided),
        }

    return result


def _latest_known_salary(record: TraineeRecord) -> float | None:
    for check_in in reversed(record.check_ins):
        if check_in.salary is not None:
            return check_in.salary
    return record.outcome.salary if record.outcome else None


def _salary_metrics(records: list[TraineeRecord]) -> dict:
    starting: list[float] = []
    current: list[float] = []
    paired: list[tuple[float, float]] = []

    for r in records:
        if not r.outcome:
            continue
        start_salary = r.outcome.salary
        current_salary = _latest_known_salary(r)

        if start_salary is not None:
            starting.append(start_salary)
        if current_salary is not None:
            current.append(current_salary)
        if start_salary is not None and current_salary is not None:
            paired.append((start_salary, current_salary))

    wage_growth_pct = None
    if paired:
        avg_paired_start = sum(p[0] for p in paired) / len(paired)
        avg_paired_current = sum(p[1] for p in paired) / len(paired)
        if avg_paired_start:
            wage_growth_pct = round((avg_paired_current - avg_paired_start) / avg_paired_start * 100, 1)

    return {
        "average_starting_salary": round(sum(starting) / len(starting), 2) if starting else None,
        "starting_salary_sample_size": len(starting),
        "average_current_salary": round(sum(current) / len(current), 2) if current else None,
        "current_salary_sample_size": len(current),
        "wage_growth_percentage": wage_growth_pct,
        "wage_growth_sample_size": len(paired),
    }


def _training_relevance_metrics(db: Session, records: list[TraineeRecord]) -> dict:
    relevant = 0
    evaluated = 0
    for r in records:
        if not r.outcome or not r.outcome.job_title or not r.training_skills:
            continue
        skill_map = get_user_skill_map(db, r.user_id)
        result = training_intelligence.calculate_training_relevance(
            db, r.training_skills, skill_map, employment_job_title=r.outcome.job_title,
        )
        evaluated += 1
        if result["level"] in RELEVANT_LEVELS:
            relevant += 1
    return {"relevant_count": relevant, "evaluated_count": evaluated, "rate": _rate(relevant, evaluated)}


def _cohort_metrics(db: Session, records: list[TraineeRecord]) -> dict:
    """The full metric suite for one cohort (all trainees, one provider, or
    one program) — the shared computation behind overview/provider/program views."""
    counts = _overall_counts(records)
    retention = _retention_rates(records)
    salary = _salary_metrics(records)
    relevance = _training_relevance_metrics(db, records)
    total = counts["total"]
    sufficient = total >= MIN_COHORT_SIZE

    metrics = {
        "trainee_count": total,
        "demo_trainee_count": sum(1 for r in records if r.is_demo),
        "sample_size_sufficient": sufficient,
        "training_completion_rate": _rate(counts["completed"], total),
        "placement_rate": _rate(counts["placed"], total),
        "employment_rate": _rate(counts["employed"], total),
        "self_employment_rate": _rate(counts["self_employed"], total),
        "unemployment_rate": _rate(counts["not_placed_explicit"], total),
        "non_placement_rate": _rate(counts["non_placed"], total),
        "retention_3_month_rate": retention["3_month"]["rate"],
        "retention_6_month_rate": retention["6_month"]["rate"],
        "retention_12_month_rate": retention["12_month"]["rate"],
        "average_starting_salary": salary["average_starting_salary"],
        "average_current_salary": salary["average_current_salary"],
        "wage_growth_percentage": salary["wage_growth_percentage"],
        "training_relevant_employment_rate": relevance["rate"],
    }

    if not sufficient:
        # Below the privacy/reliability threshold: keep the count visible,
        # suppress every rate/average that could approximate an individual's data.
        for key in metrics:
            if key not in ("trainee_count", "demo_trainee_count", "sample_size_sufficient"):
                metrics[key] = None

    return metrics


# ---------------------------------------------------------------------------
# 1. Overview
# ---------------------------------------------------------------------------

def get_overview_metrics(db: Session, filters: AnalyticsFilters) -> dict:
    records = _build_trainee_records(db, filters)
    return _cohort_metrics(db, records)


# ---------------------------------------------------------------------------
# 2 & 3. Provider comparison / program analytics
# ---------------------------------------------------------------------------

def get_provider_comparison(db: Session, filters: AnalyticsFilters) -> list[dict]:
    records = _build_trainee_records(db, filters)
    groups: dict[str, list[TraineeRecord]] = {}
    for r in records:
        groups.setdefault(r.program.provider_name, []).append(r)

    results = []
    for provider_name, group_records in groups.items():
        row = {"provider_name": provider_name, **_cohort_metrics(db, group_records)}
        results.append(row)

    results.sort(key=lambda r: (
        not r["sample_size_sufficient"],
        -(r["placement_rate"] if r["placement_rate"] is not None else -1),
    ))
    return results


def get_program_analytics(db: Session, filters: AnalyticsFilters) -> list[dict]:
    records = _build_trainee_records(db, filters)
    groups: dict[UUID, list[TraineeRecord]] = {}
    for r in records:
        groups.setdefault(r.program.id, []).append(r)

    results = []
    for program_id, group_records in groups.items():
        program = group_records[0].program
        row = {
            "training_program_id": str(program_id),
            "training_program_name": program.name,
            "provider_name": program.provider_name,
            "career_domain": program.career_domain,
            **_cohort_metrics(db, group_records),
        }
        if row["sample_size_sufficient"]:
            row["skill_gaps"] = _skill_gap_analytics(db, group_records)
        else:
            row["skill_gaps"] = []
        results.append(row)

    results.sort(key=lambda r: (
        not r["sample_size_sufficient"],
        -(r["placement_rate"] if r["placement_rate"] is not None else -1),
    ))
    return results


# ---------------------------------------------------------------------------
# 4. Skill gap analytics
# ---------------------------------------------------------------------------

def _skill_gap_analytics(db: Session, records: list[TraineeRecord]) -> list[dict]:
    considered = [r for r in records if r.training_skills]
    total = len(considered)
    if total == 0:
        return []

    gap_counts: dict[str, int] = {}
    for r in considered:
        comparison = training_intelligence.compare_training_to_student_skills(db, r.user_id, r.program.id)
        if not comparison:
            continue
        for skill in comparison["gap_skills"]:
            gap_counts[skill] = gap_counts.get(skill, 0) + 1

    ranked = sorted(gap_counts.items(), key=lambda kv: kv[1], reverse=True)[:TOP_SKILL_GAPS_LIMIT]
    return [{"skill": skill, "trainee_count": n, "percentage": _rate(n, total)} for skill, n in ranked]


def get_skill_gap_analytics(db: Session, filters: AnalyticsFilters) -> list[dict]:
    records = _build_trainee_records(db, filters)
    return _skill_gap_analytics(db, records)


# ---------------------------------------------------------------------------
# 5. Non-placement analytics
# ---------------------------------------------------------------------------

def _classify_non_placement(signal_evidence) -> str:
    """Deterministic, evidence-id-based classification — no AI call, so a
    dashboard aggregate over hundreds of trainees stays fast and
    100% reproducible. Only categories this system can actually support
    with stored data exist here (no 'location mismatch' or 'insufficient
    opportunities' — neither is tracked anywhere in the schema)."""
    ids = {e.id for e in signal_evidence}
    skill_signal_ids = {"technical_skills", "project_completion", "core_knowledge"}
    if ids & skill_signal_ids or any(i.startswith("career_gap_") or i.startswith("training_gap_") for i in ids):
        return "skill_gap"
    if "resume_status" in ids:
        return "profile_incomplete"
    return "unknown"


def get_non_placement_analytics(db: Session, filters: AnalyticsFilters) -> list[dict]:
    records = _build_trainee_records(db, filters)
    non_placed = [r for r in records if not r.outcome or r.outcome.employment_status not in PLACED_STATUSES]
    total = len(non_placed)
    if total == 0:
        return []

    counts: dict[str, int] = {}
    for r in non_placed:
        _, signal_evidence = outcome_ai_analysis._gather_non_placement_evidence(
            db, r.user_id, career_id=None, training_enrollment_id=r.enrollment.id,
        )
        category = _classify_non_placement(signal_evidence)
        counts[category] = counts.get(category, 0) + 1

    return [
        {"category": category, "trainee_count": n, "percentage": _rate(n, total)}
        for category, n in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    ]


# ---------------------------------------------------------------------------
# Filter option discovery (for the frontend's filter dropdowns)
# ---------------------------------------------------------------------------

def get_curriculum_recommendations(db: Session, filters: AnalyticsFilters) -> list[dict]:
    """The adaptive/evidence-driven improvement loop (Phase 6): outcome data
    feeding back into training-quality signals.

    Purely a threshold over numbers already computed by get_program_analytics
    — no AI, no new scoring model. A skill gap shared by a large share of a
    program's trainees, occurring alongside a below-(cross-program)-average
    placement rate for that specific program, is flagged. Small-sample
    programs are excluded entirely (same MIN_COHORT_SIZE reliability rule as
    everywhere else in this module).
    """
    programs = get_program_analytics(db, filters)
    sufficient = [p for p in programs if p["sample_size_sufficient"]]
    placement_rates = [p["placement_rate"] for p in sufficient if p["placement_rate"] is not None]
    if not placement_rates:
        return []
    overall_placement_rate = round(sum(placement_rates) / len(placement_rates), 1)

    recommendations = []
    for program in sufficient:
        if program["placement_rate"] is None or program["placement_rate"] >= overall_placement_rate:
            continue
        for gap in program["skill_gaps"]:
            if (gap["percentage"] or 0) < RECURRING_GAP_THRESHOLD_PCT:
                continue
            recommendations.append({
                "training_program_id": program["training_program_id"],
                "training_program_name": program["training_program_name"],
                "provider_name": program["provider_name"],
                "skill": gap["skill"],
                "affected_trainee_percentage": gap["percentage"],
                "program_placement_rate": program["placement_rate"],
                "overall_placement_rate": overall_placement_rate,
                "recommendation": (
                    f"{gap['skill']} is a recurring skill gap among {program['training_program_name']} trainees "
                    f"({gap['percentage']}% affected), alongside a below-average placement rate "
                    f"({program['placement_rate']}% vs {overall_placement_rate}% across programs). "
                    f"Consider strengthening {gap['skill']} in the curriculum."
                ),
            })

    recommendations.sort(key=lambda r: r["affected_trainee_percentage"], reverse=True)
    return recommendations


# ---------------------------------------------------------------------------
# Filter option discovery (for the frontend's filter dropdowns)
# ---------------------------------------------------------------------------

def get_filter_options(db: Session) -> dict:
    providers = sorted({p.provider_name for p in db.query(TrainingProgram).all()})
    domains = sorted({p.career_domain for p in db.query(TrainingProgram).all() if p.career_domain})
    programs = [
        {"id": str(p.id), "name": p.name, "provider_name": p.provider_name}
        for p in db.query(TrainingProgram).order_by(TrainingProgram.name).all()
    ]
    locations = sorted({o.location for o in db.query(EmploymentOutcome).all() if o.location})
    return {
        "providers": providers,
        "career_domains": domains,
        "programs": programs,
        "locations": locations,
        "employment_statuses": sorted(PLACED_STATUSES | NOT_PLACED_STATUSES),
    }

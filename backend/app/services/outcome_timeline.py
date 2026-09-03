"""Longitudinal employment-outcome tracking (Phase 3).

Builds the post-training timeline — Training -> Placement -> Employment ->
3/6/12-month check-ins — purely from data that has actually been recorded.
Nothing here fabricates history: a milestone that hasn't been reached yet is
"pending", and a milestone that has been reached but has no check-in on
record is "unknown" — never silently assumed to be a success.

Retention and wage-progression math are both plain, deterministic arithmetic
(no AI, no estimation). Training relevance re-uses
app.services.training_intelligence.calculate_training_relevance — the same
deterministic skill-overlap calculation from Phase 2 — applied at placement
time and at each check-in, so "does this job still match the training" can
be tracked as the job/role changes over time.
"""
import calendar
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.outcome import EmploymentOutcome, OutcomeCheckIn, TrainingEnrollment
from app.services import outcome_service
from app.services.opportunity_recommendation import get_user_skill_map
from app.services.training_intelligence import calculate_training_relevance

MILESTONE_MONTHS = (3, 6, 12)
CONTINUED_EMPLOYMENT_STATUSES = {"employed", "self_employed", "placed"}


def _add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _find_check_in_for_milestone(
    check_ins_sorted: list[OutcomeCheckIn],
    milestone_date: date,
) -> OutcomeCheckIn | None:
    """The earliest check-in at/after the milestone (freshest confirmation of
    status as of that point); falls back to the most recent check-in
    available if none exists yet at/after the milestone."""
    on_or_after = [c for c in check_ins_sorted if c.check_in_date >= milestone_date]
    if on_or_after:
        return on_or_after[0]
    if check_ins_sorted:
        return check_ins_sorted[-1]
    return None


def _retention_at_milestone(
    outcome: EmploymentOutcome,
    check_ins_sorted: list[OutcomeCheckIn],
    milestone_date: date,
    reached: bool,
) -> dict[str, Any]:
    if not reached:
        return {"status": "pending", "check_in": None}

    if outcome.employment_end_date and outcome.employment_end_date < milestone_date:
        return {"status": "no", "check_in": None}

    candidate = _find_check_in_for_milestone(check_ins_sorted, milestone_date)
    if candidate is None:
        return {"status": "unknown", "check_in": None}

    still_employed = candidate.still_employed
    if still_employed is None:
        still_employed = candidate.employment_status in CONTINUED_EMPLOYMENT_STATUSES

    return {"status": "yes" if still_employed else "no", "check_in": candidate}


def _salary_snapshot(amount, currency, period, as_of) -> dict[str, Any] | None:
    """Never fabricates a value — returns None whenever the amount itself is unrecorded."""
    if amount is None:
        return None
    return {"amount": amount, "currency": currency, "period": period, "date": as_of}


def _compute_salary_change(old: dict, new: dict) -> dict[str, Any] | None:
    """Percentage_change = ((new - old) / old) * 100. Safe against a zero
    baseline (division by zero) and against either side being unrecorded."""
    old_amount = old.get("amount")
    new_amount = new.get("amount")
    if old_amount is None or new_amount is None:
        return None

    absolute_change = round(new_amount - old_amount, 2)
    percentage_change = round((absolute_change / old_amount) * 100, 2) if old_amount else None

    return {
        "from_date": old["date"],
        "to_date": new["date"],
        "absolute_change": absolute_change,
        "percentage_change": percentage_change,
    }


def _check_in_summary(c: OutcomeCheckIn) -> dict[str, Any]:
    return {
        "id": str(c.id),
        "check_in_date": c.check_in_date,
        "months_since_employment": c.months_since_employment,
        "employment_status": c.employment_status,
        "company_name": c.company_name,
        "job_title": c.job_title,
        "salary": c.salary,
        "salary_currency": c.salary_currency,
        "salary_period": c.salary_period,
        "training_relevance": c.training_relevance,
        "still_employed": c.still_employed,
        "reason_for_leaving": c.reason_for_leaving,
        "notes": c.notes,
    }


def _pick_enrollment(db: Session, user_id: UUID, training_enrollment_id: UUID | None) -> TrainingEnrollment | None | bool:
    """Returns the enrollment to build the timeline around, None if the user
    has none, or False as a sentinel meaning "an id was given but doesn't
    belong to this user" (caller should treat that as 404, distinct from
    "no training on record at all")."""
    if training_enrollment_id:
        enrollment = outcome_service.get_enrollment(db, user_id, training_enrollment_id)
        return enrollment if enrollment else False
    enrollments = outcome_service.list_enrollments(db, user_id)  # newest first
    return enrollments[0] if enrollments else None


def build_outcome_timeline(
    db: Session,
    user_id: UUID,
    training_enrollment_id: UUID | None = None,
) -> dict[str, Any] | None:
    """Assembles the full outcome timeline for one user. Returns None only
    when an explicit training_enrollment_id was given but isn't owned by
    this user — callers should treat that as a 404. A user with no training
    or employment history at all still gets a valid (mostly empty) timeline,
    never fabricated data."""
    enrollment = _pick_enrollment(db, user_id, training_enrollment_id)
    if enrollment is False:
        return None

    program = outcome_service.get_training_program(db, enrollment.training_program_id) if enrollment else None
    training_skills = outcome_service.training_program_skill_names(db, program) if program else []

    outcomes = outcome_service.list_employment_outcomes(db, user_id)
    outcome = None
    if enrollment:
        outcome = next((o for o in outcomes if o.training_enrollment_id == enrollment.id), None)
    if outcome is None and outcomes:
        outcome = outcomes[0]

    check_ins: list[OutcomeCheckIn] = []
    if outcome:
        check_ins = sorted(
            outcome_service.list_check_ins(db, user_id, employment_outcome_id=outcome.id),
            key=lambda c: c.check_in_date,
        )

    training_block = None
    if enrollment:
        training_block = {
            "training_program_id": str(enrollment.training_program_id),
            "training_program_name": program.name if program else None,
            "enrollment_status": enrollment.status,
            "enrollment_date": enrollment.enrollment_date,
            "completion_date": enrollment.completion_date,
            "certificate_status": enrollment.certificate_status,
        }

    placement_block = None
    employment_block = None
    milestones: dict[str, Any] = {f"{m}_month": None for m in MILESTONE_MONTHS}
    retention: dict[str, str] = {f"{m}_month": "not_applicable" for m in MILESTONE_MONTHS}
    salary_progression: dict[str, Any] = {
        "initial": None, "at_3_months": None, "at_6_months": None, "at_12_months": None, "changes": [],
    }
    relevance_over_time: list[dict[str, Any]] = []

    if outcome:
        placement_block = {
            "employment_outcome_id": str(outcome.id),
            "employment_status": outcome.employment_status,
            "source_opportunity_id": outcome.source_opportunity_id,
            "source_opportunity_title": outcome.source_opportunity_title,
            "verified": outcome.verified,
        }
        employment_block = {
            "company_name": outcome.company_name,
            "job_title": outcome.job_title,
            "employment_type": outcome.employment_type,
            "employment_start_date": outcome.employment_start_date,
            "employment_end_date": outcome.employment_end_date,
            "is_remote": outcome.is_remote,
        }

        student_skill_map = get_user_skill_map(db, user_id)

        if outcome.job_title and training_skills:
            placement_relevance = calculate_training_relevance(
                db, training_skills, student_skill_map, employment_job_title=outcome.job_title,
            )
            relevance_over_time.append({
                "as_of_date": outcome.employment_start_date,
                "months_since_employment": 0,
                "job_title": outcome.job_title,
                **placement_relevance,
            })

        if outcome.employment_start_date:
            today = date.today()
            salary_key_by_month = {3: "at_3_months", 6: "at_6_months", 12: "at_12_months"}

            for months in MILESTONE_MONTHS:
                key = f"{months}_month"
                milestone_date = _add_months(outcome.employment_start_date, months)
                reached = today >= milestone_date
                result = _retention_at_milestone(outcome, check_ins, milestone_date, reached)
                candidate: OutcomeCheckIn | None = result["check_in"]

                retention[key] = result["status"]
                milestones[key] = {
                    "milestone_date": milestone_date,
                    "reached": reached,
                    "retention": result["status"],
                    "employment_status": candidate.employment_status if candidate else None,
                    "check_in_date": candidate.check_in_date if candidate else None,
                }
                salary_progression[salary_key_by_month[months]] = (
                    _salary_snapshot(candidate.salary, candidate.salary_currency, candidate.salary_period, candidate.check_in_date)
                    if candidate else None
                )

            salary_progression["initial"] = _salary_snapshot(
                outcome.salary, outcome.salary_currency, outcome.salary_period, outcome.employment_start_date,
            )

            # A milestone with no dedicated check-in falls back to the nearest
            # available one (see _find_check_in_for_milestone), which can be
            # the same underlying record an earlier milestone already used.
            # Collapse those consecutive duplicates so "no new data yet"
            # never shows up as a fake zero-change entry.
            snapshots = []
            for candidate_snapshot in (
                salary_progression["initial"],
                salary_progression["at_3_months"],
                salary_progression["at_6_months"],
                salary_progression["at_12_months"],
            ):
                if candidate_snapshot is None:
                    continue
                if snapshots and snapshots[-1]["date"] == candidate_snapshot["date"]:
                    continue
                snapshots.append(candidate_snapshot)

            for prev_snapshot, next_snapshot in zip(snapshots, snapshots[1:]):
                change = _compute_salary_change(prev_snapshot, next_snapshot)
                if change:
                    salary_progression["changes"].append(change)

        for check_in in check_ins:
            if check_in.job_title and training_skills:
                rel = calculate_training_relevance(
                    db, training_skills, student_skill_map, employment_job_title=check_in.job_title,
                )
                relevance_over_time.append({
                    "as_of_date": check_in.check_in_date,
                    "months_since_employment": check_in.months_since_employment,
                    "job_title": check_in.job_title,
                    **rel,
                })

    return {
        "training": training_block,
        "placement": placement_block,
        "employment": employment_block,
        "check_ins": [_check_in_summary(c) for c in check_ins],
        "milestones": milestones,
        "retention": retention,
        "salary_progression": salary_progression,
        "training_relevance_over_time": relevance_over_time,
    }

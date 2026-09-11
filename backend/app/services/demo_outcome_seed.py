"""Admin-triggered synthetic demo outcome data (Phase 6, section 6).

For hackathon demonstration only — this is never real Maharashtra Government
data. Every seeded trainee reuses the existing `User.is_demo` flag (the same
one the student demo account already uses) and an unmistakably synthetic
email domain, and all three training providers are named with a "(Demo)" suffix
so they're visually distinct in the provider comparison table. The admin
dashboard surfaces `demo_trainee_count` on every cohort metric (see
app.services.admin_analytics) so demo data is always visible and
attributable, never silently blended in as if it were real.
"""
import random
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.skill import Skill, UserSkill
from app.services import outcome_service
from app.services.outcome_timeline import _add_months
from app.schemas.outcome import (
    TrainingProgramCreate,
    TrainingEnrollmentCreate,
    TrainingEnrollmentUpdate,
    EmploymentOutcomeCreate,
    OutcomeCheckInCreate,
)
from app.utils.auth import get_password_hash

DEMO_EMAIL_DOMAIN = "demo.nextpath.local"
DEMO_PROVIDER_A = "Acme Skilling (Demo)"
DEMO_PROVIDER_B = "Bright Future Institute (Demo)"
DEMO_PROVIDER_C = "Skill Bridge Foundation (Demo)"
DEMO_SKILLS = ["JavaScript", "React", "Node.js", "SQL", "Git", "Python", "Data Analysis"]


def demo_outcome_data_exists(db: Session) -> bool:
    return db.query(User).filter(User.email.like(f"%@{DEMO_EMAIL_DOMAIN}")).first() is not None


def seed_demo_outcome_data(db: Session) -> dict[str, Any]:
    """Idempotent: returns immediately if demo outcome data already exists."""
    if demo_outcome_data_exists(db):
        return {"message": "Demo outcome dataset already loaded", "created": False, "trainees_created": 0}

    for name in DEMO_SKILLS:
        if not db.query(Skill).filter(Skill.name == name).first():
            db.add(Skill(name=name, category="Programming"))
    db.commit()

    program_a = outcome_service.create_training_program(db, TrainingProgramCreate(
        name="Full Stack Web Development", provider_name=DEMO_PROVIDER_A,
        career_domain="Software Development", skill_names=["JavaScript", "React", "Node.js", "SQL", "Git"],
        status="completed",
    ))
    program_b = outcome_service.create_training_program(db, TrainingProgramCreate(
        name="Data Analytics Bootcamp", provider_name=DEMO_PROVIDER_B,
        career_domain="Data Science", skill_names=["Python", "SQL", "Data Analysis"],
        status="completed",
    ))
    program_c = outcome_service.create_training_program(db, TrainingProgramCreate(
        name="Retail & Customer Service Skills", provider_name=DEMO_PROVIDER_C,
        career_domain="Customer Service", skill_names=["Python", "SQL"],
        status="completed",
    ))

    random.seed(42)
    created_count = 0
    created_users: list = []

    def make_trainee(i, program, tag, placed, employed, salary=None, retained=None, months_ago=8, skills=None):
        nonlocal created_count
        user = User(
            email=f"{tag}{i}@{DEMO_EMAIL_DOMAIN}",
            name=f"Demo Trainee {tag.upper()}{i}",
            password_hash=get_password_hash("demo-outcome-seed"),
            is_demo=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        created_count += 1
        created_users.append(user)

        enrollment = outcome_service.create_enrollment(db, user.id, TrainingEnrollmentCreate(
            training_program_id=program.id,
            enrollment_date=_add_months(date.today(), -(months_ago + 4)),
        ))
        outcome_service.update_enrollment(db, enrollment, TrainingEnrollmentUpdate(status="completed"))

        for skill_name, proficiency in (skills or {}).items():
            skill = db.query(Skill).filter(Skill.name == skill_name).first()
            if skill:
                db.add(UserSkill(user_id=user.id, skill_id=skill.id, proficiency=proficiency))
        db.commit()

        if not placed:
            return

        status = "employed" if employed else "self_employed"
        start = _add_months(date.today(), -months_ago)
        outcome = outcome_service.create_employment_outcome(db, user.id, EmploymentOutcomeCreate(
            employment_status=status,
            employment_type="full_time" if employed else "freelance",
            job_title="Frontend Developer" if program is program_a else "Data Analyst",
            company_name=f"Demo Corp {tag.upper()}{i}",
            location="Bengaluru",
            employment_start_date=start,
            salary=salary, salary_currency="INR", salary_period="annual",
        ))
        outcome.training_enrollment_id = enrollment.id
        db.commit()
        db.refresh(outcome)

        if employed and retained is not None and months_ago >= 6:
            outcome_service.create_check_in(db, outcome, OutcomeCheckInCreate(
                employment_outcome_id=outcome.id,
                check_in_date=_add_months(start, 6),
                employment_status="employed" if retained else "looking_for_work",
                still_employed=retained,
                salary=(salary + 30000) if (retained and salary) else None,
            ))

    # Program A: 8 trainees -> 6 placed (5 employed + 1 self-employed), 4/5 retained at 6mo.
    # Deliberately leaves React underrepresented so the curriculum-recommendation
    # threshold (see admin_analytics.get_curriculum_recommendations) has something
    # real to detect in the demo dataset.
    for i in range(6):
        make_trainee(
            i, program_a, "a", placed=True, employed=(i < 5),
            salary=300000 if i < 5 else None, retained=(i < 4) if i < 5 else None,
            skills={"JavaScript": 4, "React": 2 if i % 2 else 4, "Git": 4},
        )
    for i in range(6, 8):
        make_trainee(i, program_a, "a", placed=False, employed=False, skills={"JavaScript": 2})

    # Program B: 3 trainees only -> deliberately below MIN_COHORT_SIZE, so the
    # dashboard's small-sample suppression is visible in the demo too.
    for i in range(3):
        make_trainee(
            i, program_b, "b", placed=(i < 2), employed=True,
            salary=280000, retained=True, skills={"Python": 4, "SQL": 4},
        )

    def make_non_contact_trainee(i, program, tag, status, outreach_result=None):
        """A trainee whose outcome is unreachable/declined_to_respond, with an
        optional check-in recording whether contact was actually attempted."""
        nonlocal created_count
        user = User(
            email=f"{tag}{i}@{DEMO_EMAIL_DOMAIN}",
            name=f"Demo Trainee {tag.upper()}{i}",
            password_hash=get_password_hash("demo-outcome-seed"),
            is_demo=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        created_count += 1
        created_users.append(user)

        enrollment = outcome_service.create_enrollment(db, user.id, TrainingEnrollmentCreate(
            training_program_id=program.id,
            enrollment_date=_add_months(date.today(), -12),
        ))
        outcome_service.update_enrollment(db, enrollment, TrainingEnrollmentUpdate(status="completed"))
        db.commit()

        outcome = outcome_service.create_employment_outcome(db, user.id, EmploymentOutcomeCreate(
            employment_status=status,
        ))
        outcome.training_enrollment_id = enrollment.id
        db.commit()
        db.refresh(outcome)

        if outreach_result is not None:
            outcome_service.create_check_in(db, outcome, OutcomeCheckInCreate(
                employment_outcome_id=outcome.id,
                employment_status=status,
                outreach_result=outreach_result,
            ))

    # Program A: non-contact outcomes, kept on the large program so its cohort
    # stays above MIN_COHORT_SIZE. The two unreachable check-ins contrast
    # "we never tried" (not_attempted) with "we tried and got nothing"
    # (attempted_no_response).
    make_non_contact_trainee(0, program_a, "u", "unreachable", outreach_result="not_attempted")
    make_non_contact_trainee(1, program_a, "u", "unreachable", outreach_result="attempted_no_response")
    make_non_contact_trainee(2, program_a, "u", "unreachable")
    make_non_contact_trainee(0, program_a, "d", "declined_to_respond")
    make_non_contact_trainee(1, program_a, "d", "declined_to_respond")

    # Program C: deliberately weak follow-up, so the provider comparison's
    # high_unreachable_flag has something real to fire on in the demo.
    # 6 trainees, 5 unreachable (83.3%) vs Acme's ~23%: with two
    # sufficient-sample providers the flag needs the high provider above
    # 3x the other's rate (rate > 1.5x the 2-provider average), so 4-of-6
    # (66.7%) would sit just under the threshold while 5-of-6 clears it
    # unambiguously. The single employed trainee keeps the cohort realistic.
    for i in range(5):
        make_non_contact_trainee(i, program_c, "c", "unreachable")
    make_trainee(
        0, program_c, "ce", placed=True, employed=True,
        salary=250000, retained=True, skills={"Python": 3, "SQL": 3},
    )

    # Vary consent across the whole demo set so consent_coverage_pct reads as
    # a realistic mid-range share: most consented, a few with no record, one revoked.
    for idx, user in enumerate(created_users):
        if idx % 3 == 2 and idx != 5:
            continue  # no consent record at all
        outcome_service.set_consent(db, user.id, True)
        if idx == 5:
            outcome_service.set_consent(db, user.id, False)  # revoked

    return {"message": "Demo outcome dataset created", "created": True, "trainees_created": created_count}

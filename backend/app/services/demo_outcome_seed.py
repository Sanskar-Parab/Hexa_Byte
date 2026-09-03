"""Admin-triggered synthetic demo outcome data (Phase 6, section 6).

For hackathon demonstration only — this is never real Maharashtra Government
data. Every seeded trainee reuses the existing `User.is_demo` flag (the same
one the student demo account already uses) and an unmistakably synthetic
email domain, and both training providers are named with a "(Demo)" suffix
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

    random.seed(42)
    created_count = 0

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

    return {"message": "Demo outcome dataset created", "created": True, "trainees_created": created_count}

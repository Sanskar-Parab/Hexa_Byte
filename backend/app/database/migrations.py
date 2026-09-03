from sqlalchemy import text
from app.database.config import Base, engine
from app.models.user import User
from app.models.profile import Profile
from app.models.skill import Skill, UserSkill
from app.models.skill_assessment import SkillAssessmentSession
from app.models.skill_evidence import SkillEvidence
from app.models.interest import Interest, UserInterest
from app.models.career import Career, CareerRecommendation
from app.models.assessment import AssessmentQuestion, UserAssessment
from app.models.roadmap import Roadmap, RoadmapPhase
from app.models.project import Project, RecommendedProject, AIGeneratedProject
from app.models.progress import UserProgress
from app.models.resume import Resume
from app.models.job_analysis import JobAnalysis
from app.models.outcome import (
    TrainingProgram,
    TrainingProgramSkill,
    TrainingEnrollment,
    EmploymentOutcome,
    OutcomeCheckIn,
    OutcomeConsent,
)


def _column_exists(conn, table_name, column_name):
    result = conn.execute(text(f"PRAGMA table_info({table_name})"))
    return any(row[1] == column_name for row in result)


def run_migrations():
    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        if not _column_exists(conn, "user_skills", "level_name"):
            conn.execute(text("ALTER TABLE user_skills ADD COLUMN level_name VARCHAR"))
        if not _column_exists(conn, "user_skills", "confidence"):
            conn.execute(text("ALTER TABLE user_skills ADD COLUMN confidence VARCHAR DEFAULT 'LOW'"))
        if not _column_exists(conn, "user_skills", "updated_at"):
            conn.execute(text("ALTER TABLE user_skills ADD COLUMN updated_at DATETIME"))
        if not _column_exists(conn, "roadmaps", "updated_at"):
            conn.execute(text("ALTER TABLE roadmaps ADD COLUMN updated_at DATETIME"))
        if not _column_exists(conn, "roadmap_phases", "adaptation_mode"):
            conn.execute(text("ALTER TABLE roadmap_phases ADD COLUMN adaptation_mode VARCHAR DEFAULT 'full'"))
        if not _column_exists(conn, "roadmap_phases", "created_at"):
            conn.execute(text("ALTER TABLE roadmap_phases ADD COLUMN created_at DATETIME"))
        if not _column_exists(conn, "roadmap_phases", "updated_at"):
            conn.execute(text("ALTER TABLE roadmap_phases ADD COLUMN updated_at DATETIME"))
        if not _column_exists(conn, "users", "preferred_difficulty"):
            conn.execute(text("ALTER TABLE users ADD COLUMN preferred_difficulty VARCHAR DEFAULT 'AUTO'"))
        if not _column_exists(conn, "employment_outcomes", "source_opportunity_id"):
            conn.execute(text("ALTER TABLE employment_outcomes ADD COLUMN source_opportunity_id VARCHAR"))
        if not _column_exists(conn, "employment_outcomes", "source_opportunity_title"):
            conn.execute(text("ALTER TABLE employment_outcomes ADD COLUMN source_opportunity_title VARCHAR"))
        if not _column_exists(conn, "users", "is_admin"):
            conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))

    # Create new tables for Phase 6
    Resume.__table__.create(bind=engine, checkfirst=True)
    JobAnalysis.__table__.create(bind=engine, checkfirst=True)

    # Create new tables for employment outcome tracking (Phase 1)
    TrainingProgram.__table__.create(bind=engine, checkfirst=True)
    TrainingProgramSkill.__table__.create(bind=engine, checkfirst=True)
    TrainingEnrollment.__table__.create(bind=engine, checkfirst=True)
    EmploymentOutcome.__table__.create(bind=engine, checkfirst=True)
    OutcomeCheckIn.__table__.create(bind=engine, checkfirst=True)
    OutcomeConsent.__table__.create(bind=engine, checkfirst=True)

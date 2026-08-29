from pathlib import Path
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env file from backend directory
backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(backend_dir / ".env")

from app.database.config import engine, Base
from app.database.migrations import run_migrations
from app.api import auth, profile, skills, interests, assessment, careers, skill_gap, roadmap, projects, progress, coach, demo, skill_assessment, evidence, next_best_action, resume, job_analysis, opportunities

logger = logging.getLogger(__name__)

app = FastAPI(
    title="PathPilot AI",
    description="AI-powered career guidance system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(skills.router)
app.include_router(interests.router)
app.include_router(assessment.router)
app.include_router(careers.router)
app.include_router(skill_gap.router)
app.include_router(roadmap.router)
app.include_router(projects.router)
app.include_router(progress.router)
app.include_router(coach.router)
app.include_router(demo.router)
app.include_router(skill_assessment.router)
app.include_router(evidence.router)
app.include_router(next_best_action.router)
app.include_router(resume.router)
app.include_router(job_analysis.router)
app.include_router(opportunities.router)


@app.on_event("startup")
def startup():
    run_migrations()
    from app.database.seed import seed_if_empty
    seed_if_empty()

    # Fix existing manual evidence confidence (one-time migration)
    from app.database.config import SessionLocal
    from app.services.evidence_service import fix_existing_manual_evidence
    db = SessionLocal()
    try:
        updated = fix_existing_manual_evidence(db)
        if updated > 0:
            logger.info(f"Startup fix: Updated {updated} manual evidence records with correct confidence")
    except Exception as e:
        logger.warning(f"Startup fix for manual evidence confidence failed: {e}")
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "PathPilot AI"}


@app.get("/")
def root():
    return {"message": "PathPilot AI Backend", "docs": "/docs"}

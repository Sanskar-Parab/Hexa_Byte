import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.models.skill import Skill
from app.schemas.resume import (
    ResumeUploadResponse,
    ResumeDetailResponse,
    ResumeExtraction,
    ResumeSkillItem,
)
from app.services.resume_service import (
    extract_text_from_pdf,
    parse_resume_text,
    extract_skills_from_text,
    save_resume_and_create_evidence,
    get_resumes_for_user,
    get_resume_by_id,
    delete_resume,
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/resume", tags=["resume"])

ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a PDF resume. Extract skills, create evidence with MEDIUM confidence.

    Resume mentions are EVIDENCE, not proof of expert proficiency.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Only PDF files are accepted.",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    # Extract text from PDF
    try:
        raw_text = extract_text_from_pdf(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="No text could be extracted from the PDF.")

    # Parse resume sections
    extraction = parse_resume_text(raw_text)

    # Match skills against database
    all_skills = db.query(Skill).all()
    matched_skills = extract_skills_from_text(raw_text, all_skills)

    # Save resume and create evidence
    resume = save_resume_and_create_evidence(
        db=db,
        user_id=current_user.id,
        filename=file.filename,
        raw_text=raw_text,
        extraction=extraction,
        matched_skills=matched_skills,
    )

    # Trigger adaptive event on resume analysis
    try:
        from app.services.adaptive_events import on_resume_analyzed
        on_resume_analyzed(
            db=db,
            user_id=current_user.id,
            resume_id=resume.id,
            matched_skills_count=len(matched_skills),
        )
        db.commit()
    except Exception:
        db.rollback()

    return ResumeUploadResponse(
        resume_id=str(resume.id),
        filename=file.filename,
        extraction=ResumeExtraction(
            skills=extraction.get("skills", []),
            projects=extraction.get("projects", []),
            experience=extraction.get("experience", []),
            education=extraction.get("education", []),
            certifications=extraction.get("certifications", []),
            technologies=extraction.get("technologies", []),
            tools=extraction.get("tools", []),
        ),
        matched_skills=[
            ResumeSkillItem(
                skill_name=m["skill_name"],
                skill_id=m.get("skill_id"),
                context=m.get("context", ""),
            )
            for m in matched_skills
        ],
        evidence_created=len(matched_skills),
        message=f"Resume processed. {len(matched_skills)} skills detected and linked as evidence.",
    )


@router.get("", response_model=list[ResumeDetailResponse])
def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all uploaded resumes."""
    resumes = get_resumes_for_user(db, current_user.id)
    results = []
    for r in resumes:
        results.append(_resume_to_detail(r))
    return results


@router.get("/{resume_id}", response_model=ResumeDetailResponse)
def get_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific resume."""
    resume = get_resume_by_id(db, current_user.id, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return _resume_to_detail(resume)


@router.delete("/{resume_id}")
def remove_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a resume."""
    success = delete_resume(db, current_user.id, resume_id)
    if not success:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {"message": "Resume deleted"}


def _resume_to_detail(resume) -> ResumeDetailResponse:
    """Convert a Resume model to ResumeDetailResponse."""
    matched = json.loads(resume.matched_skills) if resume.matched_skills else []
    return ResumeDetailResponse(
        id=str(resume.id),
        filename=resume.filename,
        extraction=ResumeExtraction(
            skills=json.loads(resume.skills) if resume.skills else [],
            projects=json.loads(resume.projects) if resume.projects else [],
            experience=json.loads(resume.experience) if resume.experience else [],
            education=json.loads(resume.education) if resume.education else [],
            certifications=json.loads(resume.certifications) if resume.certifications else [],
            technologies=json.loads(resume.technologies) if resume.technologies else [],
            tools=json.loads(resume.tools) if resume.tools else [],
        ),
        matched_skills=[
            ResumeSkillItem(
                skill_name=m.get("skill_name", ""),
                skill_id=m.get("skill_id"),
                context=m.get("context", ""),
            )
            for m in matched
        ],
        extracted_at=resume.extracted_at,
        created_at=resume.created_at,
    )

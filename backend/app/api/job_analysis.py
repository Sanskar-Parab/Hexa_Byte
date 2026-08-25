import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.schemas.job_analysis import (
    JobAnalysisRequest,
    JobAnalysisResponse,
    JobMatchResponse,
    JobAnalysisDetailResponse,
    JobSkillMatch,
)
from app.services.job_analysis_service import (
    parse_job_description,
    match_job_to_user,
    create_job_evidence,
    save_job_analysis,
    get_job_analyses_for_user,
    get_job_analysis_by_id,
    delete_job_analysis,
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/job", tags=["job-analysis"])


@router.post("/analyze", response_model=JobMatchResponse)
def analyze_job(
    request: JobAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze a job description and match against user profile.

    Creates evidence for skills the user HAS that match job requirements.
    Does NOT create evidence for skills the user doesn't have.
    """
    if not request.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty")

    # Parse job description
    job_data = parse_job_description(request.job_description)

    # Match against user
    match_result = match_job_to_user(db, current_user.id, job_data)

    # Create evidence only for skills the user has
    all_matched = (
        match_result["strong_skills"]
        + match_result["developing_skills"]
    )
    evidence_count = create_job_evidence(db, current_user.id, job_data, all_matched)

    # Save analysis
    analysis = save_job_analysis(
        db=db,
        user_id=current_user.id,
        job_data=job_data,
        raw_text=request.job_description,
        match_result=match_result,
    )

    # Trigger adaptive event on job analysis
    try:
        from app.services.adaptive_events import on_job_analyzed
        on_job_analyzed(
            db=db,
            user_id=current_user.id,
            job_id=analysis.id,
            evidence_created=evidence_count,
        )
        db.commit()
    except Exception:
        db.rollback()

    return JobMatchResponse(
        analysis_id=str(analysis.id),
        job_title=job_data.get("job_title", "Unknown"),
        alignment_percentage=match_result["alignment_percentage"],
        strong_skills=[JobSkillMatch(**s) for s in match_result["strong_skills"]],
        developing_skills=[JobSkillMatch(**s) for s in match_result["developing_skills"]],
        missing_skills=[JobSkillMatch(**s) for s in match_result["missing_skills"]],
        not_demonstrated=[JobSkillMatch(**s) for s in match_result["not_demonstrated"]],
        top_gap=match_result.get("top_gap"),
        next_action=match_result.get("next_action"),
        evidence_created=evidence_count,
        required_skills_count=match_result["required_skills_count"],
        matched_count=match_result["matched_count"],
    )


@router.get("/history", response_model=list[JobAnalysisDetailResponse])
def list_job_analyses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all past job analyses."""
    analyses = get_job_analyses_for_user(db, current_user.id)
    return [_analysis_to_detail(a) for a in analyses]


@router.get("/{analysis_id}", response_model=JobAnalysisDetailResponse)
def get_job_analysis(
    analysis_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific job analysis."""
    analysis = get_job_analysis_by_id(db, current_user.id, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Job analysis not found")
    return _analysis_to_detail(analysis)


@router.delete("/{analysis_id}")
def remove_job_analysis(
    analysis_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a job analysis."""
    success = delete_job_analysis(db, current_user.id, analysis_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job analysis not found")
    return {"message": "Job analysis deleted"}


def _analysis_to_detail(analysis) -> JobAnalysisDetailResponse:
    """Convert a JobAnalysis model to JobAnalysisDetailResponse."""
    match_result = None
    if analysis.match_result:
        try:
            mr = json.loads(analysis.match_result)
            match_result = JobMatchResponse(
                analysis_id=str(analysis.id),
                job_title=analysis.job_title,
                alignment_percentage=mr.get("alignment_percentage", 0),
                strong_skills=[JobSkillMatch(**s) for s in mr.get("strong_skills", [])],
                developing_skills=[JobSkillMatch(**s) for s in mr.get("developing_skills", [])],
                missing_skills=[JobSkillMatch(**s) for s in mr.get("missing_skills", [])],
                not_demonstrated=[JobSkillMatch(**s) for s in mr.get("not_demonstrated", [])],
                top_gap=mr.get("top_gap"),
                next_action=mr.get("next_action"),
                evidence_created=0,
                required_skills_count=mr.get("required_skills_count", 0),
                matched_count=mr.get("matched_count", 0),
            )
        except (json.JSONDecodeError, TypeError):
            pass

    return JobAnalysisDetailResponse(
        id=str(analysis.id),
        job_title=analysis.job_title,
        raw_text=analysis.raw_text,
        required_skills=json.loads(analysis.required_skills) if analysis.required_skills else [],
        preferred_skills=json.loads(analysis.preferred_skills) if analysis.preferred_skills else [],
        experience_required=analysis.experience_required,
        education_required=analysis.education_required,
        responsibilities=json.loads(analysis.responsibilities) if analysis.responsibilities else [],
        technologies=json.loads(analysis.technologies) if analysis.technologies else [],
        match_result=match_result,
        created_at=analysis.created_at,
    )

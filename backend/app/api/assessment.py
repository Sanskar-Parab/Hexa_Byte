from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.models.assessment import AssessmentQuestion, UserAssessment
from app.schemas.assessment import AssessmentQuestionResponse, AssessmentSubmit, AssessmentResult
from app.services.assessment_service import score_assessment
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/assessment", tags=["assessment"])


@router.get("/questions", response_model=list[AssessmentQuestionResponse])
def get_questions(db: Session = Depends(get_db)):
    questions = db.query(AssessmentQuestion).all()
    return [
        AssessmentQuestionResponse(
            id=q.id,
            question_text=q.question_text,
            category=q.category,
            options=q.options,
        )
        for q in questions
    ]


@router.post("/submit", response_model=AssessmentResult)
def submit_assessment(
    submission: AssessmentSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = score_assessment(db, current_user.id, submission.answers)

    assessment = UserAssessment(
        user_id=current_user.id,
        answers=submission.answers,
        scores=result["scores"],
    )
    db.add(assessment)
    db.commit()

    return AssessmentResult(
        scores=result["scores"],
        interpretation=result["interpretation"],
        top_interests=result["top_interests"],
    )


@router.get("/result", response_model=AssessmentResult)
def get_latest_result(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assessment = db.query(UserAssessment).filter(
        UserAssessment.user_id == current_user.id
    ).order_by(UserAssessment.created_at.desc()).first()

    if not assessment:
        raise HTTPException(status_code=404, detail="No assessment found")

    return AssessmentResult(
        scores=assessment.scores,
        interpretation={},
        top_interests=[],
    )

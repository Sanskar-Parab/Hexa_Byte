from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.models.trainee_identity import MasterTrainee, TraineeProgramRecord, IdentityReview, mask_phone
from app.schemas.trainee_identity import (
    TraineeProgramCreate,
    TraineeMatchPreviewRequest,
    TraineeProgramRecordResponse,
    MasterTraineeResponse,
    MasterTraineeDetailResponse,
    CreateTraineeResponse,
    IdentityReviewResponse,
    ReviewDecisionRequest,
    FieldScores,
    ListMastersResponse,
    ListReviewsResponse,
    MatchResult,
)
from app.services import trainee_identity_service
from app.utils.auth import get_current_admin_user

router = APIRouter(prefix="/api/admin/trainees", tags=["trainee-identity"])
reviews_router = APIRouter(prefix="/api/admin/identity-reviews", tags=["trainee-identity"])


def _master_to_response(m: MasterTrainee, db: Session, enrollment_count: int | None = None) -> MasterTraineeResponse:
    if enrollment_count is None:
        enrollment_count = db.query(TraineeProgramRecord).filter(TraineeProgramRecord.master_trainee_id == m.id).count()
    return MasterTraineeResponse(
        id=m.id,
        master_code=m.master_code,
        primary_name=m.primary_name,
        dob=m.dob,
        phone_numbers=m.get_phone_numbers(),
        masked_phones=m.masked_phones(),
        linked_user_id=m.linked_user_id,
        created_at=m.created_at,
        updated_at=m.updated_at,
        enrollment_count=enrollment_count,
    )

def _record_to_response(r: TraineeProgramRecord) -> TraineeProgramRecordResponse:
    return TraineeProgramRecordResponse(
        id=r.id,
        master_trainee_id=r.master_trainee_id,
        program_name=r.program_name,
        program_trainee_id=r.program_trainee_id,
        trainee_name=r.trainee_name,
        dob=r.dob,
        phone=r.phone,
        masked_phone=mask_phone(r.phone) if r.phone else None,
        created_at=r.created_at,
    )

def _review_to_response(review: IdentityReview, db: Session) -> IdentityReviewResponse:
    field_scores = review.get_field_scores() or {"name": 0, "dob": 0, "phone": 0, "program": 0}
    fs = FieldScores(**field_scores)
    matched_master_resp = None
    enrollments_resp = []
    if review.matched_master_id:
        m = db.query(MasterTrainee).filter(MasterTrainee.id == review.matched_master_id).first()
        if m:
            matched_master_resp = _master_to_response(m, db)
            recs = db.query(TraineeProgramRecord).filter(TraineeProgramRecord.master_trainee_id == m.id).all()
            enrollments_resp = [_record_to_response(r) for r in recs]
    return IdentityReviewResponse(
        id=review.id,
        incoming_name=review.incoming_name,
        incoming_dob=review.incoming_dob,
        incoming_phone=review.incoming_phone,
        masked_phone=mask_phone(review.incoming_phone) if review.incoming_phone else None,
        incoming_program_name=review.incoming_program_name,
        incoming_program_trainee_id=review.incoming_program_trainee_id,
        matched_master_id=review.matched_master_id,
        match_score=review.match_score,
        confidence=review.confidence,
        field_scores=fs,
        status=review.status,
        created_at=review.created_at,
        decided_at=review.decided_at,
        matched_master=matched_master_resp,
        matched_master_enrollments=enrollments_resp,
    )


# ---------------------------------------------------------------------------
# Masters
# ---------------------------------------------------------------------------

@router.get("", response_model=ListMastersResponse)
def list_masters(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    skip = (page - 1) * page_size
    items, total = trainee_identity_service.list_masters(db, skip=skip, limit=page_size, search=search)
    return ListMastersResponse(
        items=[_master_to_response(m, db) for m in items],
        total=total,
        page=page,
        page_size=page_size,
    )

@router.get("/{master_id}", response_model=MasterTraineeDetailResponse)
def get_master(
    master_id: UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    result = trainee_identity_service.get_master_detail(db, master_id)
    if not result:
        raise HTTPException(status_code=404, detail="Master trainee not found")
    master, records, longitudinal = result
    # Build longitudinal summary if linked user exists
    long_summary = None
    if longitudinal:
        # don't expose full outcomes; just counts for MVP longitudinal hint
        long_summary = {
            "linked_user_id": str(master.linked_user_id) if master.linked_user_id else None,
            "enrollment_count": len(longitudinal["enrollments"]) if longitudinal["enrollments"] else 0,
            "outcome_count": len(longitudinal["outcomes"]) if longitudinal["outcomes"] else 0,
        }
    return MasterTraineeDetailResponse(
        master=_master_to_response(master, db, enrollment_count=len(records)),
        enrollments=[_record_to_response(r) for r in records],
        longitudinal=long_summary,
    )

@router.post("/match-preview", response_model=MatchResult)
def match_preview(
    data: TraineeMatchPreviewRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    result = trainee_identity_service.preview_match(
        db,
        name=data.trainee_name,
        dob=data.dob,
        phone=data.phone,
        program_name=data.program_name,
        program_trainee_id=data.program_trainee_id,
    )
    # normalize to MatchResult
    if not result.get("matched"):
        return MatchResult(
            match_score=result["match_score"],
            confidence=result["confidence"],
            field_scores=FieldScores(name=0, dob=0, phone=0, program=0),
            matched=False,
        )
    fs = result["field_scores"]
    return MatchResult(
        match_score=result["match_score"],
        confidence=result["confidence"],
        field_scores=FieldScores(**fs),
        field_weights=result.get("field_weights"),
        matched=True,
        master_id=result.get("master_id"),
        master_code=result.get("master_code"),
        matched_master=result.get("matched_master"),
    )

@router.post("", response_model=CreateTraineeResponse)
def create_trainee(
    data: TraineeProgramCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    try:
        res = trainee_identity_service.add_trainee_program_record(
            db,
            name=data.trainee_name,
            dob=data.dob,
            phone=data.phone,
            program_name=data.program_name,
            program_trainee_id=data.program_trainee_id,
            admin_user_id=_admin.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    action = res["action"]
    fs = res.get("field_scores") or {"name": 0, "dob": 0, "phone": 0, "program": 0}
    # ensure all keys
    for k in ["name", "dob", "phone", "program"]:
        fs.setdefault(k, 0)
    field_scores = FieldScores(**fs)

    master_resp = _master_to_response(res["master"], db) if res.get("master") else None
    record_resp = _record_to_response(res["record"]) if res.get("record") else None
    review_resp = _review_to_response(res["review"], db) if res.get("review") else None

    match_detail = None
    if res.get("match_detail"):
        md = res["match_detail"]
        match_detail = MatchResult(
            match_score=md["match_score"],
            confidence=md["confidence"],
            field_scores=FieldScores(**md["field_scores"]),
            field_weights=md.get("field_weights"),
            matched=True,
            master_id=md.get("master_id"),
            master_code=md.get("master_code"),
        )
    elif action == "new_master" and res.get("match_score") is not None:
        # low case still has match_detail maybe
        pass

    messages = {
        "new_master": f"New master trainee created: {master_resp.master_code if master_resp else ''}",
        "auto_linked": f"Automatically linked to existing master {master_resp.master_code if master_resp else ''} (high confidence {res.get('match_score')}%)",
        "review_required": f"Medium confidence match ({res.get('match_score')}%) — flagged for admin review",
    }

    return CreateTraineeResponse(
        action=action,
        confidence=res.get("confidence", "low"),
        match_score=res.get("match_score", 0),
        field_scores=field_scores,
        master=master_resp,
        record=record_resp,
        review=review_resp,
        match_detail=match_detail,
        message=messages.get(action, ""),
    )


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

@reviews_router.get("", response_model=ListReviewsResponse)
def list_reviews(
    status: str | None = Query(None, description="pending, approved, rejected"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    if status and status not in ("pending", "approved", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid status")
    skip = (page - 1) * page_size
    items, total = trainee_identity_service.list_reviews(db, status=status, skip=skip, limit=page_size)
    return ListReviewsResponse(
        items=[_review_to_response(r, db) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )

@reviews_router.get("/{review_id}", response_model=IdentityReviewResponse)
def get_review(
    review_id: UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    review = db.query(IdentityReview).filter(IdentityReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return _review_to_response(review, db)

@reviews_router.patch("/{review_id}", response_model=dict)
def decide_review(
    review_id: UUID,
    data: ReviewDecisionRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    result, error = trainee_identity_service.decide_review(db, review_id, data.decision, admin_user_id=_admin.id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    review = result["review"]
    master = result["master"]
    record = result["record"]
    return {
        "review": _review_to_response(review, db).model_dump(),
        "master": _master_to_response(master, db).model_dump(),
        "record": _record_to_response(record).model_dump(),
        "message": f"Review {data.decision} — {'linked' if data.decision=='link' else 'created new master'} {master.master_code}",
    }

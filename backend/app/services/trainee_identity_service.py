import json
import uuid
from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.trainee_identity import MasterTrainee, TraineeProgramRecord, IdentityReview, mask_phone
from app.services.identity_matching import find_best_match, HIGH_THRESHOLD, MEDIUM_THRESHOLD, normalize_phone


def _next_master_code(db: Session) -> str:
    count = db.query(MasterTrainee).count()
    # Find max existing code numeric part to avoid collisions if count deleted
    # simple sequential
    next_num = count + 1
    # ensure uniqueness loop
    while True:
        code = f"MT-{next_num:05d}"
        exists = db.query(MasterTrainee).filter(MasterTrainee.master_code == code).first()
        if not exists:
            return code
        next_num += 1


def _check_duplicate_program_id(db: Session, program_name: str, program_trainee_id: str) -> bool:
    existing = db.query(TraineeProgramRecord).filter(
        TraineeProgramRecord.program_name == program_name,
        TraineeProgramRecord.program_trainee_id == program_trainee_id
    ).first()
    return existing is not None


def create_master_trainee(db: Session, name: str, dob: date, phone: Optional[str], linked_user_id=None) -> MasterTrainee:
    master = MasterTrainee(
        master_code=_next_master_code(db),
        primary_name=name,
        dob=dob,
        linked_user_id=linked_user_id,
    )
    if phone:
        master.set_phone_numbers([phone])
    else:
        master.set_phone_numbers([])
    db.add(master)
    db.flush()  # get id
    return master


def create_program_record(db: Session, master_id, program_name: str, program_trainee_id: str, trainee_name: str, dob: date, phone: Optional[str]) -> TraineeProgramRecord:
    rec = TraineeProgramRecord(
        master_trainee_id=master_id,
        program_name=program_name,
        program_trainee_id=program_trainee_id,
        trainee_name=trainee_name,
        dob=dob,
        phone=phone,
    )
    db.add(rec)
    db.flush()
    # update master's phone list
    master = db.query(MasterTrainee).filter(MasterTrainee.id == master_id).first()
    if master and phone:
        master.add_phone(phone)
        master.updated_at = datetime.utcnow()
    return rec


def list_masters(db: Session, skip: int = 0, limit: int = 50, search: Optional[str] = None):
    q = db.query(MasterTrainee).order_by(MasterTrainee.created_at.desc())
    if search:
        like = f"%{search}%"
        q = q.filter(or_(MasterTrainee.primary_name.ilike(like), MasterTrainee.master_code.ilike(like)))
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return items, total


def get_master_detail(db: Session, master_id):
    master = db.query(MasterTrainee).filter(MasterTrainee.id == master_id).first()
    if not master:
        return None
    records = db.query(TraineeProgramRecord).filter(TraineeProgramRecord.master_trainee_id == master.id).order_by(TraineeProgramRecord.created_at).all()
    # longitudinal: try to fetch linked user outcomes if exists
    longitudinal = None
    if master.linked_user_id:
        # import here to avoid circular
        from app.models.outcome import TrainingEnrollment, EmploymentOutcome
        enrollments = db.query(TrainingEnrollment).filter(TrainingEnrollment.user_id == master.linked_user_id).all()
        outcomes = db.query(EmploymentOutcome).filter(EmploymentOutcome.user_id == master.linked_user_id).all()
        longitudinal = {"enrollments": enrollments, "outcomes": outcomes}
    return master, records, longitudinal


def preview_match(db: Session, name: str, dob: date, phone: Optional[str], program_name: str, program_trainee_id: str):
    """Run matching without persisting — for UI preview."""
    masters = db.query(MasterTrainee).all()
    incoming = {"name": name, "dob": dob, "phone": phone, "program_name": program_name, "program_trainee_id": program_trainee_id}
    best = find_best_match(incoming, masters, db)
    if not best:
        return {
            "matched": False,
            "match_score": 0,
            "confidence": "low",
            "field_scores": {},
            "message": "No existing trainees to compare against — will create new master.",
        }
    # strip internal
    best_clean = {k: v for k, v in best.items() if not k.startswith("_")}
    best_clean["matched"] = True
    # add matched master preview (masked phones)
    m = best["_master"]
    records = best["_records"]
    best_clean["matched_master"] = {
        "id": str(m.id),
        "master_code": m.master_code,
        "primary_name": m.primary_name,
        "dob": m.dob.isoformat() if m.dob else None,
        "phone_numbers": m.get_phone_numbers(),
        "masked_phones": m.masked_phones(),
        "enrollments": [
            {
                "program_name": r.program_name,
                "program_trainee_id": r.program_trainee_id,
                "trainee_name": r.trainee_name,
                "dob": r.dob.isoformat() if r.dob else None,
                "phone": mask_phone(r.phone) if r.phone else None,
            } for r in records
        ]
    }
    return best_clean


def add_trainee_program_record(db: Session, name: str, dob: date, phone: Optional[str], program_name: str, program_trainee_id: str, admin_user_id=None):
    """Main entry for admin creating a program record.

    Returns dict with action: new_master | auto_linked | review_required
    """
    # Check duplicate program+ID
    if _check_duplicate_program_id(db, program_name, program_trainee_id):
        raise ValueError(f"Program trainee ID '{program_trainee_id}' already exists for program '{program_name}'")

    masters = db.query(MasterTrainee).all()
    incoming = {"name": name, "dob": dob, "phone": phone, "program_name": program_name, "program_trainee_id": program_trainee_id}
    best = find_best_match(incoming, masters, db)

    if not best or not masters:
        # No existing masters -> new
        master = create_master_trainee(db, name, dob, phone)
        rec = create_program_record(db, master.id, program_name, program_trainee_id, name, dob, phone)
        db.commit()
        db.refresh(master)
        db.refresh(rec)
        return {
            "action": "new_master",
            "confidence": "low",
            "match_score": 0,
            "field_scores": {},
            "master": master,
            "record": rec,
            "matched_master": None,
        }

    score = best["match_score"]
    confidence = best["confidence"]
    field_scores = best["field_scores"]
    matched_master = best["_master"]

    if confidence == "high":
        # auto-link
        rec = create_program_record(db, matched_master.id, program_name, program_trainee_id, name, dob, phone)
        db.commit()
        db.refresh(rec)
        db.refresh(matched_master)
        return {
            "action": "auto_linked",
            "confidence": confidence,
            "match_score": score,
            "field_scores": field_scores,
            "master": matched_master,
            "record": rec,
            "matched_master": matched_master,
            "match_detail": {k: v for k, v in best.items() if not k.startswith("_")},
        }
    elif confidence == "medium":
        # create review pending
        review = IdentityReview(
            incoming_name=name,
            incoming_dob=dob,
            incoming_phone=phone,
            incoming_program_name=program_name,
            incoming_program_trainee_id=program_trainee_id,
            matched_master_id=matched_master.id,
            match_score=score,
            confidence=confidence,
            status="pending",
        )
        review.set_field_scores(field_scores)
        db.add(review)
        db.commit()
        db.refresh(review)
        return {
            "action": "review_required",
            "confidence": confidence,
            "match_score": score,
            "field_scores": field_scores,
            "review": review,
            "matched_master": matched_master,
            "match_detail": {k: v for k, v in best.items() if not k.startswith("_")},
        }
    else:
        # low -> new master
        master = create_master_trainee(db, name, dob, phone)
        rec = create_program_record(db, master.id, program_name, program_trainee_id, name, dob, phone)
        db.commit()
        db.refresh(master)
        db.refresh(rec)
        return {
            "action": "new_master",
            "confidence": confidence,
            "match_score": score,
            "field_scores": field_scores,
            "master": master,
            "record": rec,
            "matched_master": matched_master,
            "match_detail": {k: v for k, v in best.items() if not k.startswith("_")},
        }


def decide_review(db: Session, review_id, decision: str, admin_user_id=None):
    """Decision: 'link' or 'reject'."""
    review = db.query(IdentityReview).filter(IdentityReview.id == review_id).first()
    if not review:
        return None, "Review not found"
    if review.status != "pending":
        return None, f"Review already {review.status}"

    if decision == "link":
        # Link incoming as new program record to matched master
        # Check duplicate again (in case another admin created same ID in meantime)
        if _check_duplicate_program_id(db, review.incoming_program_name, review.incoming_program_trainee_id):
            return None, f"Program trainee ID '{review.incoming_program_trainee_id}' already exists for program '{review.incoming_program_name}'"
        matched_master = db.query(MasterTrainee).filter(MasterTrainee.id == review.matched_master_id).first()
        if not matched_master:
            return None, "Matched master not found"
        rec = create_program_record(
            db,
            matched_master.id,
            review.incoming_program_name,
            review.incoming_program_trainee_id,
            review.incoming_name,
            review.incoming_dob,
            review.incoming_phone,
        )
        review.status = "approved"
        review.decided_at = datetime.utcnow()
        review.decided_by = admin_user_id
        db.commit()
        db.refresh(review)
        db.refresh(rec)
        return {"review": review, "master": matched_master, "record": rec}, None

    elif decision == "reject":
        # Create new master for incoming (not same person)
        # First check duplicate? Already checked above but for reject we create new master, duplicate check still applies globally
        if _check_duplicate_program_id(db, review.incoming_program_name, review.incoming_program_trainee_id):
            return None, f"Program trainee ID '{review.incoming_program_trainee_id}' already exists for program '{review.incoming_program_name}'"
        master = create_master_trainee(db, review.incoming_name, review.incoming_dob, review.incoming_phone)
        rec = create_program_record(
            db,
            master.id,
            review.incoming_program_name,
            review.incoming_program_trainee_id,
            review.incoming_name,
            review.incoming_dob,
            review.incoming_phone,
        )
        review.status = "rejected"
        review.decided_at = datetime.utcnow()
        review.decided_by = admin_user_id
        db.commit()
        db.refresh(review)
        db.refresh(master)
        db.refresh(rec)
        return {"review": review, "master": master, "record": rec}, None
    else:
        return None, "Invalid decision, use 'link' or 'reject'"


def list_reviews(db: Session, status: Optional[str] = None, skip: int = 0, limit: int = 50):
    q = db.query(IdentityReview).order_by(IdentityReview.created_at.desc())
    if status:
        q = q.filter(IdentityReview.status == status)
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return items, total

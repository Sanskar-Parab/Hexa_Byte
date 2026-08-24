from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.models.interest import Interest, UserInterest
from app.schemas.interest import InterestResponse
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/interests", tags=["interests"])


@router.get("", response_model=list[InterestResponse])
def list_interests(db: Session = Depends(get_db)):
    return db.query(Interest).all()


@router.get("/user", response_model=list[InterestResponse])
def list_user_interests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_interests = db.query(UserInterest).filter(UserInterest.user_id == current_user.id).all()
    all_interests = {i.id: i for i in db.query(Interest).all()}
    return [all_interests[ui.interest_id] for ui in user_interests if ui.interest_id in all_interests]


@router.post("/{interest_id}")
def add_interest(
    interest_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    interest = db.query(Interest).filter(Interest.id == interest_id).first()
    if not interest:
        raise HTTPException(status_code=404, detail="Interest not found")

    existing = db.query(UserInterest).filter(
        UserInterest.user_id == current_user.id,
        UserInterest.interest_id == interest_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Interest already added")

    user_interest = UserInterest(user_id=current_user.id, interest_id=interest_id)
    db.add(user_interest)
    db.commit()
    return {"message": "Interest added"}


@router.delete("/{interest_id}")
def remove_interest(
    interest_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_interest = db.query(UserInterest).filter(
        UserInterest.user_id == current_user.id,
        UserInterest.interest_id == interest_id,
    ).first()
    if not user_interest:
        raise HTTPException(status_code=404, detail="Interest not found")

    db.delete(user_interest)
    db.commit()
    return {"message": "Interest removed"}

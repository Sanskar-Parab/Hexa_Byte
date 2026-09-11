import uuid
import json
from datetime import datetime, date
from sqlalchemy import Column, String, Text, Date, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from app.models.types import GUID
from app.database.config import Base

# User is referenced as string "User" in relationships; ensure it is
# imported elsewhere (migrations/main) before first DB query.


class MasterTrainee(Base):
    """Persistent Master Trainee identity — the real-world person.

    One MasterTrainee may own multiple ProgramEnrollments (one per
    government program, each with its own program-specific trainee ID).
    Optionally linked to an existing User account via linked_user_id.
    """
    __tablename__ = "master_trainees"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    master_code = Column(String, unique=True, nullable=False, index=True)  # MT-00001
    primary_name = Column(String, nullable=False)
    dob = Column(Date, nullable=False)
    # JSON list of phone strings observed for this trainee
    phone_numbers_json = Column(Text, nullable=True)  # json list
    linked_user_id = Column(GUID(), ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    enrollments = relationship("TraineeProgramRecord", back_populates="master", cascade="all, delete-orphan")
    linked_user = relationship("User", foreign_keys=[linked_user_id], viewonly=True)

    def get_phone_numbers(self) -> list[str]:
        if not self.phone_numbers_json:
            return []
        try:
            return json.loads(self.phone_numbers_json)
        except Exception:
            return []

    def set_phone_numbers(self, phones: list[str]):
        self.phone_numbers_json = json.dumps(phones)

    def add_phone(self, phone: str):
        phones = self.get_phone_numbers()
        normalized = _normalize_phone_digits(phone)
        # store original but dedupe on normalized
        existing_normalized = {_normalize_phone_digits(p) for p in phones}
        if normalized and normalized not in existing_normalized:
            phones.append(phone)
            self.set_phone_numbers(phones)

    def masked_phones(self) -> list[str]:
        return [mask_phone(p) for p in self.get_phone_numbers()]


class TraineeProgramRecord(Base):
    """A program-specific trainee record — retains its original program trainee ID.

    Each record belongs to exactly one MasterTrainee.
    """
    __tablename__ = "trainee_program_records"
    __table_args__ = (
        # prevent duplicate program-specific IDs within same program
        # enforced at app layer + DB unique if supported
        {},
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    master_trainee_id = Column(GUID(), ForeignKey("master_trainees.id"), nullable=False, index=True)
    program_name = Column(String, nullable=False, index=True)  # e.g. PMKVY
    program_trainee_id = Column(String, nullable=False, index=True)  # e.g. PMK-10231
    trainee_name = Column(String, nullable=False)
    dob = Column(Date, nullable=False)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    master = relationship("MasterTrainee", back_populates="enrollments")


class IdentityReview(Base):
    """Pending medium-confidence matches requiring admin decision."""
    __tablename__ = "identity_reviews"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    incoming_name = Column(String, nullable=False)
    incoming_dob = Column(Date, nullable=False)
    incoming_phone = Column(String, nullable=True)
    incoming_program_name = Column(String, nullable=False)
    incoming_program_trainee_id = Column(String, nullable=False)

    matched_master_id = Column(GUID(), ForeignKey("master_trainees.id"), nullable=True, index=True)
    match_score = Column(Float, nullable=False)
    confidence = Column(String, nullable=False)  # high, medium, low
    field_scores_json = Column(Text, nullable=True)  # JSON
    status = Column(String, nullable=False, default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(GUID(), ForeignKey("users.id"), nullable=True)

    matched_master = relationship("MasterTrainee")

    def get_field_scores(self):
        if not self.field_scores_json:
            return {}
        try:
            return json.loads(self.field_scores_json)
        except Exception:
            return {}

    def set_field_scores(self, scores: dict):
        self.field_scores_json = json.dumps(scores)


def _normalize_phone_digits(phone: str) -> str:
    if not phone:
        return ""
    digits = "".join(c for c in phone if c.isdigit())
    # keep last 10 digits for Indian numbers (strip +91 etc)
    if len(digits) > 10:
        digits = digits[-10:]
    return digits


def mask_phone(phone: str) -> str:
    """Mask phone for privacy: XXXXXX + last 4 digits."""
    if not phone:
        return ""
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) <= 4:
        return "XXXXXX" + digits
    # preserve last 4 digits, mask rest
    last4 = digits[-4:]
    # show masked form with X's
    masked = "XXXXXX" + last4
    # Alternative: "XXXXXX780" style per spec example
    return masked

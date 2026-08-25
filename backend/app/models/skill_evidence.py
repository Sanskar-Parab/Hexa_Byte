import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Text, ForeignKey, DateTime
from app.models.types import GUID
from sqlalchemy.orm import relationship
from app.database.config import Base


class SkillEvidence(Base):
    __tablename__ = "skill_evidence"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    skill_id = Column(GUID(), ForeignKey("skills.id"), nullable=False, index=True)
    source_type = Column(String, nullable=False)  # assessment, project, resume, job, manual, practical
    source_id = Column(GUID(), nullable=True)  # references source (e.g. skill_assessment_sessions.id)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    score = Column(Float, nullable=True)  # percentage score if applicable
    confidence = Column(String, nullable=False, default="LOW")  # HIGH, MEDIUM, LOW
    metadata_json = Column(Text, nullable=True)  # JSON for extra data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    skill = relationship("Skill")

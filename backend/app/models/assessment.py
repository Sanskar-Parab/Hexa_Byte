import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, JSON
from app.models.types import GUID
from sqlalchemy.orm import relationship
from app.database.config import Base


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    question_text = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    options = Column(JSON, nullable=False)
    scoring = Column(JSON, nullable=False)


class UserAssessment(Base):
    __tablename__ = "user_assessments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    answers = Column(JSON, nullable=False)
    scores = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="assessments")

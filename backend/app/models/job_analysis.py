import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from app.models.types import GUID
from sqlalchemy.orm import relationship
from app.database.config import Base


class JobAnalysis(Base):
    __tablename__ = "job_analyses"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    job_title = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    required_skills = Column(Text, nullable=True)       # JSON array
    preferred_skills = Column(Text, nullable=True)      # JSON array
    experience_required = Column(String, nullable=True)
    education_required = Column(String, nullable=True)
    responsibilities = Column(Text, nullable=True)      # JSON array
    technologies = Column(Text, nullable=True)          # JSON array
    match_result = Column(Text, nullable=True)          # JSON: full match analysis
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from app.models.types import GUID
from sqlalchemy.orm import relationship
from app.database.config import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    skills = Column(Text, nullable=True)          # JSON array
    projects = Column(Text, nullable=True)        # JSON array
    experience = Column(Text, nullable=True)      # JSON array
    education = Column(Text, nullable=True)       # JSON array
    certifications = Column(Text, nullable=True)  # JSON array
    technologies = Column(Text, nullable=True)    # JSON array
    tools = Column(Text, nullable=True)           # JSON array
    matched_skills = Column(Text, nullable=True)  # JSON array of {skill_id, skill_name, context}
    extracted_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

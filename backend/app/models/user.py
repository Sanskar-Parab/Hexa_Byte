import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from app.models.types import GUID
from sqlalchemy.orm import relationship
from app.database.config import Base


class User(Base):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("Profile", back_populates="user", uselist=False)
    skills = relationship("UserSkill", back_populates="user")
    interests = relationship("UserInterest", back_populates="user")
    assessments = relationship("UserAssessment", back_populates="user")
    career_recommendations = relationship("CareerRecommendation", back_populates="user")
    roadmaps = relationship("Roadmap", back_populates="user")
    recommended_projects = relationship("RecommendedProject", back_populates="user")
    progress = relationship("UserProgress", back_populates="user")

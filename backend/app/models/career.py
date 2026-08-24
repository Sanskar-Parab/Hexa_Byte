import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Text, ForeignKey, DateTime, JSON
from app.models.types import GUID
from sqlalchemy.orm import relationship
from app.database.config import Base


class Career(Base):
    __tablename__ = "careers"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    category = Column(String)
    required_skills = Column(JSON)
    optional_skills = Column(JSON)
    skill_importance = Column(JSON)
    recommended_projects = Column(JSON)
    learning_sequence = Column(JSON)
    related_careers = Column(JSON)

    recommendations = relationship("CareerRecommendation", back_populates="career")


class CareerRecommendation(Base):
    __tablename__ = "career_recommendations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    career_id = Column(GUID(), ForeignKey("careers.id"), nullable=False)
    match_score = Column(Float, nullable=False)
    confidence = Column(String)
    why_matches = Column(JSON)
    strengths = Column(JSON)
    missing_skills = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="career_recommendations")
    career = relationship("Career", back_populates="recommendations")

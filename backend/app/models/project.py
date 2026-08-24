import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, Float, ForeignKey, DateTime, JSON
from app.models.types import GUID
from sqlalchemy.orm import relationship
from app.database.config import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text)
    difficulty = Column(String)
    skills_developed = Column(JSON)
    expected_outcome = Column(Text)
    estimated_duration_weeks = Column(Integer)
    portfolio_value = Column(Text)

    recommended = relationship("RecommendedProject", back_populates="project")


class RecommendedProject(Base):
    __tablename__ = "recommended_projects"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    project_id = Column(GUID(), ForeignKey("projects.id"), nullable=False)
    career_id = Column(GUID(), ForeignKey("careers.id"), nullable=False)
    status = Column(String, default="recommended")  # recommended, in_progress, completed
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="recommended_projects")
    project = relationship("Project", back_populates="recommended")
    career = relationship("Career")

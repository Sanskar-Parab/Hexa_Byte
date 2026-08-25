import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, JSON
from app.models.types import GUID
from sqlalchemy.orm import relationship
from app.database.config import Base


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    career_id = Column(GUID(), ForeignKey("careers.id"), nullable=False)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="roadmaps")
    career = relationship("Career")
    phases = relationship("RoadmapPhase", back_populates="roadmap", order_by="RoadmapPhase.phase_number")


class RoadmapPhase(Base):
    __tablename__ = "roadmap_phases"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    roadmap_id = Column(GUID(), ForeignKey("roadmaps.id"), nullable=False)
    phase_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    objective = Column(Text)
    skills = Column(JSON)
    activities = Column(JSON)
    project = Column(Text)
    duration_weeks = Column(Integer)
    completion_criteria = Column(JSON)
    status = Column(String, default="not_started")  # not_started, in_progress, completed
    adaptation_mode = Column(String, default="full")  # full, adapted, skipped
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    roadmap = relationship("Roadmap", back_populates="phases")

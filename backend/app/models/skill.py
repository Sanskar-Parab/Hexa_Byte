import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from app.models.types import GUID
from sqlalchemy.orm import relationship
from app.database.config import Base


class Skill(Base):
    __tablename__ = "skills"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text)
    beginner_definition = Column(Text)
    intermediate_definition = Column(Text)
    advanced_definition = Column(Text)

    user_skills = relationship("UserSkill", back_populates="skill")


class UserSkill(Base):
    __tablename__ = "user_skills"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    skill_id = Column(GUID(), ForeignKey("skills.id"), nullable=False)
    proficiency = Column(Integer, nullable=False)  # 1-5
    level_name = Column(String, nullable=True)  # Beginner, Basic, Intermediate, Advanced, Expert
    confidence = Column(String, nullable=True, default="LOW")  # HIGH, MEDIUM, LOW
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="skills")
    skill = relationship("Skill", back_populates="user_skills")

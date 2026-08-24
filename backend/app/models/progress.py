import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from app.models.types import GUID
from sqlalchemy.orm import relationship
from app.database.config import Base


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    item_type = Column(String, nullable=False)  # phase, project, assessment
    item_id = Column(String, nullable=False)
    status = Column(String, default="not_started")  # not_started, in_progress, completed
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    user = relationship("User", back_populates="progress")

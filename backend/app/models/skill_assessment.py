import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer
from app.models.types import GUID
from app.database.config import Base


class SkillAssessmentSession(Base):
    __tablename__ = "skill_assessment_sessions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    skill_id = Column(GUID(), ForeignKey("skills.id"), nullable=False)
    questions_json = Column(Text, nullable=False)
    answers_json = Column(Text, nullable=True)
    score_percentage = Column(Integer, nullable=True)
    proficiency = Column(Integer, nullable=True)
    level_name = Column(String, nullable=True)
    status = Column(String, nullable=False, default="in_progress")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def get_questions(self):
        return json.loads(self.questions_json) if self.questions_json else []

    def set_questions(self, questions):
        self.questions_json = json.dumps(questions)

    def get_answers(self):
        return json.loads(self.answers_json) if self.answers_json else []

    def set_answers(self, answers):
        self.answers_json = json.dumps(answers)

from app.database.config import Base, engine
from app.models.user import User
from app.models.profile import Profile
from app.models.skill import Skill, UserSkill
from app.models.interest import Interest, UserInterest
from app.models.career import Career, CareerRecommendation
from app.models.assessment import AssessmentQuestion, UserAssessment
from app.models.roadmap import Roadmap, RoadmapPhase
from app.models.project import Project, RecommendedProject
from app.models.progress import UserProgress


def run_migrations():
    Base.metadata.create_all(bind=engine)

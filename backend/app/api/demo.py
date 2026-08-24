from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.skill import Skill, UserSkill
from app.models.interest import Interest, UserInterest
from app.models.assessment import AssessmentQuestion, UserAssessment
from app.models.career import Career, CareerRecommendation
from app.models.roadmap import Roadmap, RoadmapPhase
from app.models.project import Project, RecommendedProject
from app.utils.auth import create_access_token, get_password_hash

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post("/load")
def load_demo_data(db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == "aarav.sharma@demo.com").first()
    if existing:
        token = create_access_token(data={"sub": str(existing.id)})
        return {"message": "Demo data already loaded", "token": token, "user_id": str(existing.id)}

    demo_user = User(
        name="Aarav Sharma",
        email="aarav.sharma@demo.com",
        password_hash=get_password_hash("demo123"),
        is_demo=True,
    )
    db.add(demo_user)
    db.flush()

    profile = Profile(
        user_id=demo_user.id,
        age_group="18-22",
        education_level="Bachelor's",
        degree="B.Tech",
        branch="Computer Science",
        current_year="3rd Year",
        internship_experience="1 internship at a startup as a web developer",
        work_experience="",
        projects_count=3,
    )
    db.add(profile)

    demo_skills = {
        "Python": 4, "JavaScript": 3, "React": 3, "HTML/CSS": 4,
        "SQL": 3, "Git": 3, "Data Structures": 3, "Algorithms": 2,
        "Machine Learning": 1, "Docker": 1, "AWS": 1, "Node.js": 2,
    }
    for name, prof in demo_skills.items():
        skill = db.query(Skill).filter(Skill.name == name).first()
        if skill:
            db.add(UserSkill(user_id=demo_user.id, skill_id=skill.id, proficiency=prof))

    demo_interests = ["Technology", "Problem Solving", "Data Analysis", "Innovation"]
    for name in demo_interests:
        interest = db.query(Interest).filter(Interest.name == name).first()
        if interest:
            db.add(UserInterest(user_id=demo_user.id, interest_id=interest.id))

    answers = {}
    questions = db.query(AssessmentQuestion).all()
    for q in questions:
        answers[str(q.id)] = 2

    assessment = UserAssessment(
        user_id=demo_user.id,
        answers=answers,
        scores={
            "technical_interest": 0.75,
            "problem_solving": 0.80,
            "analytical_ability": 0.70,
            "creativity": 0.55,
            "communication": 0.60,
            "technology_interest": 0.85,
            "business_interest": 0.40,
            "research_interest": 0.50,
        },
    )
    db.add(assessment)
    db.commit()

    token = create_access_token(data={"sub": str(demo_user.id)})
    return {
        "message": "Demo data loaded successfully",
        "token": token,
        "user_id": str(demo_user.id),
        "user": {
            "name": demo_user.name,
            "email": demo_user.email,
        },
    }

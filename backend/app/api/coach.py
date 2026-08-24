from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.skill import UserSkill, Skill
from app.models.interest import UserInterest, Interest
from app.models.assessment import UserAssessment
from app.ai.client import AIClient
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/coach", tags=["coach"])


class CoachRequest(BaseModel):
    question: str


@router.post("/ask")
async def ask_coach(
    request: CoachRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == current_user.id).all()
    all_skills = {s.id: s for s in db.query(Skill).all()}
    user_interests = db.query(UserInterest).filter(UserInterest.user_id == current_user.id).all()
    all_interests = {i.id: i for i in db.query(Interest).all()}
    assessments = db.query(UserAssessment).filter(UserAssessment.user_id == current_user.id).order_by(UserAssessment.created_at.desc()).first()

    context_parts = [f"Name: {current_user.name}"]
    if profile:
        context_parts.append(f"Education: {profile.education_level}, {profile.degree}, {profile.branch}")
        context_parts.append(f"Year: {profile.current_year}")
        if profile.internship_experience:
            context_parts.append(f"Internships: {profile.internship_experience}")

    skill_names = []
    for us in user_skills:
        s = all_skills.get(us.skill_id)
        if s:
            skill_names.append(f"{s.name}({us.proficiency}/5)")
    if skill_names:
        context_parts.append(f"Skills: {', '.join(skill_names)}")

    interest_names = []
    for ui in user_interests:
        i = all_interests.get(ui.interest_id)
        if i:
            interest_names.append(i.name)
    if interest_names:
        context_parts.append(f"Interests: {', '.join(interest_names)}")

    if assessments and assessments.scores:
        top = sorted(assessments.scores.items(), key=lambda x: x[1], reverse=True)[:3]
        context_parts.append(f"Top assessment dimensions: {', '.join(d[0] for d in top)}")

    user_context = "\n".join(context_parts)

    ai = AIClient()
    if ai.is_available:
        response = await ai.generate_coaching_response(request.question, user_context)
        if response:
            return {"response": response, "source": "ai"}

    return {
        "response": f"Based on your profile ({current_user.name}), here's my advice regarding '{request.question}': "
                    f"Consider focusing on building your skills in areas aligned with your interests. "
                    f"Your current skills include: {', '.join(skill_names[:5]) if skill_names else 'none tracked yet'}. "
                    f"I recommend completing the career assessment and exploring the recommended career paths.",
        "source": "fallback",
    }

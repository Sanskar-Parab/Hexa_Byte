from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.utils.auth import get_current_user
from app.services.coach_service import ask_coach, get_coach_context

router = APIRouter(prefix="/api/coach", tags=["coach"])


class ConversationTurn(BaseModel):
    role: str
    content: str


class CoachRequest(BaseModel):
    question: str
    # Recent chat history only, for follow-up questions like "why?" — never a
    # source of user identity or profile data. That always comes from the
    # authenticated session below.
    conversation: list[ConversationTurn] = Field(default_factory=list)


@router.post("/ask")
async def ask_coach_endpoint(
    request: CoachRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = [turn.model_dump() for turn in request.conversation]
    result = await ask_coach(db, current_user.id, request.question, conversation)
    return result


@router.get("/context")
def get_coach_context_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_coach_context(db, current_user.id)

from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class ProgressUpdate(BaseModel):
    item_type: str  # phase, project, assessment
    item_id: str
    status: str  # not_started, in_progress, completed


class ProgressResponse(BaseModel):
    id: UUID
    item_type: str
    item_id: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

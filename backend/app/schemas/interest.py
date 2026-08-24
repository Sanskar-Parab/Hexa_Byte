from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class InterestCreate(BaseModel):
    name: str
    category: str


class InterestResponse(BaseModel):
    id: UUID
    name: str
    category: str

    class Config:
        from_attributes = True

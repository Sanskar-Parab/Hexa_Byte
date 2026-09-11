from pydantic import BaseModel, Field
from typing import Optional, Literal
from uuid import UUID
from datetime import date, datetime


class TraineeProgramCreate(BaseModel):
    """Admin creates a program-specific trainee record."""
    # Name, DOB, Phone per spec MVP
    trainee_name: str = Field(..., min_length=1, description="Full name as per program record")
    dob: date = Field(..., description="Date of birth")
    phone: Optional[str] = Field(None, description="Phone number (10 digits, optional)")
    program_name: str = Field(..., min_length=1, description="Program name e.g. PMKVY, DDU-GKY")
    program_trainee_id: str = Field(..., min_length=1, description="Program-specific trainee ID e.g. PMK-10231")

class TraineeMatchPreviewRequest(BaseModel):
    trainee_name: str
    dob: date
    phone: Optional[str] = None
    program_name: str
    program_trainee_id: str


class FieldScores(BaseModel):
    name: float  # 0-1
    dob: float
    phone: float
    program: float


class MatchResult(BaseModel):
    match_score: float  # 0-100
    confidence: Literal["high", "medium", "low"]
    field_scores: FieldScores
    field_weights: Optional[dict] = None
    matched: Optional[bool] = None
    master_id: Optional[str] = None
    master_code: Optional[str] = None
    matched_master: Optional[dict] = None


class TraineeProgramRecordResponse(BaseModel):
    id: UUID
    master_trainee_id: UUID
    program_name: str
    program_trainee_id: str
    trainee_name: str
    dob: date
    phone: Optional[str] = None
    masked_phone: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


class MasterTraineeResponse(BaseModel):
    id: UUID
    master_code: str
    primary_name: str
    dob: date
    phone_numbers: list[str] = Field(default_factory=list)
    masked_phones: list[str] = Field(default_factory=list)
    linked_user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    enrollment_count: int = 0
    class Config:
        from_attributes = True


class MasterTraineeDetailResponse(BaseModel):
    master: MasterTraineeResponse
    enrollments: list[TraineeProgramRecordResponse]
    longitudinal: Optional[dict] = None


class CreateTraineeResponse(BaseModel):
    action: Literal["new_master", "auto_linked", "review_required"]
    confidence: str
    match_score: float
    field_scores: FieldScores
    master: Optional[MasterTraineeResponse] = None
    record: Optional[TraineeProgramRecordResponse] = None
    review: Optional["IdentityReviewResponse"] = None
    match_detail: Optional[MatchResult] = None
    message: Optional[str] = None


class IdentityReviewResponse(BaseModel):
    id: UUID
    incoming_name: str
    incoming_dob: date
    incoming_phone: Optional[str] = None
    masked_phone: Optional[str] = None
    incoming_program_name: str
    incoming_program_trainee_id: str
    matched_master_id: Optional[UUID] = None
    match_score: float
    confidence: str
    field_scores: FieldScores
    status: str
    created_at: datetime
    decided_at: Optional[datetime] = None
    matched_master: Optional[MasterTraineeResponse] = None
    matched_master_enrollments: list[TraineeProgramRecordResponse] = Field(default_factory=list)
    class Config:
        from_attributes = True


class ReviewDecisionRequest(BaseModel):
    decision: Literal["link", "reject"]


class ListMastersResponse(BaseModel):
    items: list[MasterTraineeResponse]
    total: int
    page: int
    page_size: int


class ListReviewsResponse(BaseModel):
    items: list[IdentityReviewResponse]
    total: int
    page: int
    page_size: int


# For pydantic v2 forward ref
CreateTraineeResponse.model_rebuild()

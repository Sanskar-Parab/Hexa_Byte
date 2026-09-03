from pydantic import BaseModel
from typing import Literal

Confidence = Literal["high", "medium", "low", "insufficient"]
AttritionCategory = Literal[
    "skill_mismatch", "role_mismatch", "location", "salary", "career_change", "unknown"
]


class EvidenceItem(BaseModel):
    """One deterministically-computed, verifiable fact — never AI-authored."""
    id: str
    statement: str


class NonPlacementAnalysisResponse(BaseModel):
    primary_reason: str
    supporting_evidence: list[str]
    confidence: Confidence
    recommended_intervention: str
    source: Literal["ai", "fallback"]
    evidence: list[EvidenceItem]


class AttritionAnalysisResponse(BaseModel):
    category: AttritionCategory
    primary_reason: str
    supporting_evidence: list[str]
    confidence: Confidence
    recommended_intervention: str
    source: Literal["ai", "fallback"]
    evidence: list[EvidenceItem]


class TrainingRelevanceExplanationResponse(BaseModel):
    level: Literal["high", "medium", "low", "unknown"]
    explanation: str
    overlap_skills: list[str]
    coverage_ratio: float
    source: Literal["ai", "fallback"]

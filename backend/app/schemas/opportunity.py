from typing import Optional

from pydantic import BaseModel


class MatchedSkill(BaseModel):
    skill: str
    user_proficiency: int
    requirement: str = "required"


class OpportunityRecommendation(BaseModel):
    id: str
    title: str
    organization: str
    organization_url: Optional[str] = None
    type: str
    url: Optional[str] = None
    logo: Optional[str] = None
    location: Optional[str] = None
    remote: Optional[bool] = None
    work_type: Optional[str] = None
    seniority: Optional[str] = None
    salary: Optional[str] = None
    posted_date: Optional[str] = None
    valid_through: Optional[str] = None
    source: Optional[str] = None
    source_domain: Optional[str] = None
    registration_open: bool = True
    match_score: int
    matched_skills: list[MatchedSkill]
    partial_skills: list[MatchedSkill]
    missing_skills: list[str]
    why_match: list[str]
    skill_gap_message: Optional[str] = None
    recommendation: Optional[str] = None


class UserSkillSummary(BaseModel):
    skills_used: list[str]
    skill_count: int


class OpportunityRecommendationsResponse(BaseModel):
    recommendations: list[OpportunityRecommendation]
    user_skill_summary: UserSkillSummary
    source_status: str = "ok"
    message: Optional[str] = None

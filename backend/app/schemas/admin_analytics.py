from pydantic import BaseModel
from typing import Optional


class CohortMetrics(BaseModel):
    trainee_count: int
    demo_trainee_count: int = 0
    sample_size_sufficient: bool
    training_completion_rate: Optional[float] = None
    placement_rate: Optional[float] = None
    employment_rate: Optional[float] = None
    self_employment_rate: Optional[float] = None
    unemployment_rate: Optional[float] = None
    non_placement_rate: Optional[float] = None
    retention_3_month_rate: Optional[float] = None
    retention_6_month_rate: Optional[float] = None
    retention_12_month_rate: Optional[float] = None
    average_starting_salary: Optional[float] = None
    average_current_salary: Optional[float] = None
    wage_growth_percentage: Optional[float] = None
    training_relevant_employment_rate: Optional[float] = None


class ProviderComparisonRow(CohortMetrics):
    provider_name: str


class SkillGapRow(BaseModel):
    skill: str
    trainee_count: int
    percentage: Optional[float] = None


class ProgramAnalyticsRow(CohortMetrics):
    training_program_id: str
    training_program_name: str
    provider_name: str
    career_domain: Optional[str] = None
    skill_gaps: list[SkillGapRow] = []


class NonPlacementCategoryRow(BaseModel):
    category: str
    trainee_count: int
    percentage: Optional[float] = None


class CurriculumRecommendationRow(BaseModel):
    training_program_id: str
    training_program_name: str
    provider_name: str
    skill: str
    affected_trainee_percentage: Optional[float] = None
    program_placement_rate: Optional[float] = None
    overall_placement_rate: Optional[float] = None
    recommendation: str


class FilterOptionsResponse(BaseModel):
    providers: list[str]
    career_domains: list[str]
    programs: list[dict]
    locations: list[str]
    employment_statuses: list[str]

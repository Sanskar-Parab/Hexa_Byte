from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.user import User
from app.schemas.admin_analytics import (
    CohortMetrics,
    ProviderComparisonRow,
    ProgramAnalyticsRow,
    SkillGapRow,
    NonPlacementCategoryRow,
    CurriculumRecommendationRow,
    FilterOptionsResponse,
)
from app.services import admin_analytics, demo_outcome_seed
from app.services.admin_analytics import AnalyticsFilters
from app.utils.auth import get_current_admin_user

router = APIRouter(prefix="/api/admin/outcomes", tags=["admin-analytics"])


def _filters(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    provider_name: str | None = Query(default=None),
    training_program_id: UUID | None = Query(default=None),
    career_domain: str | None = Query(default=None),
    location: str | None = Query(default=None),
    employment_status: str | None = Query(default=None),
) -> AnalyticsFilters:
    return AnalyticsFilters(
        start_date=start_date,
        end_date=end_date,
        provider_name=provider_name,
        training_program_id=training_program_id,
        career_domain=career_domain,
        location=location,
        employment_status=employment_status,
    )


@router.get("/overview", response_model=CohortMetrics)
def get_overview(
    filters: AnalyticsFilters = Depends(_filters),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    return admin_analytics.get_overview_metrics(db, filters)


@router.get("/providers", response_model=list[ProviderComparisonRow])
def get_providers(
    filters: AnalyticsFilters = Depends(_filters),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    return admin_analytics.get_provider_comparison(db, filters)


@router.get("/programs", response_model=list[ProgramAnalyticsRow])
def get_programs(
    filters: AnalyticsFilters = Depends(_filters),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    return admin_analytics.get_program_analytics(db, filters)


@router.get("/skill-gaps", response_model=list[SkillGapRow])
def get_skill_gaps(
    filters: AnalyticsFilters = Depends(_filters),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    return admin_analytics.get_skill_gap_analytics(db, filters)


@router.get("/non-placement", response_model=list[NonPlacementCategoryRow])
def get_non_placement(
    filters: AnalyticsFilters = Depends(_filters),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    return admin_analytics.get_non_placement_analytics(db, filters)


@router.get("/curriculum-recommendations", response_model=list[CurriculumRecommendationRow])
def get_curriculum_recommendations(
    filters: AnalyticsFilters = Depends(_filters),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """The evidence-driven improvement loop: recurring skill gaps correlated
    with below-average placement, flagged for curriculum review. Purely a
    threshold over deterministic aggregates — no AI, no fabricated insight."""
    return admin_analytics.get_curriculum_recommendations(db, filters)


@router.get("/filters", response_model=FilterOptionsResponse)
def get_filter_options(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    return admin_analytics.get_filter_options(db)


@router.post("/demo-data")
def load_demo_outcome_data(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Admin-only, idempotent: seeds clearly-labelled synthetic demo trainees
    (see app.services.demo_outcome_seed) for hackathon demonstration. Never
    represents itself as real Maharashtra Government data — every seeded
    trainee is flagged `is_demo=True` and surfaced via `demo_trainee_count`
    on every dashboard metric."""
    return demo_outcome_seed.seed_demo_outcome_data(db)

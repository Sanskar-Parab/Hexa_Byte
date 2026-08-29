"""Orchestrates the AI-personalized job/internship recommendation pipeline.

USER -> demonstrated skills+proficiency -> normalization -> live opportunity
provider data -> required-skill extraction -> deterministic skill matching ->
AI contextual analysis (top candidates only) -> hybrid score -> ranked,
filtered results.

Never recommends from a local database of jobs — every opportunity returned
originates from `app.services.opportunity_provider` (live RapidAPI data).
"""
import logging
import os
import threading
import time
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.groq_client import groq_client
from app.models.skill import Skill, UserSkill
from app.services import opportunity_provider
from app.services.opportunity_matching import match_opportunity_skills

logger = logging.getLogger(__name__)

AI_ANALYSIS_TOP_N = int(os.getenv("OPPORTUNITY_AI_TOP_N", "5"))
DETERMINISTIC_WEIGHT = float(os.getenv("OPPORTUNITY_DETERMINISTIC_WEIGHT", "0.6"))
AI_WEIGHT = float(os.getenv("OPPORTUNITY_AI_WEIGHT", "0.4"))

# This provider returns no explicit skills field on ANY posting, so every
# opportunity would otherwise need its own Groq call just to get a skill
# list. Bound that cost two ways: cache extracted skills per posting (they
# don't change) and cap how many *new* extractions one request will pay for
# — postings beyond the cap simply get an empty skill list (deterministic
# score 0), which is no worse than what an irrelevant posting would score
# anyway, and they still sort to the bottom.
_SKILL_EXTRACTION_CACHE_TTL_SECONDS = 3600
MAX_SKILL_EXTRACTIONS_PER_REQUEST = int(os.getenv("OPPORTUNITY_MAX_SKILL_EXTRACTIONS", "20"))

_skill_extraction_cache: dict[str, tuple[float, list[str]]] = {}
_skill_extraction_lock = threading.Lock()

UNAVAILABLE_MESSAGE = "Opportunities are temporarily unavailable. Please try again later."

# type -> human label used when only that type failed to fetch (partial degradation).
_TYPE_LABELS = {"internship": "Internship", "job": "Job"}


def _get_cached_skills(cache_key: str) -> Optional[list[str]]:
    with _skill_extraction_lock:
        entry = _skill_extraction_cache.get(cache_key)
        if not entry:
            return None
        expires_at, value = entry
        if time.time() > expires_at:
            del _skill_extraction_cache[cache_key]
            return None
        return value


def _set_cached_skills(cache_key: str, value: list[str]) -> None:
    with _skill_extraction_lock:
        _skill_extraction_cache[cache_key] = (time.time() + _SKILL_EXTRACTION_CACHE_TTL_SECONDS, value)


def clear_skill_extraction_cache() -> None:
    with _skill_extraction_lock:
        _skill_extraction_cache.clear()


def get_user_skill_map(db: Session, user_id: UUID) -> dict[str, int]:
    """The authenticated user's REAL demonstrated skills, never hardcoded/invented."""
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    if not user_skills:
        return {}
    all_skills = {s.id: s for s in db.query(Skill).all()}
    result: dict[str, int] = {}
    for us in user_skills:
        skill = all_skills.get(us.skill_id)
        if skill:
            result[skill.name] = us.proficiency
    return result


def _extract_required_skills(opportunity: dict, extraction_budget: dict[str, int]) -> list[str]:
    """This provider does not supply an explicit required-skills field, so
    every opportunity falls back to Groq extraction from title+description
    (only when Groq is available; never fabricated deterministically).

    Results are cached per posting (id+type) and the number of *new*
    extractions per request is bounded by `extraction_budget` — see the
    module-level comment for why.
    """
    if opportunity.get("required_skills"):
        return opportunity["required_skills"]

    cache_key = f"{opportunity.get('type')}:{opportunity.get('id')}"
    cached = _get_cached_skills(cache_key)
    if cached is not None:
        return cached

    if not groq_client.is_available or extraction_budget["remaining"] <= 0:
        return []

    text = f"{opportunity.get('title', '')}. {opportunity.get('description', '')}".strip()
    if len(text) < 10:
        return []

    extraction_budget["remaining"] -= 1
    skills, _ = groq_client.extract_skills_from_text(text)
    result = skills or []
    _set_cached_skills(cache_key, result)
    return result


def _default_why_match(deterministic: dict) -> list[str]:
    reasons = []
    for item in deterministic["matched_skills"][:3]:
        reasons.append(f"Strong {item['skill']} proficiency ({item['user_proficiency']}/5)")
    for item in deterministic["partial_skills"][:2]:
        reasons.append(f"Some experience with {item['skill']} ({item['user_proficiency']}/5)")
    if not reasons:
        reasons.append("This role is in your target skill area, though no direct skill matches were found yet.")
    return reasons


def _skill_gap_message(missing_skills: list[str]) -> Optional[str]:
    if not missing_skills:
        return None
    if len(missing_skills) == 1:
        return f"Learning {missing_skills[0]} would strengthen this match."
    return f"Learning {', '.join(missing_skills[:2])} would strengthen this match."


def get_recommendations(
    db: Session,
    user_id: UUID,
    opportunity_type: str = "all",
    limit: int = 10,
    min_match: int = 0,
    target_career: Optional[str] = None,
) -> dict[str, Any]:
    """Full pipeline: authenticated user's skills -> live provider data -> ranked matches.

    Returns a dict matching OpportunityRecommendationsResponse. Degrades
    gracefully on any provider failure — never raises to the caller. A
    failure for one type (e.g. jobs down, internships fine) does not hide
    the data that *did* load; `source_status` is only "unavailable" when
    nothing could be fetched at all.
    """
    user_skill_map = get_user_skill_map(db, user_id)

    types_to_fetch = ["internship", "job"] if opportunity_type == "all" else [opportunity_type]

    opportunities: list[dict] = []
    failed_types: list[str] = []

    for otype in types_to_fetch:
        try:
            # Exactly one provider request per type per cache window — no
            # role-based pre-filtering or multi-call fan-out. Relevance to
            # the user's skills is achieved entirely by the deterministic +
            # AI scoring below, which ranks/filters after a single fetch.
            items = opportunity_provider.get_opportunities(otype)
            opportunities.extend(items)
        except opportunity_provider.OpportunityProviderError as e:
            logger.warning(f"Opportunity provider fetch failed for {otype}: {e}")
            failed_types.append(otype)

    skill_summary = {
        "skills_used": sorted(user_skill_map.keys()),
        "skill_count": len(user_skill_map),
    }

    if not opportunities:
        return {
            "recommendations": [],
            "user_skill_summary": skill_summary,
            "source_status": "unavailable" if failed_types else "ok",
            "message": UNAVAILABLE_MESSAGE if failed_types else "No opportunities found right now.",
        }

    # Some data loaded even though another type failed — surface that
    # partial degradation without hiding the recommendations that did load.
    partial_message = None
    if failed_types:
        labels = " and ".join(_TYPE_LABELS.get(t, t) for t in failed_types)
        partial_message = f"{labels} data is temporarily unavailable — showing what's currently available."

    scored = []
    extraction_budget = {"remaining": MAX_SKILL_EXTRACTIONS_PER_REQUEST}
    for opp in opportunities:
        required_skills = _extract_required_skills(opp, extraction_budget)
        deterministic = match_opportunity_skills(required_skills, user_skill_map)
        scored.append({"opportunity": opp, "required_skills": required_skills, "deterministic": deterministic})

    scored.sort(key=lambda x: x["deterministic"]["match_score"], reverse=True)

    # Only the strongest candidates are worth an AI call — bounded cost.
    candidate_pool = scored[: max(limit * 2, AI_ANALYSIS_TOP_N, limit)]

    final_results = []
    for i, entry in enumerate(candidate_pool):
        opp = entry["opportunity"]
        deterministic = entry["deterministic"]

        ai_analysis = None
        if i < AI_ANALYSIS_TOP_N and groq_client.is_available and deterministic["match_score"] > 0:
            ai_analysis, _ = groq_client.analyze_opportunity_match(
                title=opp["title"],
                organization=opp["organization"],
                opp_type=opp["type"],
                required_skills=entry["required_skills"],
                description=opp.get("description", ""),
                user_skills=user_skill_map,
                target_career=target_career,
                deterministic_result=deterministic,
            )

        if ai_analysis:
            final_score = round(
                deterministic["match_score"] * DETERMINISTIC_WEIGHT
                + ai_analysis.match_score * AI_WEIGHT
            )
            why_match = ai_analysis.why_match or _default_why_match(deterministic)
            recommendation = ai_analysis.recommendation or None
        else:
            final_score = deterministic["match_score"]
            why_match = _default_why_match(deterministic)
            recommendation = None

        final_results.append({
            "id": opp["id"],
            "title": opp["title"],
            "organization": opp["organization"],
            "organization_url": opp.get("organization_url"),
            "type": opp["type"],
            "url": opp.get("url"),
            "logo": opp.get("logo"),
            "location": opp.get("location"),
            "remote": opp.get("remote"),
            "work_type": opp.get("employment_type"),
            "seniority": opp.get("seniority"),
            "salary": opp.get("salary"),
            "posted_date": opp.get("posted_date"),
            "valid_through": opp.get("valid_through"),
            "source": opp.get("source"),
            "source_domain": opp.get("source_domain"),
            "registration_open": bool(opp.get("registration_open", True)),
            "match_score": max(0, min(100, final_score)),
            "matched_skills": deterministic["matched_skills"],
            "partial_skills": deterministic["partial_skills"],
            "missing_skills": deterministic["missing_skills"],
            "why_match": why_match,
            "skill_gap_message": _skill_gap_message(deterministic["missing_skills"]),
            "recommendation": recommendation,
        })

    final_results.sort(key=lambda x: x["match_score"], reverse=True)
    final_results = [r for r in final_results if r["match_score"] >= min_match][:limit]

    return {
        "recommendations": final_results,
        "user_skill_summary": skill_summary,
        "source_status": "ok",
        "message": partial_message,
    }

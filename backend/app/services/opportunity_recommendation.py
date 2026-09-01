"""Orchestrates the AI-personalized job/internship recommendation pipeline.

USER -> demonstrated skills+proficiency -> normalization -> career-aware
JSearch query -> live opportunity provider data (India) -> required-skill
extraction -> deterministic skill matching -> experience-suitability nudge ->
AI contextual analysis (top candidates only) -> hybrid score -> ranked,
filtered results.

Never recommends from a local database of jobs — every opportunity returned
originates from `app.services.opportunity_provider` (live JSearch data via
RapidAPI).
"""
import logging
import os
import re
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

# Search strategy (Phase 10): one primary career/skill-based query per
# request; a second query only fires when the primary came back thin. Never
# one query per skill — that's what exhausted the previous provider's quota.
MIN_RESULTS_BEFORE_SECONDARY_QUERY = 8

# JSearch returns no explicit skills field on many postings, so those fall
# back to Groq extraction from title+description. Bound that cost two ways:
# cache extracted skills per posting (they don't change) and cap how many
# *new* extractions one request will pay for — postings beyond the cap
# simply get an empty skill list (deterministic score 0), which is no worse
# than what an irrelevant posting would score anyway, and they still sort to
# the bottom.
_SKILL_EXTRACTION_CACHE_TTL_SECONDS = 3600
MAX_SKILL_EXTRACTIONS_PER_REQUEST = int(os.getenv("OPPORTUNITY_MAX_SKILL_EXTRACTIONS", "20"))

_skill_extraction_cache: dict[str, tuple[float, list[str]]] = {}
_skill_extraction_lock = threading.Lock()

UNAVAILABLE_MESSAGE = "Opportunities are temporarily unavailable. Please try again later."

# Beginner-priority ranking nudge (Phase 24/41) — a small signal, not a hard
# filter, and only ever applied on top of a nonzero deterministic skill match
# so it can never turn an unrelated posting into a "good" recommendation.
_BEGINNER_FRIENDLY_PATTERN = re.compile(
    r"\b(intern(ship)?|entry.level|entry level|junior|graduate|fresher|trainee)\b", re.IGNORECASE
)
_SENIOR_PATTERN = re.compile(r"\b(senior|sr\.?|staff|principal|lead|architect|manager)\b", re.IGNORECASE)
BEGINNER_PROFICIENCY_CEILING = 4  # user has no skill at Advanced (4/5) or above
SENIOR_EXPERIENCE_YEARS = 4
BEGINNER_MATCH_BONUS = 8
SENIOR_ROLE_PENALTY = 12


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


def _top_skill(user_skill_map: dict[str, int]) -> Optional[str]:
    if not user_skill_map:
        return None
    return max(user_skill_map.items(), key=lambda kv: kv[1])[0]


def _build_search_queries(
    target_career: Optional[str],
    user_skill_map: dict[str, int],
    opportunity_type: str,
) -> list[str]:
    """Career-aware query generation (Phase 9/40): a primary query driven by
    the user's target career (falling back to their strongest skill, then a
    generic technology query), plus an optional secondary query driven by
    their strongest skill — never one query per skill.
    """
    base = (target_career or "").strip()
    if not base:
        top_skill = _top_skill(user_skill_map)
        base = f"{top_skill} developer" if top_skill else "software developer"

    # An internship-only request is better served by biasing the query text
    # itself than by fetching a mixed pool and discarding most of it.
    suffix = " intern" if opportunity_type == "internship" else ""
    primary = f"{base}{suffix}".strip()

    queries = [primary]

    top_skill = _top_skill(user_skill_map)
    if top_skill:
        secondary = f"{top_skill} developer{suffix}".strip()
        if secondary.lower() != primary.lower():
            queries.append(secondary)

    return queries[:2]


def _merge_dedupe(existing: list[dict], additions: list[dict]) -> list[dict]:
    seen_ids = {o["id"] for o in existing}
    seen_urls = {o["url"] for o in existing if o.get("url")}
    merged = list(existing)
    for opp in additions:
        if opp["id"] in seen_ids:
            continue
        if opp.get("url") and opp["url"] in seen_urls:
            continue
        seen_ids.add(opp["id"])
        if opp.get("url"):
            seen_urls.add(opp["url"])
        merged.append(opp)
    return merged


def _fetch_candidate_pool(
    target_career: Optional[str],
    user_skill_map: dict[str, int],
    opportunity_type: str,
) -> tuple[list[dict], bool]:
    """Runs the search strategy: always one primary query; a second query
    only when the primary came back thin (Phase 10). Returns
    (opportunities, fetch_failed) — fetch_failed is only True when nothing
    could be fetched at all, so a working secondary/failing primary (or vice
    versa) still returns whatever data did load.
    """
    queries = _build_search_queries(target_career, user_skill_map, opportunity_type)

    pool: list[dict] = []
    any_success = False

    try:
        pool = opportunity_provider.get_opportunities(queries[0])
        any_success = True
    except opportunity_provider.OpportunityProviderError as e:
        logger.warning("Primary opportunity search failed for %r: %s", queries[0], e)

    if len(pool) < MIN_RESULTS_BEFORE_SECONDARY_QUERY and len(queries) > 1:
        try:
            more = opportunity_provider.get_opportunities(queries[1])
            pool = _merge_dedupe(pool, more)
            any_success = True
        except opportunity_provider.OpportunityProviderError as e:
            logger.warning("Secondary opportunity search failed for %r: %s", queries[1], e)

    return pool, not any_success


def _extract_required_skills(opportunity: dict, extraction_budget: dict[str, int]) -> list[str]:
    """Use JSearch's `job_required_skills` directly when present (Phase 21).
    Otherwise fall back to Groq extraction from title+description (only when
    Groq is available; never fabricated deterministically).

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


def _is_beginner_user(user_skill_map: dict[str, int]) -> bool:
    if not user_skill_map:
        return True
    return max(user_skill_map.values()) < BEGINNER_PROFICIENCY_CEILING


def _experience_adjustment(opp: dict, is_beginner: bool) -> int:
    """Beginner-priority ranking nudge (Phase 24/41): entry-level/internship
    roles rank slightly higher, senior roles slightly lower, for beginner
    users only. Never hides senior roles outright — just deprioritizes them."""
    if not is_beginner:
        return 0

    title = opp.get("title") or ""
    years = opp.get("experience_years_required")

    if opp.get("type") == "internship" or _BEGINNER_FRIENDLY_PATTERN.search(title):
        return BEGINNER_MATCH_BONUS
    if _SENIOR_PATTERN.search(title) or (isinstance(years, (int, float)) and years >= SENIOR_EXPERIENCE_YEARS):
        return -SENIOR_ROLE_PENALTY
    return 0


def get_recommendations(
    db: Session,
    user_id: UUID,
    opportunity_type: str = "all",
    limit: int = 10,
    min_match: int = 0,
    target_career: Optional[str] = None,
) -> dict[str, Any]:
    """Full pipeline: authenticated user's skills -> career-aware JSearch
    query (India) -> ranked matches.

    Returns a dict matching OpportunityRecommendationsResponse. Degrades
    gracefully on any provider failure — never raises to the caller.
    """
    user_skill_map = get_user_skill_map(db, user_id)

    pool, fetch_failed = _fetch_candidate_pool(target_career, user_skill_map, opportunity_type)

    if opportunity_type != "all":
        pool = [o for o in pool if o["type"] == opportunity_type]

    skill_summary = {
        "skills_used": sorted(user_skill_map.keys()),
        "skill_count": len(user_skill_map),
    }

    if not pool:
        return {
            "recommendations": [],
            "user_skill_summary": skill_summary,
            "source_status": "unavailable" if fetch_failed else "ok",
            "message": UNAVAILABLE_MESSAGE if fetch_failed else "No opportunities found right now.",
        }

    is_beginner = _is_beginner_user(user_skill_map)

    scored = []
    extraction_budget = {"remaining": MAX_SKILL_EXTRACTIONS_PER_REQUEST}
    for opp in pool:
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

        # Experience-suitability nudge only ever applies on top of a real
        # skill match — an opportunity with zero deterministic overlap stays
        # at zero regardless of experience level (Phase 19/23 invariant).
        if final_score > 0:
            final_score += _experience_adjustment(opp, is_beginner)

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
        "message": None,
    }

"""Client for the JSearch API by OpenWeb Ninja (jsearch.p.rapidapi.com) —
the sole source of live job/internship opportunity data for the
recommendation feature.

Only GET /search is used for the recommendation pipeline. JSearch has no
separate "internships" endpoint — a posting is classified as an internship
or a job locally, from provider metadata/title (see
`classify_opportunity_type`), never guessed.

Query construction (career/skill -> search text) lives in
`app.services.opportunity_recommendation`; this module only knows how to
call JSearch and normalize its response into our internal opportunity
shape. Never exposes the RapidAPI key beyond this module — every network
call goes through `_request`, which handles timeouts, retries, and
rate-limit/quota errors without leaking secrets or stack traces to callers.
"""
import logging
import os
import re
import threading
import time
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 15.0
DEFAULT_CACHE_TTL_SECONDS = 3600  # 1 hour — search results don't need to be fresher than that

# RapidAPI plans for opportunity-data providers commonly enforce small request
# quotas. Once a 429 is seen, back off for a while instead of hammering the
# API on every subsequent recommendation request.
DEFAULT_QUOTA_BACKOFF_SECONDS = 3600  # 1 hour

# Confirmed against a live call (2026-08-31): this RapidAPI subscription
# serves /search-v2 — /search 404s with a generic "endpoint does not exist"
# for this account even when fully subscribed and quota is available. If
# this ever needs to change back, /search's envelope is `{"data": [...]}`
# (a bare list) vs. v2's `{"data": {"jobs": [...], "cursor": ...}}` —
# `_extract_list` already handles both shapes defensively.
SEARCH_PATH = "/search-v2"

# India is the platform's default and only supported market for recommendations.
DEFAULT_COUNTRY = "in"
DEFAULT_DATE_POSTED = "month"

_quota_exhausted_until: float = 0.0
_quota_lock = threading.Lock()


class OpportunityProviderError(Exception):
    """Raised when the opportunity provider is unavailable, misconfigured, or rate-limited."""


class _TTLCache:
    """Small in-process cache shared across all users — provider opportunity
    data is the same for everyone, only the per-user skill match differs, so
    this cache must never be keyed by user."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any:
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            expires_at, value = entry
            if time.time() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        with self._lock:
            self._store[key] = (time.time() + ttl_seconds, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


_cache = _TTLCache()


def _get_cache_ttl() -> int:
    try:
        return int(os.getenv("OPPORTUNITY_CACHE_TTL_SECONDS", str(DEFAULT_CACHE_TTL_SECONDS)))
    except ValueError:
        return DEFAULT_CACHE_TTL_SECONDS


def _get_quota_backoff_seconds() -> int:
    try:
        return int(os.getenv("OPPORTUNITY_QUOTA_BACKOFF_SECONDS", str(DEFAULT_QUOTA_BACKOFF_SECONDS)))
    except ValueError:
        return DEFAULT_QUOTA_BACKOFF_SECONDS


def _get_credentials() -> tuple[Optional[str], str]:
    api_key = os.getenv("OPPORTUNITY_RAPIDAPI_KEY", "")
    host = os.getenv("OPPORTUNITY_RAPIDAPI_HOST", "jsearch.p.rapidapi.com")
    return (api_key or None), host


def is_configured() -> bool:
    api_key, _ = _get_credentials()
    return bool(api_key)


def _quota_backoff_remaining() -> float:
    with _quota_lock:
        remaining = _quota_exhausted_until - time.time()
    return remaining if remaining > 0 else 0.0


def _start_quota_backoff() -> None:
    global _quota_exhausted_until
    with _quota_lock:
        _quota_exhausted_until = time.time() + _get_quota_backoff_seconds()


def reset_quota_backoff() -> None:
    """Clear the in-memory quota backoff (used by tests / manual recovery)."""
    global _quota_exhausted_until
    with _quota_lock:
        _quota_exhausted_until = 0.0


def _request(path: str, params: Optional[dict[str, Any]] = None) -> Any:
    """Make a single authenticated GET request to the opportunity provider.

    Retries transient network errors once. Never logs the API key. Raises
    OpportunityProviderError on any failure so callers can degrade gracefully.
    """
    api_key, host = _get_credentials()
    if not api_key:
        raise OpportunityProviderError("Opportunity provider is not configured")

    backoff_remaining = _quota_backoff_remaining()
    if backoff_remaining > 0:
        raise OpportunityProviderError(
            f"Opportunity provider quota exhausted; backing off for {int(backoff_remaining)}s more"
        )

    headers = {
        "x-rapidapi-host": host,
        "x-rapidapi-key": api_key,
    }

    last_error: Optional[Exception] = None
    for attempt in range(2):
        try:
            response = httpx.get(
                f"https://{host}{path}",
                headers=headers,
                params=params or {},
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )

            if response.status_code == 429:
                # Covers both a hard monthly-quota cutoff and short-term burst
                # throttling. Either way, immediate retries won't help — start
                # a cooldown so subsequent calls in this process fail fast.
                logger.warning("Opportunity provider rate limit hit on %s", path)
                _start_quota_backoff()
                raise OpportunityProviderError("Opportunity provider rate limit reached")

            response.raise_for_status()
            return response.json()

        except OpportunityProviderError:
            raise
        except httpx.HTTPStatusError as e:
            logger.warning("Opportunity provider HTTP %s on %s", e.response.status_code, path)
            raise OpportunityProviderError(f"Opportunity provider returned HTTP {e.response.status_code}") from e
        except httpx.TimeoutException as e:
            last_error = e
            logger.warning("Opportunity provider timeout on %s (attempt %d)", path, attempt + 1)
        except Exception as e:
            last_error = e
            logger.warning(
                "Opportunity provider error on %s (attempt %d): %s", path, attempt + 1, type(e).__name__
            )

    raise OpportunityProviderError(
        f"Opportunity provider unreachable after retries: {type(last_error).__name__ if last_error else 'unknown error'}"
    )


def _cached_request(cache_key: str, path: str, params: Optional[dict[str, Any]] = None) -> Any:
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached
    data = _request(path, params)
    _cache.set(cache_key, data, _get_cache_ttl())
    return data


def clear_cache() -> None:
    _cache.clear()
    reset_quota_backoff()


def _extract_list(data: Any) -> list[dict]:
    """JSearch's envelope is {"status", "request_id", "parameters", "data": ...}.
    On /search, `data` is a bare list; on /search-v2 (confirmed live), it's
    `{"jobs": [...], "cursor": ...}`. Unwrap both shapes defensively rather
    than assuming either holds."""
    if isinstance(data, dict):
        value = data.get("data")
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            jobs = value.get("jobs")
            if isinstance(jobs, list):
                return [item for item in jobs if isinstance(item, dict)]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def search(
    query: str,
    *,
    country: str = DEFAULT_COUNTRY,
    date_posted: str = DEFAULT_DATE_POSTED,
    page: int = 1,
    num_pages: int = 1,
) -> list[dict]:
    """One GET /search call (cached per exact parameter set) -> raw JSearch job objects.

    `country` uses JSearch's documented ISO country code parameter for
    server-side location filtering (Phase 7) rather than fetching globally
    and filtering afterward.
    """
    params = {
        "query": query,
        "country": country,
        "date_posted": date_posted,
        "page": str(page),
        "num_pages": str(num_pages),
    }
    cache_key = f"search:{query}:{country}:{date_posted}:{page}:{num_pages}"
    data = _cached_request(cache_key, SEARCH_PATH, params)
    return _extract_list(data)


# --- Normalization -----------------------------------------------------

_INTERN_TITLE_PATTERN = re.compile(r"\bintern(ship)?s?\b", re.IGNORECASE)
_INTERN_EMPLOYMENT_TYPES = {"INTERN"}

_EMPLOYMENT_TYPE_LABELS = {
    "FULLTIME": "Full Time",
    "PARTTIME": "Part Time",
    "CONTRACTOR": "Contract",
    "INTERN": "Internship",
    "TEMPORARY": "Temporary",
}

_INDIA_COUNTRY_CODES = {"IN", "INDIA"}


def _employment_type_enum(raw: dict) -> Optional[str]:
    """`job_employment_types` (confirmed live on /search-v2) is a clean enum
    list (e.g. ["INTERN"]); the singular `job_employment_type` has been
    observed with mangled encoding (e.g. "Full�time") on the same live
    responses, so the list is preferred whenever present."""
    types = raw.get("job_employment_types")
    if isinstance(types, list):
        for t in types:
            if isinstance(t, str) and t.strip():
                return t.strip().upper()
    single = raw.get("job_employment_type")
    if isinstance(single, str) and single.strip():
        return single.strip().upper()
    return None


def classify_opportunity_type(raw: dict) -> str:
    """Classify a JSearch posting as "internship" or "job".

    Only classified as an internship when provider metadata says so
    (employment type enum == "INTERN") or the title unambiguously says so
    (Phase 12) — never inferred from anything softer than that, and never
    defaults to "internship" when unsure.
    """
    if _employment_type_enum(raw) in _INTERN_EMPLOYMENT_TYPES:
        return "internship"
    title = raw.get("job_title")
    if isinstance(title, str) and _INTERN_TITLE_PATTERN.search(title):
        return "internship"
    return "job"


def _format_employment_type(raw: dict) -> Optional[str]:
    key = _employment_type_enum(raw)
    if not key:
        return None
    return _EMPLOYMENT_TYPE_LABELS.get(key, key.replace("_", " ").title())


def _is_india_relevant(raw: dict) -> bool:
    """LEVEL 2 India validation (Phase 17) — reject a posting only when the
    provider explicitly says it's not India. Missing/ambiguous country data
    (common for remote postings) is not rejected, since the search itself is
    already scoped server-side to India (Phase 7)."""
    country = raw.get("job_country")
    if isinstance(country, str) and country.strip():
        return country.strip().upper() in _INDIA_COUNTRY_CODES
    return True


def _fmt_num(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _format_salary(raw: dict) -> Optional[str]:
    """Only ever format salary data the provider actually gave us — never
    invent one (Phase 27). Most India postings disclose no salary at all
    (confirmed live), so this is expected to return None often."""
    min_s = raw.get("job_min_salary")
    max_s = raw.get("job_max_salary")
    if min_s is not None or max_s is not None:
        if min_s is not None and max_s is not None and min_s != max_s:
            amount = f"{_fmt_num(min_s)}-{_fmt_num(max_s)}"
        else:
            amount = _fmt_num(min_s if min_s is not None else max_s)

        currency = raw.get("job_salary_currency")
        if isinstance(currency, str) and currency.strip():
            amount = f"{currency.strip()} {amount}"

        period = raw.get("job_salary_period")
        if isinstance(period, str) and period.strip():
            amount = f"{amount}/{period.strip().lower()}"

        return amount

    # Some responses carry a pre-formatted string or a bare number instead
    # of the structured min/max fields.
    salary_string = raw.get("job_salary_string")
    if isinstance(salary_string, str) and salary_string.strip():
        return salary_string.strip()

    salary_num = raw.get("job_salary")
    if isinstance(salary_num, (int, float)) and salary_num:
        amount = _fmt_num(salary_num)
        currency = raw.get("job_salary_currency")
        if isinstance(currency, str) and currency.strip():
            amount = f"{currency.strip()} {amount}"
        period = raw.get("job_salary_period")
        if isinstance(period, str) and period.strip():
            amount = f"{amount}/{period.strip().lower()}"
        return amount

    return None


def _resolve_experience(raw: dict) -> tuple[Optional[str], Optional[float]]:
    """`job_required_experience` is an object like
    {"required_experience_in_months": int|None, "experience_mentioned": bool,
    "experience_preferred": bool} — never assume it's present or numeric (Phase 24)."""
    req = raw.get("job_required_experience")
    if not isinstance(req, dict):
        return None, None

    months = req.get("required_experience_in_months")
    years: Optional[float] = None
    if isinstance(months, (int, float)) and months > 0:
        years = round(months / 12, 1)

    if years:
        label = f"{years:g}+ years experience"
    elif req.get("experience_mentioned"):
        label = "Experience required"
    else:
        label = None

    return label, years


def _resolve_required_skills(raw: dict) -> list[str]:
    skills = raw.get("job_required_skills")
    if isinstance(skills, list):
        return [s.strip() for s in skills if isinstance(s, str) and s.strip()]
    return []


def _resolve_apply_url(raw: dict) -> Optional[str]:
    """Only ever return a URL the provider actually gave us — never construct one (Phase 34)."""
    link = raw.get("job_apply_link")
    if isinstance(link, str) and link.strip().lower().startswith("http"):
        return link.strip()

    options = raw.get("apply_options")
    if isinstance(options, list):
        for opt in options:
            if isinstance(opt, dict):
                url = opt.get("apply_link")
                if isinstance(url, str) and url.strip().lower().startswith("http"):
                    return url.strip()
    return None


def _resolve_source_domain(raw: dict) -> Optional[str]:
    """Derived from the real apply URL's host — never a claimed/guessed source (Phase 33)."""
    link = _resolve_apply_url(raw)
    if not link:
        return None
    try:
        netloc = urlparse(link).netloc
    except ValueError:
        return None
    return netloc or None


def _resolve_location(raw: dict) -> Optional[str]:
    city = raw.get("job_city")
    state = raw.get("job_state")
    country = raw.get("job_country")
    parts = [p.strip() for p in (city, state) if isinstance(p, str) and p.strip()]
    if parts:
        if isinstance(country, str) and country.strip().upper() in _INDIA_COUNTRY_CODES:
            parts.append("India")
        return ", ".join(parts)

    loc = raw.get("job_location")
    if isinstance(loc, str) and loc.strip():
        return loc.strip()

    if raw.get("job_is_remote") is True:
        return "Remote"

    return None


def _resolve_description(raw: dict) -> str:
    description = raw.get("job_description")
    if not isinstance(description, str):
        description = ""

    highlights = raw.get("job_highlights")
    if isinstance(highlights, dict):
        quals = highlights.get("Qualifications")
        if isinstance(quals, list):
            qual_text = "; ".join(str(q) for q in quals if isinstance(q, str) and q.strip())
            if qual_text:
                description = f"{description}\nQualifications: {qual_text}".strip()

    return description


def normalize_opportunity(raw: dict) -> Optional[dict]:
    """Convert a raw JSearch job object into our internal opportunity shape.

    Returns None for records missing the bare minimum (id + title) or that
    fail the India relevance check, rather than guessing — we never invent
    opportunity data.
    """
    if not isinstance(raw, dict):
        return None

    job_id = raw.get("job_id")
    title = raw.get("job_title")
    if job_id is None or not isinstance(title, str) or not title.strip():
        return None

    if not _is_india_relevant(raw):
        return None

    organization = raw.get("employer_name")
    if not isinstance(organization, str) or not organization.strip():
        organization = "Unknown Organization"

    organization_url = raw.get("employer_website")
    if not isinstance(organization_url, str) or not organization_url.strip().lower().startswith("http"):
        organization_url = None

    logo = raw.get("employer_logo")
    if not isinstance(logo, str) or not logo.strip().lower().startswith("http"):
        logo = None

    remote = raw.get("job_is_remote")
    if not isinstance(remote, bool):
        remote = None

    seniority, experience_years = _resolve_experience(raw)

    return {
        "id": str(job_id),
        "title": title.strip(),
        "organization": organization.strip(),
        "organization_url": organization_url,
        "type": classify_opportunity_type(raw),
        "url": _resolve_apply_url(raw),
        "logo": logo,
        "location": _resolve_location(raw),
        "remote": remote,
        "employment_type": _format_employment_type(raw),
        "seniority": seniority,
        "experience_years_required": experience_years,
        "posted_date": raw.get("job_posted_at_datetime_utc") if isinstance(raw.get("job_posted_at_datetime_utc"), str) else None,
        # JSearch does not supply an explicit expiry field — never invent one;
        # absence means we don't know it's closed, so it stays open (Phase 27/12 precedent).
        "valid_through": None,
        "salary": _format_salary(raw),
        "registration_open": True,
        "required_skills": _resolve_required_skills(raw),
        "description": _resolve_description(raw),
        "source": raw.get("job_publisher") if isinstance(raw.get("job_publisher"), str) else None,
        "source_domain": _resolve_source_domain(raw),
        "country": raw.get("job_country") if isinstance(raw.get("job_country"), str) else None,
    }


def get_opportunities(
    query: str,
    *,
    country: str = DEFAULT_COUNTRY,
    date_posted: str = DEFAULT_DATE_POSTED,
    page: int = 1,
    num_pages: int = 1,
) -> list[dict]:
    """Fetch, normalize, and dedupe opportunities for one search query.

    Exactly one upstream request per distinct query per cache window. Query
    strategy (how many queries, what text) is decided by
    `opportunity_recommendation` — this function just executes one.
    """
    raw_items = search(query, country=country, date_posted=date_posted, page=page, num_pages=num_pages)

    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    seen_fallback: set[tuple[str, str, str]] = set()
    normalized: list[dict] = []

    for raw in raw_items:
        opp = normalize_opportunity(raw)
        if not opp:
            continue
        if opp["id"] in seen_ids:
            continue
        if opp["url"] and opp["url"] in seen_urls:
            continue
        fallback_key = (
            opp["title"].strip().lower(),
            opp["organization"].strip().lower(),
            (opp["location"] or "").strip().lower(),
        )
        if fallback_key in seen_fallback:
            continue

        seen_ids.add(opp["id"])
        if opp["url"]:
            seen_urls.add(opp["url"])
        seen_fallback.add(fallback_key)

        if opp["registration_open"]:
            normalized.append(opp)

    return normalized

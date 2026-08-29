"""Client for the RapidAPI "Internships API" provider (internships-api.p.rapidapi.com)
— the sole source of live internship/job opportunity data for the recommendation
feature.

Two endpoints on the same RapidAPI product:
  - Career Site API (`/active-jb-7d`)  -> internships, sourced from company career sites
  - Job Board API   (`/active-ats-7d`) -> jobs, sourced from job boards

NOTE on this mapping: an earlier round of live testing saw inconsistent
403-vs-429 responses that looked order-dependent rather than endpoint-
dependent. That turned out to be caused by a truncated API key (one
character was dropped when it was copied into `.env`), not a real quota or
subscription issue — once the full key was in place, `/active-jb-7d`
(confirmed independently as the Career Site/internships endpoint) worked as
originally reported. If either endpoint is later found to be swapped, fix it
by changing `INTERNSHIPS_PATH`/`JOBS_PATH` below; nothing else needs to
change. Whichever endpoint is genuinely unreachable, `fetch_*` surfaces that
failure and the recommendation pipeline degrades gracefully for that type
rather than guessing or faking data.

Never exposes the RapidAPI key beyond this module. Every network call goes
through `_request`, which handles timeouts, retries, and rate-limit/quota
errors without leaking secrets or stack traces to callers.
"""
import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_CACHE_TTL_SECONDS = 900  # 15 minutes

# RapidAPI plans for opportunity-data providers commonly enforce small request
# quotas. Once a 429 is seen, back off for a while instead of hammering the
# API on every subsequent recommendation request.
DEFAULT_QUOTA_BACKOFF_SECONDS = 3600  # 1 hour

# Confirmed endpoints on the "Internships API" RapidAPI product (see module
# docstring for how this mapping was verified).
INTERNSHIPS_PATH = "/active-jb-7d"
JOBS_PATH = "/active-ats-7d"

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
    host = os.getenv("OPPORTUNITY_RAPIDAPI_HOST", "internships-api.p.rapidapi.com")
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
        "Content-Type": "application/json",
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
    """This provider's exact envelope shape is not guaranteed to be a bare
    array — unwrap common wrapper patterns defensively."""
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("data", "results", "items", "jobs"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def fetch_internships() -> list[dict]:
    """Career Site API — internship postings from company career sites."""
    data = _cached_request("internships", INTERNSHIPS_PATH)
    return _extract_list(data)


def fetch_jobs() -> list[dict]:
    """Job Board API — job postings from job boards."""
    data = _cached_request("jobs", JOBS_PATH)
    return _extract_list(data)


def _dig(raw: dict, *path: str, default: Any = None) -> Any:
    current: Any = raw
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


def _parse_date(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (ValueError, OSError, OverflowError):
            return None
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(cleaned, fmt)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed
            except ValueError:
                continue
    return None


def _is_still_active(raw: dict) -> bool:
    """An opportunity is only "closed" if its `date_validthrough` has
    demonstrably passed. Missing expiry data means we don't know it's
    expired, so it stays active — we never invent an expiry (Phase 16)."""
    valid_through = _parse_date(raw.get("date_validthrough"))
    if valid_through and valid_through < datetime.now(timezone.utc):
        return False
    return True


def _resolve_location(raw: dict) -> Optional[str]:
    """Prefer the provider's own normalized `locations_derived` field; only
    fall back to the raw (likely schema.org JobPosting-shaped) location data
    on a best-effort basis, never inventing a location."""
    derived = raw.get("locations_derived")
    if isinstance(derived, list) and derived:
        parts = [d for d in derived if isinstance(d, str) and d.strip()]
        if parts:
            return ", ".join(parts[:2])
    if isinstance(derived, str) and derived.strip():
        return derived.strip()

    raw_locations = raw.get("locations_raw")
    if isinstance(raw_locations, list) and raw_locations:
        first = raw_locations[0]
        if isinstance(first, dict):
            address = first.get("address") if isinstance(first.get("address"), dict) else first
            parts = [
                address.get("addressLocality"),
                address.get("addressRegion"),
                address.get("addressCountry"),
            ]
            joined = ", ".join(p for p in parts if isinstance(p, str) and p.strip())
            if joined:
                return joined
        if isinstance(first, str) and first.strip():
            return first.strip()
    if isinstance(raw_locations, str) and raw_locations.strip():
        return raw_locations.strip()

    requirements_raw = raw.get("location_requirements_raw")
    if isinstance(requirements_raw, str) and requirements_raw.strip():
        return requirements_raw.strip()

    return None


def _format_salary(salary_raw: Any) -> Optional[str]:
    """`salary_raw` appears to follow schema.org JobPosting `baseSalary`
    conventions in this provider family. Format it defensively; never guess
    a value that isn't actually present."""
    if isinstance(salary_raw, (str, int, float)):
        return str(salary_raw)
    if isinstance(salary_raw, dict):
        currency = salary_raw.get("currency")
        value = salary_raw.get("value")
        if isinstance(value, dict):
            min_v = value.get("minValue")
            max_v = value.get("maxValue")
            unit = value.get("unitText")
            if min_v is not None or max_v is not None:
                if min_v is not None and max_v is not None and min_v != max_v:
                    amount = f"{min_v}-{max_v}"
                else:
                    amount = str(min_v if min_v is not None else max_v)
                result = " ".join(str(p) for p in (currency, amount) if p)
                if unit:
                    result += f"/{str(unit).lower()}"
                return result or None
    return None


def _resolve_apply_url(raw: dict) -> Optional[str]:
    """Only ever return a URL the provider actually gave us — never construct one."""
    url = raw.get("url")
    if isinstance(url, str) and url.strip().lower().startswith("http"):
        return url.strip()
    return None


def normalize_opportunity(raw: dict, opportunity_type: str) -> Optional[dict]:
    """Convert a raw provider record into our internal Opportunity shape.

    Returns None for records missing the bare minimum (id + title) rather
    than guessing — we never invent opportunity data.
    """
    if not isinstance(raw, dict):
        return None

    ext_id = raw.get("id")
    title = raw.get("title")
    if ext_id is None or not isinstance(title, str) or not title.strip():
        return None

    organization = raw.get("organization")
    if not isinstance(organization, str) or not organization.strip():
        organization = "Unknown Organization"

    organization_url = raw.get("organization_url")
    if not isinstance(organization_url, str) or not organization_url.strip().lower().startswith("http"):
        organization_url = None

    remote = raw.get("remote_derived")
    if not isinstance(remote, bool):
        remote = None

    employment_type = raw.get("employment_type")
    if isinstance(employment_type, list):
        employment_type = ", ".join(str(e) for e in employment_type if e) or None
    elif not isinstance(employment_type, str):
        employment_type = None

    seniority = raw.get("seniority")
    if not isinstance(seniority, str):
        seniority = None

    description = raw.get("description")
    if not isinstance(description, str):
        description = ""

    source = raw.get("source") if isinstance(raw.get("source"), str) else None
    source_domain = raw.get("source_domain") if isinstance(raw.get("source_domain"), str) else None

    return {
        "id": str(ext_id),
        "title": title.strip(),
        "organization": organization.strip(),
        "organization_url": organization_url,
        "type": opportunity_type,
        "url": _resolve_apply_url(raw),
        "logo": raw.get("organization_logo") if isinstance(raw.get("organization_logo"), str) else None,
        "location": _resolve_location(raw),
        "remote": remote,
        "employment_type": employment_type,
        "seniority": seniority,
        "posted_date": raw.get("date_posted") if isinstance(raw.get("date_posted"), str) else None,
        "valid_through": raw.get("date_validthrough") if isinstance(raw.get("date_validthrough"), str) else None,
        "salary": _format_salary(raw.get("salary_raw")),
        "registration_open": _is_still_active(raw),
        "required_skills": [],  # this provider does not supply explicit skills; see opportunity_recommendation's AI fallback
        "description": description,
        "source": source,
        "source_domain": source_domain,
    }


def get_opportunities(opportunity_type: str) -> list[dict]:
    """Fetch, normalize, dedupe, and filter-out-expired opportunities of one type.

    Exactly one upstream request per type per cache window — no role-based
    pre-filtering or multi-call fan-out (that caused quota exhaustion with
    the previous provider).
    """
    fetch_fn = fetch_internships if opportunity_type == "internship" else fetch_jobs
    raw_items = fetch_fn()

    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    normalized: list[dict] = []
    for raw in raw_items:
        opp = normalize_opportunity(raw, opportunity_type)
        if not opp:
            continue
        if opp["id"] in seen_ids:
            continue
        if opp["url"] and opp["url"] in seen_urls:
            continue
        seen_ids.add(opp["id"])
        if opp["url"]:
            seen_urls.add(opp["url"])
        if opp["registration_open"]:
            normalized.append(opp)

    return normalized

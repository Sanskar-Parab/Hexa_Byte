"""Deterministic / fuzzy trainee identity matching engine.

Explainable weighted matching — no ML.

Weights (tunable via env or constants):
  Name similarity         30%
  DOB exact match         30%
  Phone exact match       15%
  Program-ID evidence     25%  (only meaningful when program is the same;
                                for cross-program we use neutral 0.5 so
                                max cross-program score can still reach HIGH)

Thresholds:
  >= 85  → high (auto-link)
  60-84 → medium (admin review)
  < 60  → low (new trainee)

All scores are 0-100 for display, 0-1 internally.
"""
import re
import difflib
import os
from datetime import date
from typing import Optional

# Configurable weights/thresholds — env overrides for easy tuning
NAME_WEIGHT = float(os.getenv("IDENTITY_NAME_WEIGHT", "0.30"))
DOB_WEIGHT = float(os.getenv("IDENTITY_DOB_WEIGHT", "0.30"))
PHONE_WEIGHT = float(os.getenv("IDENTITY_PHONE_WEIGHT", "0.15"))
PROGRAM_WEIGHT = float(os.getenv("IDENTITY_PROGRAM_WEIGHT", "0.25"))

# Normalize if sum != 1.0 (e.g. custom env)
_WEIGHT_SUM = NAME_WEIGHT + DOB_WEIGHT + PHONE_WEIGHT + PROGRAM_WEIGHT
if abs(_WEIGHT_SUM - 1.0) > 1e-6:
    NAME_WEIGHT /= _WEIGHT_SUM
    DOB_WEIGHT /= _WEIGHT_SUM
    PHONE_WEIGHT /= _WEIGHT_SUM
    PROGRAM_WEIGHT /= _WEIGHT_SUM

HIGH_THRESHOLD = float(os.getenv("IDENTITY_HIGH_THRESHOLD", "85"))
MEDIUM_THRESHOLD = float(os.getenv("IDENTITY_MEDIUM_THRESHOLD", "60"))


def normalize_phone(phone: Optional[str]) -> str:
    if not phone:
        return ""
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) > 10:
        digits = digits[-10:]
    return digits


def _normalize_name(name: str) -> str:
    if not name:
        return ""
    # lower, collapse whitespace, strip punctuation other than spaces
    s = name.strip().lower()
    # remove punctuation except spaces
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def name_similarity(a: str, b: str) -> float:
    """Return 0-1 similarity for two names.

    Uses difflib + token subset boost for middle initials.
    Explainable: high when tokens match even if middle initial differs.
    """
    na = _normalize_name(a)
    nb = _normalize_name(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0

    # difflib ratio
    ratio = difflib.SequenceMatcher(None, na, nb).ratio()

    # token subset check (ignore single-letter middle initials)
    ta = na.split()
    tb = nb.split()
    # filtered tokens (len>1)
    fa = {t for t in ta if len(t) > 1}
    fb = {t for t in tb if len(t) > 1}

    if fa and fb:
        # if filtered set of one is subset of the other → strong match
        # e.g. {rahul,sharma} subset of {rahul,sharma} (s removed)
        # Require at least 2 meaningful tokens to avoid false positives
        # (e.g. "A Sharma" {sharma} subset of "Amit Sharma" should NOT boost)
        if (fa.issubset(fb) or fb.issubset(fa)) and min(len(fa), len(fb)) >= 2:
            # boost to at least 0.92 but keep difflib if higher
            return max(ratio, 0.92)
        # Jaccard
        inter = len(fa & fb)
        union = len(fa | fb)
        jacc = inter / union if union else 0.0
        # return max of ratio and jacc (jacc may be lower for "Rahul Sharma" vs "Rahul S Sharma" -> 0.66)
        # but we already handled subset, so plain max
        return max(ratio, jacc)

    return ratio


def dob_score(dob_a: Optional[date], dob_b: Optional[date]) -> float:
    if not dob_a or not dob_b:
        return 0.0
    return 1.0 if dob_a == dob_b else 0.0


def phone_score(phone_a: Optional[str], phone_b: Optional[str]) -> float:
    na = normalize_phone(phone_a)
    nb = normalize_phone(phone_b)
    if not na or not nb:
        return 0.0
    return 1.0 if na == nb else 0.0

def phone_score_against_list(phone_incoming: Optional[str], phone_list: list[str]) -> float:
    """Score incoming phone against any phone in master's list."""
    if not phone_incoming or not phone_list:
        return 0.0
    inc = normalize_phone(phone_incoming)
    if not inc:
        return 0.0
    for p in phone_list:
        if normalize_phone(p) == inc:
            return 1.0
    return 0.0


def program_score(
    prog_a: Optional[str],
    prog_id_a: Optional[str],
    prog_b: Optional[str],
    prog_id_b: Optional[str],
) -> float:
    """Program-ID evidence score 0-1.

    Rules:
    - Same program + same ID → 1.0 (duplicate — very strong, but UI should block duplicate anyway)
    - Same program + different ID → 0.0 (same program should have consistent ID if same person; different ID suggests different person)
    - Different program → 0.5 (neutral — IDs are not globally comparable, don't penalize)
    - Missing program info → 0.5 neutral
    """
    if not prog_a or not prog_b:
        return 0.5
    pa = prog_a.strip().lower()
    pb = prog_b.strip().lower()
    if pa == pb:
        # same program: compare IDs
        ida = (prog_id_a or "").strip().lower()
        idb = (prog_id_b or "").strip().lower()
        if not ida or not idb:
            return 0.5
        return 1.0 if ida == idb else 0.0
    else:
        # cross-program: IDs not comparable
        return 0.5


def compute_match(
    incoming_name: str,
    incoming_dob: date,
    incoming_phone: Optional[str],
    incoming_program: str,
    incoming_program_id: str,
    master,  # MasterTrainee
    master_program_records: Optional[list] = None,
) -> dict:
    """Compute match of incoming record against a single MasterTrainee.

    Returns dict with score 0-100 and field breakdown.
    """
    # master fields
    master_name = getattr(master, "primary_name", "") or ""
    master_dob = getattr(master, "dob", None)
    master_phones = []
    try:
        master_phones = master.get_phone_numbers() if hasattr(master, "get_phone_numbers") else []
    except Exception:
        master_phones = []

    # field scores 0-1
    n_score = name_similarity(incoming_name or "", master_name)
    d_score = dob_score(incoming_dob, master_dob)
    p_score = phone_score_against_list(incoming_phone, master_phones)
    # For program: compare incoming vs any existing enrollment's program? For master we compare against all
    # If master has multiple enrollments, use best (max) program score? Actually neutral across programs will be 0.5 anyway.
    # To be conservative, we compute program score against the existing enrollments;
    # if any enrollment is same program + same ID -> 1, if same program different ID -> 0, else neutral 0.5.
    # We'll take the maximum program score (most favorable) if multiple, but if any same-program mismatch we should consider 0?
    # For cross-program case (most common), all will be 0.5 => 0.5.
    # For duplicate prevention, if incoming same program same ID exists, score will be high but duplicate check will block earlier.
    if master_program_records is not None and len(master_program_records) > 0:
        # compute program score vs each record and take best? For same program mismatch, we want to penalize, so we should take min? Let's reason:
        # If incoming PMKVY vs master has PMKVY and DDU-GKY records, incoming PMKVY same program should be compared to PMKVY record only.
        # Taking max across all would incorrectly allow DDU record to give neutral 0.5 and hide same-program mismatch 0.
        # So compute program score ONLY against records with same program name, if any.
        same_program_scores = []
        neutral_scores = []
        for rec in master_program_records:
            rp = getattr(rec, "program_name", None)
            ri = getattr(rec, "program_trainee_id", None)
            sc = program_score(incoming_program, incoming_program_id, rp, ri)
            if rp and rp.strip().lower() == (incoming_program or "").strip().lower():
                same_program_scores.append(sc)
            else:
                neutral_scores.append(sc)
        if same_program_scores:
            # if same program exists, use its score (if multiple same program, take max)
            prog_score = max(same_program_scores)
        elif neutral_scores:
            prog_score = neutral_scores[0]  # 0.5
        else:
            prog_score = 0.5
    else:
        # no enrollments yet — neutral
        prog_score = 0.5

    weighted = (n_score * NAME_WEIGHT) + (d_score * DOB_WEIGHT) + (p_score * PHONE_WEIGHT) + (prog_score * PROGRAM_WEIGHT)
    overall = round(weighted * 100, 2)

    # confidence bucket
    if overall >= HIGH_THRESHOLD:
        confidence = "high"
    elif overall >= MEDIUM_THRESHOLD:
        confidence = "medium"
    else:
        confidence = "low"

    # Safety: never auto-link on name alone or phone alone without DOB
    # If DOB mismatches (0) then max possible = NAME+PHONE+PROGRAM = 30+15+25=70 => medium at best, not high
    # If name very low (<0.5) but DOB+phone match, we should not auto-link either: require name >=0.6 for high
    # Enforce: high requires dob_match==1 and name >=0.7 (explainable)
    # This prevents false positives from name-only or phone-only
    if confidence == "high":
        if d_score != 1.0 or n_score < 0.7:
            confidence = "medium"
            # cap score to just below high to force review
            overall = min(overall, HIGH_THRESHOLD - 0.01)

    return {
        "match_score": overall,
        "confidence": confidence,
        "field_scores": {
            "name": round(n_score, 4),
            "dob": round(d_score, 4),
            "phone": round(p_score, 4),
            "program": round(prog_score, 4),
        },
        "field_weights": {
            "name": NAME_WEIGHT,
            "dob": DOB_WEIGHT,
            "phone": PHONE_WEIGHT,
            "program": PROGRAM_WEIGHT,
        },
        "master_id": str(getattr(master, "id", "")),
        "master_code": getattr(master, "master_code", None),
    }


def find_best_match(incoming_data: dict, masters: list, db) -> Optional[dict]:
    """Find best matching master for incoming_data.

    incoming_data keys: name, dob, phone, program_name, program_trainee_id
    Returns best match dict or None if no masters.
    """
    if not masters:
        return None

    # Need to fetch program records per master for accurate program scoring
    from app.models.trainee_identity import TraineeProgramRecord
    best = None
    for m in masters:
        records = db.query(TraineeProgramRecord).filter(TraineeProgramRecord.master_trainee_id == m.id).all()
        res = compute_match(
            incoming_name=incoming_data.get("name") or incoming_data.get("trainee_name") or "",
            incoming_dob=incoming_data.get("dob"),
            incoming_phone=incoming_data.get("phone"),
            incoming_program=incoming_data.get("program_name") or incoming_data.get("program") or "",
            incoming_program_id=incoming_data.get("program_trainee_id") or incoming_data.get("programTraineeId") or "",
            master=m,
            master_program_records=records,
        )
        res["_master"] = m
        res["_records"] = records
        if best is None or res["match_score"] > best["match_score"]:
            best = res
    return best


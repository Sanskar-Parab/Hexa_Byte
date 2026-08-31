import json
import logging
import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.job_analysis import JobAnalysis
from app.models.skill import Skill, UserSkill
from app.models.skill_evidence import SkillEvidence
from app.services.evidence_service import create_evidence

logger = logging.getLogger(__name__)

# Common tech keywords to detect in job descriptions
TECH_KEYWORDS = [
    "javascript", "typescript", "python", "java", "c++", "c#", "go", "rust", "ruby",
    "php", "swift", "kotlin", "scala", "r", "matlab", "sql", "html", "css",
    "react", "angular", "vue", "svelte", "next.js", "node.js", "express",
    "django", "flask", "fastapi", "spring", "rails", "laravel",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
    "git", "github", "gitlab", "bitbucket",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "dynamodb",
    "graphql", "rest", "api", "microservices",
    "machine learning", "deep learning", "tensorflow", "pytorch", "nlp",
    "figma", "sketch", "adobe", "photoshop",
    "agile", "scrum", "jira", "confluence",
    "linux", "bash", "shell",
]

# Education keywords
EDUCATION_KEYWORDS = [
    "bachelor", "master", "phd", "doctorate", "degree", "bs ", "ms ", "b.s.", "m.s.",
    "b.tech", "m.tech", "bca", "mca", "mba", "associate",
]


def parse_job_description(raw_text: str) -> dict:
    """Parse a job description into structured fields.

    Uses heuristic detection for sections, requirements, and technologies.
    """
    lines = raw_text.split("\n")
    result = {
        "job_title": _extract_title(lines),
        "required_skills": [],
        "preferred_skills": [],
        "experience_required": _extract_experience(raw_text),
        "education_required": _extract_education(raw_text),
        "responsibilities": [],
        "technologies": [],
    }

    # Determine section boundaries
    current_section = None
    in_required = False
    in_preferred = False
    in_responsibilities = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        lower = stripped.lower().rstrip(":")

        # Detect section headers
        if any(kw in lower for kw in ["requirement", "required", "qualification", "must have", "you should have"]):
            current_section = "required"
            in_required = True
            in_preferred = False
            in_responsibilities = False
            continue
        if any(kw in lower for kw in ["prefer", "nice to have", "bonus", "ideal candidate", "plus"]):
            current_section = "preferred"
            in_preferred = True
            in_required = False
            in_responsibilities = False
            continue
        if any(kw in lower for kw in ["responsibilit", "what you", "role", "you will", "day-to-day", "about the"]):
            current_section = "responsibilities"
            in_responsibilities = True
            in_required = False
            in_preferred = False
            continue
        if any(kw in lower for kw in ["about us", "about company", "benefit", "perks", "offer"]):
            current_section = None
            in_required = False
            in_preferred = False
            in_responsibilities = False
            continue

        # Collect content based on current section
        cleaned = re.sub(r'^[\-\*\•\◦\▪\►\→\>]+\s*', '', stripped)
        cleaned = re.sub(r'^\d+[\.\)]\s*', '', cleaned)

        if not cleaned or len(cleaned) > 300:
            continue

        if in_required:
            result["required_skills"].append(cleaned)
        elif in_preferred:
            result["preferred_skills"].append(cleaned)
        elif in_responsibilities:
            result["responsibilities"].append(cleaned)

    # Extract technologies from full text
    result["technologies"] = _extract_technologies(raw_text)

    # If no required skills found via sections, try to extract from full text
    if not result["required_skills"]:
        result["required_skills"] = _extract_skills_from_bullets(lines)

    return result


def _extract_title(lines: list[str]) -> str:
    """Extract job title from the first meaningful lines."""
    for line in lines[:10]:
        stripped = line.strip()
        if not stripped or len(stripped) > 100:
            continue
        # Skip common non-title patterns
        lower = stripped.lower()
        if any(kw in lower for kw in ["posted", "location", "remote", "full-time", "part-time", "contract"]):
            continue
        return stripped
    return "Unknown Position"


def _extract_experience(text: str) -> str | None:
    """Extract experience requirements from text."""
    patterns = [
        r'(\d+[\+\-\s]*(?:to|-)\s*\d+\+?\s*years?\s*(?:of\s+)?(?:experience|exp))',
        r'(\d+\+?\s*years?\s*(?:of\s+)?(?:experience|exp))',
        r'(?:minimum|at least|requir\w*)\s*(\d+\+?\s*years?)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def _extract_education(text: str) -> str | None:
    """Extract education requirements from text."""
    text_lower = text.lower()
    for kw in EDUCATION_KEYWORDS:
        if kw in text_lower:
            # Find the surrounding context
            idx = text_lower.index(kw)
            start = max(0, idx - 30)
            end = min(len(text), idx + 60)
            context = text[start:end].strip()
            # Clean up
            context = re.sub(r'\s+', ' ', context)
            return context
    return None


def _extract_technologies(text: str) -> list[str]:
    """Extract technology mentions from text."""
    text_lower = text.lower()
    found = []
    for tech in TECH_KEYWORDS:
        pattern = r'\b' + re.escape(tech) + r'\b'
        if re.search(pattern, text_lower):
            found.append(tech)
    return found


def _extract_skills_from_bullets(lines: list[str]) -> list[str]:
    """Extract skill-like bullet points from lines."""
    skills = []
    for line in lines:
        stripped = line.strip()
        cleaned = re.sub(r'^[\-\*\•\◦\▪\►\→\>]+\s*', '', stripped)
        cleaned = re.sub(r'^\d+[\.\)]\s*', '', cleaned)
        if cleaned and len(cleaned) < 150 and len(cleaned) > 3:
            # Heuristic: if it mentions tech keywords or is short, treat as skill
            lower = cleaned.lower()
            if any(tech in lower for tech in TECH_KEYWORDS[:20]):
                skills.append(cleaned)
    return skills[:20]  # Cap at 20


def match_job_to_user(db: Session, user_id: UUID, job_data: dict) -> dict:
    """Compare job requirements against user's actual evidence.

    IMPORTANT: This function creates evidence about job requirements
    but must NOT create evidence that the user possesses skills they don't have.
    """
    # Get all user skills with proficiency
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    all_skills = {s.id: s for s in db.query(Skill).all()}

    user_skill_map = {}
    for us in user_skills:
        skill = all_skills.get(us.skill_id)
        if skill:
            user_skill_map[skill.name.lower()] = {
                "skill_id": str(us.skill_id),
                "proficiency": us.proficiency,
                "confidence": us.confidence or "LOW",
            }

    # Get evidence counts per skill
    evidence_records = db.query(SkillEvidence).filter(
        SkillEvidence.user_id == user_id,
    ).all()
    evidence_by_skill = {}
    for ev in evidence_records:
        skill = all_skills.get(ev.skill_id)
        if skill:
            evidence_by_skill.setdefault(skill.name.lower(), []).append(ev)

    strong = []
    developing = []
    missing = []
    not_demonstrated = []

    required_skills = job_data.get("required_skills", [])
    total_required = len(required_skills)

    for req in required_skills:
        # Try to match the requirement text to a known skill
        matched = _match_requirement_to_skill(req, user_skill_map, all_skills)

        if matched:
            skill_info = user_skill_map.get(matched["skill_name"].lower(), {})
            proficiency = skill_info.get("proficiency", 0)
            confidence = skill_info.get("confidence", "LOW")
            ev_count = len(evidence_by_skill.get(matched["skill_name"].lower(), []))

            item = {
                "skill_name": matched["skill_name"],
                "user_proficiency": proficiency,
                "confidence": confidence,
                "evidence_count": ev_count,
                "is_required": True,
            }

            if proficiency >= 4:
                item["status"] = "strong"
                strong.append(item)
            elif proficiency >= 1:
                item["status"] = "developing"
                developing.append(item)
            else:
                item["status"] = "not_demonstrated"
                not_demonstrated.append(item)
        else:
            # Skill not found in user profile at all
            missing.append({
                "skill_name": req[:80],
                "user_proficiency": 0,
                "confidence": None,
                "evidence_count": 0,
                "is_required": True,
                "status": "missing",
            })

    # Compute alignment
    if total_required > 0:
        alignment = (len(strong) * 1.0 + len(developing) * 0.5) / total_required * 100
    else:
        alignment = 0.0

    # Find top gap (first missing or not_demonstrated)
    top_gap = None
    for item in missing + not_demonstrated:
        top_gap = item["skill_name"]
        break

    # Suggest next action. A 0% alignment from zero detected requirements means
    # extraction failed, not that the user is unqualified — don't let it fall
    # through to _suggest_next_action's empty-lists case, which claims the
    # user "appears well-qualified" (contradicting the 0% shown alongside it).
    if total_required == 0:
        next_action = (
            "We couldn't detect specific requirements from this posting. "
            "Try pasting the full description with bullet-pointed requirements."
        )
    else:
        next_action = _suggest_next_action(strong, developing, missing, not_demonstrated)

    return {
        "alignment_percentage": round(alignment, 1),
        "strong_skills": strong,
        "developing_skills": developing,
        "missing_skills": missing,
        "not_demonstrated": not_demonstrated,
        "top_gap": top_gap,
        "next_action": next_action,
        "required_skills_count": total_required,
        "matched_count": len(strong) + len(developing),
    }


def _match_requirement_to_skill(
    requirement: str,
    user_skill_map: dict,
    all_skills: dict,
) -> dict | None:
    """Try to match a job requirement to a known skill name."""
    req_lower = requirement.lower()

    # Direct match against user skills
    for skill_name in user_skill_map:
        if skill_name in req_lower or req_lower in skill_name:
            return {"skill_name": all_skills[UUID(user_skill_map[skill_name]["skill_id"])].name if user_skill_map[skill_name].get("skill_id") else skill_name}

    # Match against all known skills
    for skill in all_skills.values():
        if skill.name.lower() in req_lower or req_lower in skill.name.lower():
            if skill.name.lower() in user_skill_map:
                return {"skill_name": skill.name}

    # Check for partial matches (e.g., "React.js" matches "React")
    for skill_name in user_skill_map:
        base_name = skill_name.split(".")[0].split(" ")[0]
        if base_name and base_name in req_lower:
            skill_id = user_skill_map[skill_name].get("skill_id")
            if skill_id:
                skill = all_skills.get(UUID(skill_id))
                if skill:
                    return {"skill_name": skill.name}

    for skill in all_skills.values():
        base_name = skill.name.lower().split(".")[0].split(" ")[0]
        if base_name and base_name in req_lower:
            if skill.name.lower() in user_skill_map:
                return {"skill_name": skill.name}

    return None


def _suggest_next_action(
    strong: list,
    developing: list,
    missing: list,
    not_demonstrated: list,
) -> str:
    """Suggest the most impactful next action based on the match analysis."""
    if missing:
        return f"Build a project demonstrating {missing[0]['skill_name']}"
    if not_demonstrated:
        return f"Assess your {not_demonstrated[0]['skill_name']} proficiency"
    if developing:
        return f"Advance {developing[0]['skill_name']} from developing to strong"
    return "You appear well-qualified for this role"


def create_job_evidence(
    db: Session,
    user_id: UUID,
    job_data: dict,
    matched_skills: list[dict],
) -> int:
    """Create evidence for skills the user HAS that match the job.

    IMPORTANT: Only creates evidence for skills the user actually possesses.
    Does NOT create evidence for missing skills.
    """
    all_skills = {s.name.lower(): s for s in db.query(Skill).all()}
    evidence_count = 0

    for item in matched_skills:
        if item["status"] in ("strong", "developing"):
            skill_name = item["skill_name"].lower()
            skill = all_skills.get(skill_name)
            if not skill:
                continue

            # Check if user has this skill
            user_skill = db.query(UserSkill).filter(
                UserSkill.user_id == user_id,
                UserSkill.skill_id == skill.id,
            ).first()
            if not user_skill:
                continue

            create_evidence(
                db=db,
                user_id=user_id,
                skill_id=skill.id,
                source_type="job",
                title=f"Job Match: {job_data.get('job_title', 'Unknown')}",
                description=f"Skill required in job posting — {item['skill_name']}",
                score=None,
                metadata={
                    "job_title": job_data.get("job_title", ""),
                    "proficiency": item["user_proficiency"],
                },
            )
            evidence_count += 1

    db.commit()
    return evidence_count


def save_job_analysis(
    db: Session,
    user_id: UUID,
    job_data: dict,
    raw_text: str,
    match_result: dict | None = None,
) -> JobAnalysis:
    """Save a job analysis record."""
    analysis = JobAnalysis(
        user_id=user_id,
        job_title=job_data.get("job_title", "Unknown"),
        raw_text=raw_text,
        required_skills=json.dumps(job_data.get("required_skills", [])),
        preferred_skills=json.dumps(job_data.get("preferred_skills", [])),
        experience_required=job_data.get("experience_required"),
        education_required=job_data.get("education_required"),
        responsibilities=json.dumps(job_data.get("responsibilities", [])),
        technologies=json.dumps(job_data.get("technologies", [])),
        match_result=json.dumps(match_result) if match_result else None,
    )
    db.add(analysis)
    db.commit()
    return analysis


def get_job_analyses_for_user(db: Session, user_id: UUID) -> list[JobAnalysis]:
    """Get all job analyses for a user."""
    return db.query(JobAnalysis).filter(
        JobAnalysis.user_id == user_id,
    ).order_by(JobAnalysis.created_at.desc()).all()


def get_job_analysis_by_id(db: Session, user_id: UUID, analysis_id: UUID) -> JobAnalysis | None:
    """Get a specific job analysis by ID."""
    return db.query(JobAnalysis).filter(
        JobAnalysis.id == analysis_id,
        JobAnalysis.user_id == user_id,
    ).first()


def delete_job_analysis(db: Session, user_id: UUID, analysis_id: UUID) -> bool:
    """Delete a job analysis record."""
    analysis = get_job_analysis_by_id(db, user_id, analysis_id)
    if not analysis:
        return False
    db.delete(analysis)
    db.commit()
    return True

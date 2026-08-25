import io
import json
import logging
import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.models.skill import Skill, UserSkill
from app.services.evidence_service import create_evidence

logger = logging.getLogger(__name__)

# Section headers for resume parsing
SECTION_HEADERS = {
    "skills": ["skills", "technical skills", "core competencies", "competencies", "proficiencies"],
    "experience": ["experience", "work experience", "professional experience", "employment", "work history"],
    "education": ["education", "academic background", "academic record", "qualifications"],
    "projects": ["projects", "personal projects", "key projects", "project experience"],
    "certifications": ["certifications", "certificates", "licenses", "credentials"],
    "technologies": ["technologies", "tech stack", "technology"],
    "tools": ["tools", "software", "applications", "platforms"],
}


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file using PyPDF2."""
    from PyPDF2 import PdfReader

    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def parse_resume_text(raw_text: str) -> dict:
    """Parse resume text into structured sections using heuristic header detection.

    Returns dict with keys: skills, projects, experience, education,
    certifications, technologies, tools.
    """
    lines = raw_text.split("\n")
    sections = {key: [] for key in SECTION_HEADERS}
    current_section = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        lower = stripped.lower().rstrip(":").rstrip()

        # Check if this line is a section header
        matched_section = None
        for section_key, headers in SECTION_HEADERS.items():
            for header in headers:
                if lower == header or lower == header + ":":
                    matched_section = section_key
                    break
            if matched_section:
                break

        if matched_section:
            current_section = matched_section
            continue

        # If we're in a section, collect content
        if current_section:
            # Skip empty lines and overly long lines (likely paragraphs, not list items)
            if len(stripped) > 200:
                continue
            # Remove leading bullet characters
            cleaned = re.sub(r'^[\-\*\•\◦\▪\►\→\>]+\s*', '', stripped)
            cleaned = re.sub(r'^\d+[\.\)]\s*', '', cleaned)
            if cleaned:
                sections[current_section].append(cleaned)

    return sections


def extract_skills_from_text(raw_text: str, all_skills: list[Skill]) -> list[dict]:
    """Cross-reference resume text against known skills in the database.

    Returns list of {skill_name, skill_id, context} for matches.
    This is EVIDENCE, not proof of proficiency.
    """
    text_lower = raw_text.lower()
    matches = []

    for skill in all_skills:
        name_lower = skill.name.lower()
        # Check if skill name appears in text (word boundary aware)
        pattern = r'\b' + re.escape(name_lower) + r'\b'
        if re.search(pattern, text_lower):
            # Find the surrounding context (line where it appears)
            context = _find_context(raw_text, skill.name)
            matches.append({
                "skill_name": skill.name,
                "skill_id": str(skill.id),
                "context": context,
            })

    return matches


def _find_context(text: str, term: str) -> str:
    """Find the line containing the term and return it as context."""
    for line in text.split("\n"):
        if term.lower() in line.lower():
            cleaned = line.strip()
            if len(cleaned) > 150:
                cleaned = cleaned[:150] + "..."
            return cleaned
    return f"Mentioned in resume"


def save_resume_and_create_evidence(
    db: Session,
    user_id: UUID,
    filename: str,
    raw_text: str,
    extraction: dict,
    matched_skills: list[dict],
) -> Resume:
    """Save resume record and create evidence for matched skills.

    Resume mentions are EVIDENCE with MEDIUM confidence.
    They are NOT proof of expert proficiency.
    """
    resume = Resume(
        user_id=user_id,
        filename=filename,
        raw_text=raw_text,
        skills=json.dumps(extraction.get("skills", [])),
        projects=json.dumps(extraction.get("projects", [])),
        experience=json.dumps(extraction.get("experience", [])),
        education=json.dumps(extraction.get("education", [])),
        certifications=json.dumps(extraction.get("certifications", [])),
        technologies=json.dumps(extraction.get("technologies", [])),
        tools=json.dumps(extraction.get("tools", [])),
        matched_skills=json.dumps(matched_skills),
    )
    db.add(resume)
    db.flush()

    evidence_count = 0
    for match in matched_skills:
        skill_id = UUID(match["skill_id"])
        # Check if user already has this skill
        user_skill = db.query(UserSkill).filter(
            UserSkill.user_id == user_id,
            UserSkill.skill_id == skill_id,
        ).first()

        if not user_skill:
            # Create user skill with proficiency 1 (detected, not proven)
            user_skill = UserSkill(
                user_id=user_id,
                skill_id=skill_id,
                proficiency=1,
                level_name="Detected",
                confidence="LOW",
            )
            db.add(user_skill)
            db.flush()

        # Create resume evidence (MEDIUM confidence)
        create_evidence(
            db=db,
            user_id=user_id,
            skill_id=skill_id,
            source_type="resume",
            title=f"Resume: {filename}",
            description=f"Skill mentioned in resume — {match.get('context', 'mentioned')}",
            score=None,
            metadata={
                "filename": filename,
                "context": match.get("context", ""),
            },
        )
        evidence_count += 1

    db.commit()
    return resume


def get_resumes_for_user(db: Session, user_id: UUID) -> list[Resume]:
    """Get all resumes for a user."""
    return db.query(Resume).filter(
        Resume.user_id == user_id,
    ).order_by(Resume.created_at.desc()).all()


def get_resume_by_id(db: Session, user_id: UUID, resume_id: UUID) -> Resume | None:
    """Get a specific resume by ID."""
    return db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id,
    ).first()


def delete_resume(db: Session, user_id: UUID, resume_id: UUID) -> bool:
    """Delete a resume record."""
    resume = get_resume_by_id(db, user_id, resume_id)
    if not resume:
        return False
    db.delete(resume)
    db.commit()
    return True

import json
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.career import Career
from app.models.roadmap import Roadmap, RoadmapPhase
from app.models.skill import UserSkill, Skill
from app.services.skill_gap import analyze_skill_gaps

MASTER_SYSTEM_PROMPT = """You are PathPilot AI, an expert career guidance system for students and professionals in India.

Your role is to generate personalized learning roadmaps based on:
1. The user's current skill level and gaps
2. The target career's requirements
3. Realistic timelines for skill development
4. Progressive learning that builds foundations first

IMPORTANT RULES:
- Be specific and actionable
- Include concrete project ideas
- Set realistic timeframes (weeks, not months for each phase)
- Focus on in-demand skills for the Indian job market
- Include both technical and soft skill development
- Make each phase have clear completion criteria
- Prioritize skills by career importance

You must respond with valid JSON matching this exact schema:
{
  "summary": "Brief overview of the roadmap",
  "phases": [
    {
      "phase_number": 1,
      "title": "Phase title",
      "objective": "What you'll achieve",
      "skills": ["skill1", "skill2"],
      "activities": ["activity1", "activity2"],
      "project": "Hands-on project description",
      "duration_weeks": 4,
      "completion_criteria": ["criteria1", "criteria2"]
    }
  ]
}

Generate 4-6 phases that progressively build skills from current level to career-ready."""


def _generate_deterministic_roadmap(
    career: Career,
    skill_gaps: dict[str, Any],
    user_name: str,
) -> dict[str, Any]:
    gaps = skill_gaps.get("gaps", [])
    learning_sequence = career.learning_sequence or []

    if learning_sequence:
        phases = []
        for i, seq in enumerate(learning_sequence[:6], 1):
            phase_gaps = [g for g in gaps if g["skill"] in seq.get("skills", [])]
            duration = max(2, min(8, len(phase_gaps) * 2 + 2))

            phases.append({
                "phase_number": i,
                "title": seq.get("title", f"Phase {i}"),
                "objective": seq.get("objective", f"Learn {', '.join(seq.get('skills', []))}"),
                "skills": seq.get("skills", []),
                "activities": [
                    f"Complete tutorials and documentation for each skill",
                    f"Practice with coding challenges",
                    f"Build small exercises for each concept",
                ],
                "project": seq.get("project", f"Build a project demonstrating {', '.join(seq.get('skills', [])[:2])}"),
                "duration_weeks": duration,
                "completion_criteria": [
                    f"Demonstrate proficiency in each skill",
                    f"Complete the project successfully",
                    f"Pass self-assessment quiz",
                ],
            })
    else:
        skill_groups = []
        group = []
        for gap in gaps:
            group.append(gap["skill"])
            if len(group) >= 3:
                skill_groups.append(group)
                group = []
        if group:
            skill_groups.append(group)

        phases = []
        for i, skills in enumerate(skill_groups[:6], 1):
            duration = max(2, min(6, len(skills) * 2))
            phases.append({
                "phase_number": i,
                "title": f"Master {skills[0]} and Related Skills",
                "objective": f"Build foundational knowledge in {', '.join(skills)}",
                "skills": skills,
                "activities": [
                    f"Study core concepts of {skills[0]}",
                    "Complete hands-on exercises",
                    "Read documentation and best practices",
                ],
                "project": f"Build a small project using {skills[0]}",
                "duration_weeks": duration,
                "completion_criteria": [
                    f"Complete all learning activities for {', '.join(skills)}",
                    "Build and deploy the project",
                    "Document learnings",
                ],
            })

    return {
        "summary": f"Personalized roadmap for {career.name} - {len(phases)} phases covering {len(gaps)} skill gaps",
        "phases": phases,
    }


async def generate_roadmap(
    db: Session,
    user_id: UUID,
    career_id: UUID,
    user_name: str = "User",
    use_ai: bool = False,
) -> dict[str, Any]:
    career = db.query(Career).filter(Career.id == career_id).first()
    if not career:
        return {"error": "Career not found"}

    skill_gaps = analyze_skill_gaps(db, user_id, career_id)

    if use_ai:
        try:
            from app.ai.client import AIClient
            ai = AIClient()
            if ai.is_available:
                user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
                all_skills = {s.id: s for s in db.query(Skill).all()}

                user_skill_details = []
                for us in user_skills:
                    s = all_skills.get(us.skill_id)
                    if s:
                        user_skill_details.append({"name": s.name, "level": us.proficiency})

                prompt = f"""Generate a personalized learning roadmap for {user_name}.

Target Career: {career.name}
Career Description: {career.description}

Current Skills: {json.dumps(user_skill_details)}

Skill Gaps (prioritized): {json.dumps([{"skill": g["skill"], "gap": g["gap_size"], "importance": g["importance"]} for g in skill_gaps.get("gaps", [])[:10]])}

Career Learning Sequence: {json.dumps(career.learning_sequence or [])}

Generate a comprehensive roadmap with 4-6 phases."""

                response = await ai.generate_roadmap(prompt)
                if response:
                    validated = ai.validate_roadmap_response(response)
                    if validated:
                        roadmap_data = validated
                    else:
                        roadmap_data = _generate_deterministic_roadmap(career, skill_gaps, user_name)
                else:
                    roadmap_data = _generate_deterministic_roadmap(career, skill_gaps, user_name)
            else:
                roadmap_data = _generate_deterministic_roadmap(career, skill_gaps, user_name)
        except Exception:
            roadmap_data = _generate_deterministic_roadmap(career, skill_gaps, user_name)
    else:
        roadmap_data = _generate_deterministic_roadmap(career, skill_gaps, user_name)

    existing = db.query(Roadmap).filter(
        Roadmap.user_id == user_id,
        Roadmap.career_id == career_id,
    ).first()
    if existing:
        db.query(RoadmapPhase).filter(RoadmapPhase.roadmap_id == existing.id).delete()
        db.delete(existing)
        db.flush()

    roadmap = Roadmap(
        user_id=user_id,
        career_id=career_id,
        summary=roadmap_data.get("summary", ""),
    )
    db.add(roadmap)
    db.flush()

    for phase_data in roadmap_data.get("phases", []):
        phase = RoadmapPhase(
            roadmap_id=roadmap.id,
            phase_number=phase_data.get("phase_number", 0),
            title=phase_data.get("title", ""),
            objective=phase_data.get("objective", ""),
            skills=phase_data.get("skills", []),
            activities=phase_data.get("activities", []),
            project=phase_data.get("project", ""),
            duration_weeks=phase_data.get("duration_weeks", 4),
            completion_criteria=phase_data.get("completion_criteria", []),
        )
        db.add(phase)

    db.commit()
    db.refresh(roadmap)

    return {
        "id": str(roadmap.id),
        "career_id": str(roadmap.career_id),
        "career_name": career.name,
        "summary": roadmap.summary,
        "phases": [
            {
                "id": str(p.id),
                "phase_number": p.phase_number,
                "title": p.title,
                "objective": p.objective,
                "skills": p.skills,
                "activities": p.activities,
                "project": p.project,
                "duration_weeks": p.duration_weeks,
                "completion_criteria": p.completion_criteria,
                "status": p.status,
            }
            for p in sorted(roadmap.phases, key=lambda x: x.phase_number)
        ],
        "created_at": str(roadmap.created_at),
    }

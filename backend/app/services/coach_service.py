import json
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.profile import Profile
from app.models.skill import Skill, UserSkill
from app.models.interest import Interest, UserInterest
from app.models.assessment import UserAssessment
from app.models.career import Career, CareerRecommendation
from app.models.roadmap import Roadmap, RoadmapPhase
from app.models.skill_evidence import SkillEvidence
from app.models.project import RecommendedProject, AIGeneratedProject
from app.models.progress import UserProgress
from app.models.resume import Resume
from app.models.job_analysis import JobAnalysis

logger = logging.getLogger(__name__)

COACH_SYSTEM_PROMPT = """You are PathPilot AI, an expert career coach for students and professionals in India.

=== CORE RESPONSE PRINCIPLE ===
ALWAYS answer the user's actual question FIRST. The user's question is the priority.
Use the provided profile data ONLY as context to personalize the answer — never as the answer itself.

=== ABSOLUTE RULES ===

1. QUESTION FIRST, PROFILE SECOND:
   - If the user asks "How do I improve React?", explain HOW to improve React.
   - Do NOT respond with a list of all their skills.
   - Do NOT start with "Hi [name]!" or "Hello [name]!" unless it is the very first message in a new session.
   - Only mention profile data that is directly relevant to answering the current question.

2. GREETING RULES:
   - NEVER greet the user on every message.
   - NEVER start responses with "Hi [name]!", "Hello [name]!", or "Hey [name]!" on follow-up messages.
   - A greeting is ONLY acceptable for the first message of a genuinely new conversation.
   - For all follow-up questions, start directly with the answer.

3. NO PROFILE DUMPS:
   - NEVER list all skills unless the user specifically asks "What are my skills?" or similar.
   - If the user asks about React, only mention React-related skills (React, JavaScript, HTML/CSS, frontend skills).
   - Do NOT mention Python, Java, SQL, Git, or unrelated skills unless they are relevant to the question.

4. PERSONALIZATION USING SKILL LEVELS:
   - Use the user's actual skill proficiency to adapt your advice:
     * 0/5: No demonstrated skill → Start from fundamentals
     * 1/5: Very basic → Focus on fundamentals and simple practice
     * 2/5: Basic working knowledge → Build small projects and strengthen weak areas
     * 3/5: Intermediate → Build realistic projects and learn best practices
     * 4/5: Advanced → Focus on architecture, optimization, testing
     * 5/5: Expert → Focus on advanced patterns, leadership, specialization
   - Adapt your recommendations based on prerequisites. If JavaScript is 1/5, recommend strengthening it before React.

5. LEARNING QUESTIONS — USE THIS STRUCTURE:
   When the user asks "How do I improve X?" or "How do I learn X?":
   - Start with their current level in the requested skill and relevant prerequisites
   - Provide a step-by-step roadmap with clear phases
   - Include practice exercises or project suggestions
   - End with a concrete next action or milestone

6. TRUTH ENFORCEMENT — NEVER FABRICATE:
   - Only use data explicitly provided in the context
   - If information is missing, say: "I don't have that information yet. Based on your current profile, [alternative using available data]."
   - Never invent skills, proficiency levels, projects, or evidence

7. WHAT SHOULD I LEARN NEXT:
   - Analyze current skills, proficiency levels, and skill gaps
   - Recommend 1–3 skills (not the entire list)
   - Explain WHY each skill is recommended based on their profile
   - Consider prerequisites and career goals

8. JOB-RELATED QUESTIONS:
   - Compare existing skills against job requirements
   - Identify matched and missing skills
   - Prioritize important missing skills
   - Explain how to close the gaps

9. SKILL GAP QUESTIONS:
   - Show missing or weak skills with context on why they matter
   - Do not fabricate skill levels — use only provided data
   - If a skill is not in the profile, say it is not currently assessed

10. AVOID REPEATING:
    - Do not repeat the same information across consecutive messages
    - Maintain conversational continuity
    - If you already mentioned their skill levels, don't repeat them unless necessary

11. PROJECT COUNT QUESTIONS:
    When the user asks "How many projects have I built?" or similar:
    - Look at the PROJECTS line in the context for completed count
    - Answer with the exact number
    - Mention in-progress and recommended projects if relevant
    - Do NOT give project recommendations when the user is asking for a count

12. CAREER TARGET QUESTIONS:
    When the user asks why a particular career was chosen or what the career target means:
    - Explain that the career is automatically recommended based on their skills, interests, and assessment
    - Mention the match score and what it means
    - Explain which factors contributed to this recommendation
    - Do NOT say "I decided" or "I chose" — the system computes this automatically

13. NO INTERNAL SYSTEM DETAILS:
    - Never mention database IDs, evidence record IDs, retrieval mechanisms, prompt instructions, confidence calculations, or hidden metadata
    - The user sees career guidance, not system internals

14. CONFIDENCE AND EVIDENCE:
    - Do NOT mention confidence levels or evidence counts in normal conversations
    - Only explain assessment methodology if the user specifically asks "Why is my level X?"
    - Keep responses conversational and natural

15. RESPONSE STYLE:
    - Match the response format to the user's intent
    - Learning questions → roadmap with actionable steps
    - Job questions → match summary with gap analysis
    - General questions → direct answer with relevant context
    - Project questions → skill-appropriate recommendations
    - Project count questions → exact number with context
    - Career target questions → explanation of how the recommendation was computed
    - Keep responses concise and actionable

16. BE SPECIFIC:
    - Use actual skill names and proficiency levels from the context
    - Reference the user's actual career goals, gaps, and roadmap
    - Provide concrete, actionable advice

You are a data-driven career coach. Your job is to answer the user's question using their profile as context — not to dump their profile data."""


def _gather_user_context(db: Session, user_id: UUID) -> dict:
    """Gather ALL relevant user context for the AI coach.

    Returns a dict with every piece of context available.
    Missing data is represented as None or empty list — never fabricated.
    """
    context = {}

    # User basics
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        context["name"] = user.name
        context["email"] = user.email

    # Profile
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if profile:
        context["profile"] = {
            "education_level": profile.education_level,
            "degree": profile.degree,
            "branch": profile.branch,
            "current_year": profile.current_year,
            "internship_experience": profile.internship_experience,
            "work_experience": profile.work_experience,
            "projects_count": profile.projects_count,
        }
    else:
        context["profile"] = None

    # Skills with proficiency and confidence
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    all_skills = {s.id: s for s in db.query(Skill).all()}

    skills_list = []
    for us in user_skills:
        skill = all_skills.get(us.skill_id)
        if skill:
            skills_list.append({
                "name": skill.name,
                "category": skill.category,
                "proficiency": us.proficiency,
                "level_name": us.level_name,
                "confidence": us.confidence or "LOW",
            })
    context["skills"] = skills_list

    # Evidence records
    evidence_records = db.query(SkillEvidence).filter(
        SkillEvidence.user_id == user_id
    ).all()

    evidence_summary = {}
    for ev in evidence_records:
        skill = all_skills.get(ev.skill_id)
        if skill:
            evidence_summary.setdefault(skill.name, []).append({
                "source_type": ev.source_type,
                "title": ev.title,
                "confidence": ev.confidence,
                "score": ev.score,
            })
    context["evidence"] = evidence_summary

    # Interests
    user_interests = db.query(UserInterest).filter(UserInterest.user_id == user_id).all()
    all_interests = {i.id: i for i in db.query(Interest).all()}
    interest_names = []
    for ui in user_interests:
        interest = all_interests.get(ui.interest_id)
        if interest:
            interest_names.append(interest.name)
    context["interests"] = interest_names

    # Assessment results
    assessments = db.query(UserAssessment).filter(
        UserAssessment.user_id == user_id
    ).order_by(UserAssessment.created_at.desc()).all()

    if assessments:
        latest = assessments[0]
        context["assessment"] = {
            "scores": latest.scores,
            "created_at": str(latest.created_at),
        }
    else:
        context["assessment"] = None

    # Selected career (top recommendation or user's chosen career)
    career_recommendations = db.query(CareerRecommendation).filter(
        CareerRecommendation.user_id == user_id
    ).order_by(CareerRecommendation.match_score.desc()).all()

    if career_recommendations:
        top_rec = career_recommendations[0]
        career = db.query(Career).filter(Career.id == top_rec.career_id).first()
        if career:
            context["selected_career"] = {
                "name": career.name,
                "description": career.description,
                "category": career.category,
                "required_skills": career.required_skills or [],
                "optional_skills": career.optional_skills or [],
            }
            context["career_match"] = {
                "match_score": top_rec.match_score,
                "confidence": top_rec.confidence,
                "why_matches": top_rec.why_matches,
                "strengths": top_rec.strengths,
                "missing_skills": top_rec.missing_skills,
            }
        else:
            context["selected_career"] = None
            context["career_match"] = None
    else:
        context["selected_career"] = None
        context["career_match"] = None

    # All career recommendations
    all_recs = []
    for rec in career_recommendations[:5]:
        career = db.query(Career).filter(Career.id == rec.career_id).first()
        if career:
            all_recs.append({
                "career_name": career.name,
                "match_score": rec.match_score,
                "confidence": rec.confidence,
            })
    context["career_recommendations"] = all_recs

    # Skill gaps (for selected career)
    if context["selected_career"]:
        from app.services.skill_gap import analyze_skill_gaps
        skill_gaps = analyze_skill_gaps(db, user_id, context["selected_career"]["id"] if isinstance(context["selected_career"], dict) and "id" in context["selected_career"] else career_recommendations[0].career_id)
        context["skill_gaps"] = skill_gaps
    else:
        context["skill_gaps"] = None

    # Roadmap and current phase
    if context["selected_career"] and career_recommendations:
        roadmap = db.query(Roadmap).filter(
            Roadmap.user_id == user_id,
            Roadmap.career_id == career_recommendations[0].career_id,
        ).first()

        if roadmap:
            phases = db.query(RoadmapPhase).filter(
                RoadmapPhase.roadmap_id == roadmap.id
            ).order_by(RoadmapPhase.phase_number).all()

            current_phase = None
            completed_phases = []
            for phase in phases:
                if phase.status == "in_progress":
                    current_phase = {
                        "phase_number": phase.phase_number,
                        "title": phase.title,
                        "objective": phase.objective,
                        "skills": phase.skills,
                        "duration_weeks": phase.duration_weeks,
                        "adaptation_mode": phase.adaptation_mode,
                    }
                elif phase.status == "completed":
                    completed_phases.append(phase.title)

            context["roadmap"] = {
                "summary": roadmap.summary,
                "total_phases": len(phases),
                "completed_phases": len(completed_phases),
                "current_phase": current_phase,
                "completed_phase_titles": completed_phases,
            }
        else:
            context["roadmap"] = None
    else:
        context["roadmap"] = None

    # Projects
    recommended_projects = db.query(RecommendedProject).filter(
        RecommendedProject.user_id == user_id
    ).all()

    ai_projects = db.query(AIGeneratedProject).filter(
        AIGeneratedProject.user_id == user_id
    ).all()

    projects_summary = {
        "recommended": len([p for p in recommended_projects if p.status == "recommended"]),
        "in_progress": len([p for p in recommended_projects if p.status == "in_progress"]),
        "completed": len([p for p in recommended_projects if p.status == "completed"]) + len([p for p in ai_projects if p.status == "completed"]),
        "ai_generated": len(ai_projects),
        "ai_completed": len([p for p in ai_projects if p.status == "completed"]),
    }
    context["projects"] = projects_summary

    # Completed project details
    completed_project_ids = []
    for p in recommended_projects:
        if p.status == "completed":
            project = db.query(RecommendedProject).filter(RecommendedProject.id == p.id).first()
            if project:
                completed_project_ids.append(str(project.project_id))
    context["completed_project_count"] = len(completed_project_ids)

    # Resume evidence
    resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
    context["resumes_uploaded"] = len(resumes)
    if resumes:
        context["resume_skills_found"] = json.loads(resumes[0].skills) if resumes[0].skills else []
    else:
        context["resume_skills_found"] = []

    # Job analyses
    job_analyses = db.query(JobAnalysis).filter(JobAnalysis.user_id == user_id).all()
    context["job_analyses_count"] = len(job_analyses)
    if job_analyses:
        latest_job = job_analyses[0]
        match_result = json.loads(latest_job.match_result) if latest_job.match_result else None
        context["latest_job_analysis"] = {
            "job_title": latest_job.job_title,
            "alignment": match_result.get("alignment_percentage") if match_result else None,
            "missing_skills": match_result.get("missing_skills", []) if match_result else [],
        }
    else:
        context["latest_job_analysis"] = None

    # Next best action
    from app.services.next_best_action import compute_next_best_action
    nba = compute_next_best_action(db, user_id)
    context["next_best_action"] = {
        "action": nba.get("action"),
        "title": nba.get("title"),
        "description": nba.get("description"),
        "why": nba.get("why"),
        "skill_name": nba.get("skill_name"),
    }

    return context


def _build_context_string(context: dict) -> str:
    """Build a structured context string for the AI prompt.

    This is the source of truth for the AI — it only sees what's here.
    """
    parts = []

    parts.append(f"USER: {context.get('name', 'Unknown')}")

    profile = context.get("profile")
    if profile:
        parts.append(f"EDUCATION: {profile.get('education_level', 'N/A')}, {profile.get('degree', 'N/A')}, {profile.get('branch', 'N/A')}")
        parts.append(f"YEAR: {profile.get('current_year', 'N/A')}")
        if profile.get("internship_experience"):
            parts.append(f"INTERNSHIPS: {profile['internship_experience']}")
        if profile.get("work_experience"):
            parts.append(f"WORK EXPERIENCE: {profile['work_experience']}")
    else:
        parts.append("PROFILE: No profile data available")

    # Skills
    skills = context.get("skills", [])
    if skills:
        skill_lines = []
        for s in sorted(skills, key=lambda x: x["proficiency"], reverse=True):
            skill_lines.append(f"  - {s['name']}: {s['proficiency']}/5 ({s['confidence']} confidence)")
        parts.append(f"SKILLS ({len(skills)} total):\n" + "\n".join(skill_lines))
    else:
        parts.append("SKILLS: No skills tracked yet")

    # Evidence
    evidence = context.get("evidence", {})
    if evidence:
        evidence_lines = []
        for skill_name, ev_list in evidence.items():
            sources = [e["source_type"] for e in ev_list]
            evidence_lines.append(f"  - {skill_name}: {len(ev_list)} evidence records (sources: {', '.join(set(sources))})")
        parts.append(f"EVIDENCE:\n" + "\n".join(evidence_lines))
    else:
        parts.append("EVIDENCE: No evidence records")

    # Interests
    interests = context.get("interests", [])
    if interests:
        parts.append(f"INTERESTS: {', '.join(interests)}")
    else:
        parts.append("INTERESTS: None selected")

    # Assessment
    assessment = context.get("assessment")
    if assessment and assessment.get("scores"):
        scores = assessment["scores"]
        top_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
        parts.append(f"ASSESSMENT TOP DIMENSIONS: {', '.join(f'{d}={v:.0%}' for d, v in top_scores)}")
    else:
        parts.append("ASSESSMENT: Not completed")

    # Selected career
    career = context.get("selected_career")
    if career:
        parts.append(f"TARGET CAREER: {career['name']} ({career.get('category', 'N/A')})")
        parts.append(f"CAREER DESCRIPTION: {career.get('description', 'N/A')[:200]}")
        required = career.get("required_skills", [])
        if required:
            parts.append(f"REQUIRED SKILLS: {', '.join(required)}")
    else:
        parts.append("TARGET CAREER: None selected")

    # Career match
    match = context.get("career_match")
    if match:
        parts.append(f"CAREER MATCH SCORE: {match['match_score']:.0%} ({match['confidence']} confidence)")
        if match.get("missing_skills"):
            parts.append(f"MISSING SKILLS: {', '.join(match['missing_skills'][:5])}")

    # Skill gaps
    gaps = context.get("skill_gaps")
    if gaps and gaps.get("gaps"):
        gap_lines = []
        for g in gaps["gaps"][:8]:
            gap_lines.append(f"  - {g['skill']}: current {g['current_level']}/5, gap {g['gap_size']}, importance {g['importance']}, priority {g['priority_score']}")
        parts.append(f"SKILL GAPS (sorted by priority):\n" + "\n".join(gap_lines))
    else:
        parts.append("SKILL GAPS: No gap analysis available")

    # Roadmap
    roadmap = context.get("roadmap")
    if roadmap:
        parts.append(f"ROADMAP: {roadmap['summary']}")
        parts.append(f"PROGRESS: {roadmap['completed_phases']}/{roadmap['total_phases']} phases completed")
        if roadmap.get("current_phase"):
            cp = roadmap["current_phase"]
            parts.append(f"CURRENT PHASE: Phase {cp['phase_number']} — {cp['title']}")
            parts.append(f"  Objective: {cp['objective']}")
            parts.append(f"  Skills: {', '.join(cp.get('skills', []))}")
            parts.append(f"  Duration: {cp['duration_weeks']} weeks")
        if roadmap.get("completed_phase_titles"):
            parts.append(f"COMPLETED PHASES: {', '.join(roadmap['completed_phase_titles'])}")
    else:
        parts.append("ROADMAP: No roadmap generated yet")

    # Projects
    projects = context.get("projects", {})
    if projects:
        parts.append(f"PROJECTS: {projects.get('completed', 0)} completed, {projects.get('in_progress', 0)} in progress, {projects.get('recommended', 0)} recommended")

    # Resumes
    resumes_count = context.get("resumes_uploaded", 0)
    if resumes_count > 0:
        parts.append(f"RESUMES: {resumes_count} uploaded")
    else:
        parts.append("RESUMES: None uploaded")

    # Job analyses
    job_count = context.get("job_analyses_count", 0)
    if job_count > 0:
        latest = context.get("latest_job_analysis")
        if latest:
            parts.append(f"JOB ANALYSES: {job_count} completed, latest: '{latest['job_title']}' (alignment: {latest.get('alignment', 'N/A')}%)")
    else:
        parts.append("JOB ANALYSES: None completed")

    # Next best action
    nba = context.get("next_best_action", {})
    if nba.get("action"):
        parts.append(f"NEXT BEST ACTION: {nba['title']}")
        parts.append(f"  Why: {nba['why']}")
        if nba.get("skill_name"):
            parts.append(f"  Skill: {nba['skill_name']}")

    return "\n".join(parts)


def _build_suggestions(context: dict) -> list[str]:
    """Build contextual follow-up suggestions based on user's current state."""
    suggestions = []

    # Check what's missing and suggest accordingly
    skills = context.get("skills", [])
    assessment = context.get("assessment")
    career = context.get("selected_career")
    roadmap = context.get("roadmap")
    projects = context.get("projects", {})
    nba = context.get("next_best_action", {})

    if not skills:
        suggestions.append("How do I add my skills?")
    elif not assessment:
        suggestions.append("Should I take the career assessment?")
    elif not career:
        suggestions.append("Which career path suits me best?")
    elif not roadmap:
        suggestions.append("Generate my learning roadmap")
    elif projects.get("completed", 0) == 0:
        suggestions.append("What project should I build first?")
    elif nba.get("action") == "ASSESS_SKILL":
        suggestions.append(f"Help me prepare for {nba.get('skill_name', 'this')} assessment")
    elif nba.get("action") == "BUILD_PROJECT":
        suggestions.append("Guide me through building my next project")

    # Generic useful suggestions
    if len(suggestions) < 3:
        gaps = context.get("skill_gaps")
        if gaps and gaps.get("gaps"):
            top_gap = gaps["gaps"][0]
            suggestions.append(f"How do I improve my {top_gap['skill']} skills?")

    if len(suggestions) < 3:
        suggestions.append("What's my biggest career blocker right now?")

    return suggestions[:3]


async def ask_coach(
    db: Session,
    user_id: UUID,
    question: str,
) -> dict:
    """Answer a coaching question using full user context.

    Returns:
        {
            "response": str,
            "source": "ai" | "fallback",
            "context_used": dict  # summary of what context was injected
        }
    """
    context = _gather_user_context(db, user_id)
    context_string = _build_context_string(context)

    from app.ai.client import AIClient
    ai = AIClient()

    if ai.is_available:
        try:
            response = await ai.generate_coaching_response(question, context_string)
            if response:
                suggestions = _build_suggestions(context)
                return {
                    "response": response,
                    "source": "ai",
                    "suggestions": suggestions,
                    "context_used": {
                        "skills_count": len(context.get("skills", [])),
                        "has_career": context.get("selected_career") is not None,
                        "has_roadmap": context.get("roadmap") is not None,
                        "has_assessment": context.get("assessment") is not None,
                        "projects_completed": context.get("projects", {}).get("completed", 0),
                        "evidence_count": sum(len(v) for v in context.get("evidence", {}).values()),
                    },
                }
        except Exception as e:
            logger.warning(f"AI coaching failed: {e}")

    # Fallback: build a deterministic response using actual context
    response = _build_fallback_response(context, question)
    suggestions = _build_suggestions(context)
    return {
        "response": response,
        "source": "fallback",
        "suggestions": suggestions,
        "context_used": {
            "skills_count": len(context.get("skills", [])),
            "has_career": context.get("selected_career") is not None,
            "has_roadmap": context.get("roadmap") is not None,
            "has_assessment": context.get("assessment") is not None,
            "projects_completed": context.get("projects", {}).get("completed", 0),
            "evidence_count": sum(len(v) for v in context.get("evidence", {}).values()),
        },
    }


def _detect_user_intent(question: str) -> str:
    """Detect the user's intent from their question.
    
    Returns one of:
    - 'skill_improvement': How to improve/learn a specific skill
    - 'what_next': What should I learn next
    - 'skill_gaps': What skills am I missing
    - 'job_match': Job-related questions
    - 'project_count': How many projects have I done
    - 'project': Project recommendations
    - 'progress': Progress/status questions
    - 'explanation': What is X (concept explanation)
    - 'assessment': Assessment/result questions
    - 'skills_list': List my skills
    - 'general': General questions
    """
    q = question.lower()
    
    # Skills listing question (check before other skill-related intents)
    if any(phrase in q for phrase in [
        "what are my skills", "what skills do i have", "list my skills",
        "show my skills", "my skills", "skill list", "what skills am i good at",
        "what can i do", "what do i know"
    ]):
        return "skills_list"
    
    # Project count question (check before general project intent)
    if any(phrase in q for phrase in [
        "how many projects", "number of projects", "project count",
        "projects completed", "projects done", "projects i have",
        "how many have i built", "how many have i completed",
        "how many have i done", "total projects"
    ]):
        return "project_count"
    
    # What should I learn next (check before general "learn" intent)
    if any(phrase in q for phrase in [
        "what should i learn", "what next", "where should i start",
        "what should i do next", "what to learn next", "next steps",
        "what's the best next", "recommend a skill", "what should i focus on"
    ]):
        return "what_next"
    
    # Skill improvement / learning
    if any(phrase in q for phrase in [
        "how do i improve", "how to improve", "how do i learn", "how to learn",
        "how can i improve", "how can i learn", "improve my", "getting better at",
        "practice", "study", "master", "become better", "can you help me improve",
        "help me improve", "learn"
    ]):
        return "skill_improvement"
    
    # Job-related (check before skill_gaps to catch "missing skills for this job")
    if any(phrase in q for phrase in [
        "job", "position", "role", "hiring", "interview",
        "resume", "employment", "company", "work",
        "missing for this job", "skills for this job", "skills for this position",
        "skills for this role", "skills for this career", "match for this job"
    ]):
        return "job_match"
    
    # Skill gaps
    if any(phrase in q for phrase in [
        "what skills am i missing", "skill gap", "missing skills",
        "what am i lacking", "what do i need to learn", "weakest skills",
        "skills i'm missing", "skills am i lacking"
    ]):
        return "skill_gaps"
    
    # Career-related (general career questions)
    if any(phrase in q for phrase in [
        "career"
    ]):
        return "job_match"
    
    # Project-related
    if any(phrase in q for phrase in [
        "project", "build", "portfolio", "what should i build",
        "what project", "create", "application", "app"
    ]):
        return "project"
    
    # Progress / status
    if any(phrase in q for phrase in [
        "how am i doing", "progress", "readiness", "where am i",
        "status", "how am i progressing", "current level"
    ]):
        return "progress"
    
    # Assessment / results
    if any(phrase in q for phrase in [
        "assessment", "quiz", "test result", "score", "why is my",
        "why does it say", "evidence", "confidence"
    ]):
        return "assessment"
    
    # Explanation (what is X)
    if any(phrase in q for phrase in [
        "what is", "what are", "explain", "define", "tell me about",
        "difference between", "how does"
    ]):
        return "explanation"
    
    return "general"


def _get_relevant_skills(context: dict, skill_keyword: str) -> list[dict]:
    """Get skills from context that are relevant to a specific keyword.
    
    Returns a list of matching skills sorted by proficiency.
    """
    skills = context.get("skills", [])
    if not skill_keyword:
        return []
    
    keyword_lower = skill_keyword.lower()
    relevant = []
    
    # Common skill category mappings for frontend/backend/etc.
    frontend_skills = {"react", "vue", "angular", "html", "css", "javascript", "typescript", "sass", "tailwind", "bootstrap", "svelte", "next.js", "nextjs", "frontend", "front-end", "ui", "ux"}
    backend_skills = {"python", "java", "node", "nodejs", "django", "flask", "express", "spring", "php", "ruby", "go", "rust", "c#", ".net", "backend", "back-end", "api", "rest", "graphql"}
    data_skills = {"sql", "mysql", "postgresql", "mongodb", "data", "database", "pandas", "numpy", "machine learning", "ml", "ai", "tensorflow", "pytorch", "data science", "analytics"}
    devops_skills = {"git", "docker", "kubernetes", "aws", "azure", "gcp", "ci/cd", "linux", "devops", "cloud", "terraform", "jenkins"}
    
    # Determine category based on keyword
    category = None
    if keyword_lower in frontend_skills:
        category = "frontend"
    elif keyword_lower in backend_skills:
        category = "backend"
    elif keyword_lower in data_skills:
        category = "data"
    elif keyword_lower in devops_skills:
        category = "devops"
    
    for skill in skills:
        name_lower = skill["name"].lower()
        skill_category = skill.get("category", "").lower()
        
        # Direct match
        if keyword_lower in name_lower or name_lower in keyword_lower:
            relevant.append(skill)
            continue
        
        # Category match
        if category and (skill_category == category or skill_category in [category]):
            relevant.append(skill)
            continue
        
        # Check if skill name is in the category sets
        if category == "frontend" and name_lower in frontend_skills:
            relevant.append(skill)
        elif category == "backend" and name_lower in backend_skills:
            relevant.append(skill)
        elif category == "data" and name_lower in data_skills:
            relevant.append(skill)
        elif category == "devops" and name_lower in devops_skills:
            relevant.append(skill)
    
    return sorted(relevant, key=lambda x: x["proficiency"], reverse=True)


def _extract_skill_from_question(question: str) -> str:
    """Extract the main skill name from a question about improving/learning a skill."""
    q = question.lower()
    
    # Remove common prefixes/suffixes
    for phrase in ["how do i improve my", "how to improve", "how do i learn", "how to learn",
                    "how can i improve", "improve my", "get better at", "learn",
                    "how do i get better at", "tell me about", "what is"]:
        if phrase in q:
            q = q.replace(phrase, "")
    
    # Clean up
    q = q.strip().rstrip("?").strip()
    
    # Remove trailing words that aren't part of skill names
    for suffix in ["skills", "skill", "basics", "fundamentals", "from scratch", "as a beginner"]:
        if q.endswith(suffix):
            q = q[:-len(suffix)].strip()
    
    return q.strip()


def _build_fallback_response(context: dict, question: str) -> str:
    """Build a deterministic fallback response using actual context data.
    
    NEVER invents data — only uses what's in context.
    Follows the new response guidelines:
    - Answers the user's question FIRST
    - No repeated greetings
    - No full profile dumps
    - Uses profile data as context, not as the main response
    """
    name = context.get("name", "there")
    skills = context.get("skills", [])
    career = context.get("selected_career")
    gaps = context.get("skill_gaps")
    roadmap = context.get("roadmap")
    nba = context.get("next_best_action", {})
    intent = _detect_user_intent(question)
    
    # Skill improvement / learning question
    if intent == "skill_improvement":
        skill_keyword = _extract_skill_from_question(question)
        relevant_skills = _get_relevant_skills(context, skill_keyword)
        
        # Find the specific skill if mentioned
        target_skill = None
        for s in skills:
            if skill_keyword and skill_keyword.lower() in s["name"].lower():
                target_skill = s
                break
        
        response = ""
        
        # Start with current level if we found the skill
        if target_skill:
            response += f"Your {target_skill['name']} level is currently {target_skill['proficiency']}/5.\n\n"
            
            # Add prerequisite context if relevant
            if skill_keyword.lower() in ["react", "vue", "angular", "svelte", "next.js", "nextjs"]:
                js_skill = next((s for s in skills if "javascript" in s["name"].lower() or "js" in s["name"].lower()), None)
                if js_skill and js_skill["proficiency"] <= 2:
                    response += f"Since your JavaScript foundation is at {js_skill['proficiency']}/5, I'd recommend strengthening JavaScript basics before going deep into {target_skill['name']}.\n\n"
                elif js_skill and js_skill["proficiency"] >= 4:
                    response += f"Your JavaScript foundation is already strong at {js_skill['proficiency']}/5, so you can move directly into {target_skill['name']} fundamentals.\n\n"
        elif relevant_skills:
            # We found related skills but not the exact one
            response += f"Based on your profile, here are your current levels in related areas:\n"
            for s in relevant_skills[:3]:
                response += f"- {s['name']}: {s['proficiency']}/5\n"
            response += "\n"
        else:
            response += f"Let me help you with improving your {skill_keyword} skills.\n\n"
        
        # Provide a learning roadmap
        response += "Here's a structured approach to improve:\n\n"
        response += "### Step 1 — Fundamentals\n"
        response += "- Review core concepts and terminology\n"
        response += "- Complete beginner tutorials or documentation\n"
        response += "- Practice basic exercises\n\n"
        response += "### Step 2 — Hands-on Practice\n"
        response += "- Build small practice projects\n"
        response += "- Follow along with tutorials, then try on your own\n"
        response += "- Solve coding challenges related to this skill\n\n"
        response += "### Step 3 — Build Real Projects\n"
        response += "- Start with a simple project (Todo app, calculator, etc.)\n"
        response += "- Gradually increase complexity\n"
        response += "- Focus on solving real problems\n\n"
        response += "### Step 4 — Learn Best Practices\n"
        response += "- Study code organization and patterns\n"
        response += "- Learn testing and debugging\n"
        response += "- Read about performance and optimization\n\n"
        
        # Personalize project suggestions based on level
        if target_skill:
            level = target_skill["proficiency"]
            if level <= 1:
                response += "**Recommended first project:** A simple application that uses core features of this technology.\n\n"
            elif level <= 3:
                response += "**Recommended projects:**\n- Build a portfolio project that showcases multiple features\n- Contribute to an open-source project\n\n"
            else:
                response += "**Recommended next steps:**\n- Build a complex, production-quality application\n- Mentor others or write technical content\n\n"
        
        response += f"**Your next action:** Start with Step 1 today. Set aside 30-60 minutes to review the fundamentals."
        
        return response
    
    # Skills list question
    if intent == "skills_list":
        response = ""
        
        if skills:
            response += "Here are your current skills:\n\n"
            for s in sorted(skills, key=lambda x: x["proficiency"], reverse=True):
                response += f"- **{s['name']}**: {s['proficiency']}/5\n"
            
            response += "\n"
            
            # Add brief context about gaps if available
            if gaps and gaps.get("gaps"):
                top_gap = gaps["gaps"][0]
                response += f"Your biggest gap is **{top_gap['skill']}** at {top_gap['current_level']}/5."
        else:
            response = "You haven't added any skills yet. Start by adding the skills you currently have to your profile."
        
        return response
    
    # What should I learn next
    if intent == "what_next":
        response = ""
        
        if gaps and gaps.get("gaps"):
            top_gaps = gaps["gaps"][:3]
            response += "Based on your current profile, here are the highest-value skills to learn next:\n\n"
            
            for i, gap in enumerate(top_gaps, 1):
                skill_name = gap.get("skill", "Unknown")
                current = gap.get("current_level", 0)
                importance = gap.get("importance", 0)
                priority = gap.get("priority_score", 0)
                
                # Add context about why this skill matters
                why = ""
                if importance >= 0.8:
                    why = "High importance for your target career"
                elif importance >= 0.6:
                    why = "Important for your career path"
                else:
                    why = "Valuable for your skill set"
                
                response += f"{i}. **{skill_name}** — Currently {current}/5 — {why}\n"
            
            response += "\n"
            
            if career:
                response += f"For your target career ({career['name']}), these skills would help close the biggest gaps.\n\n"
            
            if nba.get("action"):
                response += f"**Recommended next step:** {nba['title']}\n"
                if nba.get("why"):
                    response += f"Why: {nba['why']}\n"
        elif not skills:
            response = "You haven't added any skills yet. Start by declaring your current skills so I can recommend what to learn next."
        elif not career:
            response = f"You have {len(skills)} skills tracked but haven't selected a target career yet. Take the career assessment or explore career recommendations to get personalized guidance on what to learn next."
        else:
            response = "You seem to be on track with your current skills. Consider taking an assessment to identify any areas for improvement, or start a new project to practice what you know."
        
        return response
    
    # Skill gaps question
    if intent == "skill_gaps":
        response = ""
        
        if gaps and gaps.get("gaps"):
            response += "Here are your current skill gaps, sorted by priority:\n\n"
            
            for gap in gaps["gaps"][:5]:
                skill_name = gap.get("skill", "Unknown")
                current = gap.get("current_level", 0)
                gap_size = gap.get("gap_size", 0)
                importance = gap.get("importance", 0)
                
                response += f"- **{skill_name}**: Currently {current}/5, gap of {gap_size}, importance {importance}\n"
            
            response += "\nThese are the areas where improving would have the biggest impact on your career goals."
        elif not skills:
            response = "You haven't added any skills yet, so I can't analyze your gaps. Start by adding your current skills to your profile."
        else:
            response = "Based on your current skills, you don't have any major gaps identified. Keep building through projects and assessments to maintain your skills."
        
        return response
    
    # Job-related questions
    if intent == "job_match":
        response = ""
        
        # Check for job analysis data
        job_analysis = context.get("latest_job_analysis")
        career_match = context.get("career_match")
        
        if job_analysis:
            response += f"**Job Analysis: {job_analysis.get('job_title', 'Unknown')}**\n\n"
            
            alignment = job_analysis.get("alignment")
            if alignment:
                response += f"Your alignment with this job: {alignment}%\n\n"
            
            missing = job_analysis.get("missing_skills", [])
            if missing:
                response += f"**Missing skills:** {', '.join(missing[:5])}\n\n"
                response += "Focus on learning these skills to improve your match."
            else:
                response += "You have a strong skill match for this position."
        elif career_match:
            response += f"**Career Match: {career.get('name', 'Unknown')}**\n\n"
            
            match_score = career_match.get("match_score", 0)
            response += f"Your match score: {match_score:.0%}\n\n"
            
            missing = career_match.get("missing_skills", [])
            if missing:
                response += f"**Missing skills:** {', '.join(missing[:5])}\n\n"
            
            strengths = career_match.get("strengths", [])
            if strengths:
                response += f"**Your strengths:** {', '.join(strengths[:5])}\n"
        else:
            response = "I don't have specific job analysis data for you yet. To get job matching insights, you can analyze a job description on the Job Analysis page."
        
        return response
    
    # Project count questions
    if intent == "project_count":
        response = ""
        projects = context.get("projects", {})
        completed = projects.get("completed", 0)
        in_progress = projects.get("in_progress", 0)
        recommended = projects.get("recommended", 0)
        
        response += f"You've completed **{completed}** project{'s' if completed != 1 else ''} so far.\n\n"
        
        if in_progress > 0:
            response += f"You also have **{in_progress}** project{'s' if in_progress != 1 else ''} currently in progress.\n\n"
        
        if recommended > 0:
            response += f"There are **{recommended}** project{'s' if recommended != 1 else ''} recommended for you.\n\n"
        
        if completed == 0:
            response += "Start building projects to gain practical experience and strengthen your skills."
        elif completed < 3:
            response += "Keep building! Adding more projects will help solidify your skills and strengthen your portfolio."
        else:
            response += "Great progress! Focus on making your projects more complex or try new technologies."
        
        return response
    
    # Project questions
    if intent == "project":
        response = ""
        projects = context.get("projects", {})
        
        if nba.get("action") == "BUILD_PROJECT":
            response += f"**Recommended next project:** {nba['title']}\n"
            if nba.get("why"):
                response += f"Why: {nba['why']}\n\n"
        
        # Recommend projects based on skill level
        if skills:
            # Find the skill with the lowest proficiency to recommend projects for
            weakest_skill = min(skills, key=lambda x: x["proficiency"])
            response += f"Based on your current levels, I'd recommend projects that help strengthen your {weakest_skill['name']} skills (currently {weakest_skill['proficiency']}/5).\n\n"
            
            if weakest_skill["proficiency"] <= 1:
                response += "**Beginner projects:**\n"
                response += "- Simple calculator or todo app\n"
                response += "- Personal portfolio website\n"
                response += "- Basic CRUD application\n\n"
            elif weakest_skill["proficiency"] <= 3:
                response += "**Intermediate projects:**\n"
                response += "- Full-stack application with authentication\n"
                response += "- REST API with database integration\n"
                response += "- Real-time application (chat, notifications)\n\n"
            else:
                response += "**Advanced projects:**\n"
                response += "- Complex dashboard with data visualization\n"
                response += "- Microservices architecture\n"
                response += "- Performance-optimized production application\n\n"
        else:
            response += "Add some skills to your profile first so I can recommend projects that target your specific areas for improvement."
        
        return response
    
    # Progress / status questions
    if intent == "progress":
        response = "Here's your current status:\n\n"
        
        if skills:
            avg_prof = sum(s["proficiency"] for s in skills) / len(skills)
            response += f"**Skills:** {len(skills)} tracked, average proficiency {avg_prof:.1f}/5\n"
        
        if career:
            match = context.get("career_match", {})
            response += f"**Target career:** {career['name']} (match: {match.get('match_score', 0):.0%})\n"
        
        if roadmap:
            response += f"**Roadmap progress:** {roadmap['completed_phases']}/{roadmap['total_phases']} phases completed\n"
            if roadmap.get("current_phase"):
                cp = roadmap["current_phase"]
                response += f"**Current phase:** Phase {cp['phase_number']} — {cp['title']}\n"
        
        projects = context.get("projects", {})
        response += f"**Projects:** {projects.get('completed', 0)} completed\n"
        
        return response
    
    # Assessment / explanation questions
    if intent == "assessment":
        response = ""
        
        # Check if asking about specific skill level
        q_lower = question.lower()
        if "why" in q_lower and ("level" in q_lower or "proficiency" in q_lower or "/" in q_lower):
            # User is asking why their level is what it is
            skill_keyword = _extract_skill_from_question(question)
            target_skill = None
            for s in skills:
                if skill_keyword and skill_keyword.lower() in s["name"].lower():
                    target_skill = s
                    break
            
            if target_skill:
                response += f"Your {target_skill['name']} proficiency is {target_skill['proficiency']}/5.\n\n"
                response += "This level is based on:\n"
                
                # Check evidence for this skill
                evidence = context.get("evidence", {})
                skill_evidence = evidence.get(target_skill["name"], [])
                if skill_evidence:
                    response += f"- {len(skill_evidence)} evidence records from sources: {', '.join(set(e['source_type'] for e in skill_evidence))}\n"
                    response += "- Assessment results and self-reported data\n\n"
                    response += "To improve this level, complete more assessments, build projects, or add evidence of your skills."
                else:
                    response += "- Your self-reported skill level\n"
                    response += "- Any assessments you've completed\n\n"
                    response += "Take a skill assessment or add evidence of your work to update this level."
            else:
                response = "I don't have information about that specific skill in your profile."
        else:
            response = "I can explain your assessment results. What specific skill or result would you like me to explain?"
        
        return response
    
    # Explanation (what is X) — answer directly without profile dump
    if intent == "explanation":
        skill_keyword = _extract_skill_from_question(question)
        
        # Provide a helpful explanation without dumping the profile
        response = f"Let me explain {skill_keyword or 'that concept'} for you.\n\n"
        
        # Add general guidance
        if skill_keyword:
            response += f"**{skill_keyword.title()}** is a technology/concept used in software development.\n\n"
            response += "To learn more about it:\n"
            response += "- Check the official documentation\n"
            response += "- Follow beginner tutorials\n"
            response += "- Practice with small projects\n\n"
            
            # Only mention profile if relevant
            relevant = _get_relevant_skills(context, skill_keyword)
            if relevant:
                response += "Based on your profile, here are your current levels in related areas:\n"
                for s in relevant[:3]:
                    response += f"- {s['name']}: {s['proficiency']}/5\n"
                response += "\nUse this as a starting point for your learning journey."
        else:
            response += "For detailed explanations, I recommend checking official documentation and following structured tutorials."
        
        return response
    
    # Default: general response
    response = ""
    
    # Provide a helpful, concise response
    if skills:
        # Show only top skills briefly
        top_skills = sorted(skills, key=lambda x: x["proficiency"], reverse=True)[:3]
        skill_summary = ", ".join(f"{s['name']} ({s['proficiency']}/5)" for s in top_skills)
        response += f"Based on your profile, your top skills are: {skill_summary}.\n\n"
    
    if career:
        match = context.get("career_match", {})
        response += f"Your target career is {career['name']} (match: {match.get('match_score', 0):.0%}).\n\n"
    
    if nba.get("action"):
        response += f"**Suggested next step:** {nba['title']}\n"
        if nba.get("why"):
            response += f"Why: {nba['why']}\n"
    
    if not skills and not career:
        response += "To get started: complete your profile, add your skills, and take the career assessment."
    
    return response


def get_coach_context(db: Session, user_id: UUID) -> dict:
    """Return a summary of the context available for the coach.

    Used by the frontend to display context information.
    """
    context = _gather_user_context(db, user_id)
    return {
        "name": context.get("name"),
        "skills_count": len(context.get("skills", [])),
        "has_profile": context.get("profile") is not None,
        "has_assessment": context.get("assessment") is not None,
        "selected_career": context.get("selected_career", {}).get("name") if context.get("selected_career") else None,
        "career_match_score": context.get("career_match", {}).get("match_score") if context.get("career_match") else None,
        "has_roadmap": context.get("roadmap") is not None,
        "roadmap_progress": f"{context['roadmap']['completed_phases']}/{context['roadmap']['total_phases']}" if context.get("roadmap") else None,
        "projects_completed": context.get("projects", {}).get("completed", 0),
        "evidence_count": sum(len(v) for v in context.get("evidence", {}).values()),
        "next_best_action": context.get("next_best_action", {}).get("title"),
        "top_skill_gaps": [
            {"skill": g["skill"], "gap": g["gap_size"]}
            for g in (context.get("skill_gaps", {}).get("gaps", [])[:3])
        ],
    }

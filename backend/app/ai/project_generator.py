import os
import re
import json
import logging
from typing import Optional

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class GeneratedProject(BaseModel):
    title: str
    description: str
    difficulty: str
    why_this_project: str
    skills_practiced: list[str]
    skills_targeted: list[str]
    duration: str
    learning_objectives: list[str]
    deliverables: list[str]
    completion_criteria: list[str]


class GeneratedProjectResponse(BaseModel):
    projects: list[GeneratedProject]


PROJECT_GENERATION_PROMPT = """You are a career-focused project recommendation engine. Generate project recommendations tailored to a specific learner.

LEARNER PROFILE:
- Target career: {career_name}
- Current skill levels: {skill_levels}
- Skill gaps (high priority): {skill_gaps}
- Roadmap phase: {roadmap_phase}
- User difficulty level: {user_difficulty}
- Previously completed projects: {previous_projects}

REQUIREMENTS:
- Generate exactly {count} projects
- Projects must target the user's ACTUAL skill gaps (do not assume they know skills they don't)
- Match difficulty to the user's current level: {user_difficulty}
- Each project should build skills needed for {career_name}
- Projects should be progressively harder within the difficulty level
- Do NOT generate projects for skills the user already has at proficiency 4+
- Focus on skills where the user has proficiency 0-2

DIFFICULTY GUIDELINES:
- BEGINNER: Simple, guided projects with clear steps. 1-2 weeks.
- INTERMEDIATE: Multi-component projects requiring integration. 2-4 weeks.
- ADVANCED: Complex, real-world scenarios with ambiguity. 4-8 weeks.
- INDUSTRY: Production-ready, portfolio-worthy projects. 6-12 weeks.

Return ONLY valid JSON with this exact structure:
{{
  "projects": [
    {{
      "title": "Project Title",
      "description": "2-3 sentence project description",
      "difficulty": "BEGINNER|INTERMEDIATE|ADVANCED|INDUSTRY",
      "why_this_project": "Why this project helps this specific learner",
      "skills_practiced": ["skill1", "skill2"],
      "skills_targeted": ["gap_skill1", "gap_skill2"],
      "duration": "2 weeks",
      "learning_objectives": ["objective1", "objective2"],
      "deliverables": ["deliverable1", "deliverable2"],
      "completion_criteria": ["criteria1", "criteria2"]
    }}
  ]
}}

IMPORTANT: Return ONLY the JSON object. No thinking, no commentary, no markdown fences."""


def _strip_thinking_tags(content: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    return cleaned.strip()


def _extract_json_from_response(content: str) -> Optional[dict]:
    cleaned = _strip_thinking_tags(content)

    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:])
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    try:
        start = cleaned.index("{")
        end = cleaned.rindex("}") + 1
        return json.loads(cleaned[start:end])
    except (ValueError, json.JSONDecodeError):
        pass

    return None


class GroqProjectGenerator:
    def __init__(self):
        self._client = None
        self._error_message = None
        self._initialized = False

    def _ensure_initialized(self):
        if self._initialized:
            return
        self._initialized = True

        api_key = os.getenv("GROQ_API_KEY", "")
        model = os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b")

        if not api_key:
            self._error_message = "AI project generation unavailable: GROQ_API_KEY not configured"
            return

        try:
            import groq
            self._client = groq.Groq(api_key=api_key)
            self._model = model
        except Exception as e:
            logger.error(f"Failed to initialize Groq client for projects: {e}")
            self._error_message = f"AI project generation unavailable: {type(e).__name__}"

    @property
    def is_available(self) -> bool:
        self._ensure_initialized()
        return self._client is not None

    @property
    def error_message(self) -> Optional[str]:
        self._ensure_initialized()
        return self._error_message

    @staticmethod
    def _get_candidate_models() -> list[str]:
        configured = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        defaults = [configured, "openai/gpt-oss-20b", "qwen/qwen3.6-27b", "openai/gpt-oss-120b"]
        seen = set()
        result = []
        for m in defaults:
            if m and m not in seen:
                seen.add(m)
                result.append(m)
        return result

    def generate_projects(
        self,
        career_name: str,
        skill_levels: dict[str, int],
        skill_gaps: list[str],
        roadmap_phase: str,
        user_difficulty: str,
        previous_projects: list[str],
        count: int = 3,
    ) -> tuple[Optional[list[GeneratedProject]], Optional[str]]:
        """Generate AI project recommendations.

        Returns:
            Tuple of (list of GeneratedProject or None, error_message or None)
        """
        if not self.is_available:
            return None, self._error_message or "AI service not available"

        skill_levels_str = ", ".join(
            f"{name}: {level}/5" for name, level in sorted(skill_levels.items())
        ) if skill_levels else "None listed"

        skill_gaps_str = ", ".join(skill_gaps[:10]) if skill_gaps else "None identified"
        previous_str = ", ".join(previous_projects[:5]) if previous_projects else "None"

        prompt = PROJECT_GENERATION_PROMPT.format(
            career_name=career_name,
            skill_levels=skill_levels_str,
            skill_gaps=skill_gaps_str,
            roadmap_phase=roadmap_phase,
            user_difficulty=user_difficulty,
            previous_projects=previous_str,
            count=count,
        )

        candidate_models = self._get_candidate_models()
        last_error = None

        for model in candidate_models:
            for attempt in range(2):
                try:
                    response = self._client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "Return ONLY valid JSON. No thinking, no commentary, no markdown."},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.7,
                        max_tokens=3000,
                    )

                    content = response.choices[0].message.content
                    if not content:
                        continue

                    data = _extract_json_from_response(content)
                    if data is None:
                        continue

                    projects = []
                    for p in data.get("projects", []):
                        difficulty = p.get("difficulty", "BEGINNER").upper()
                        if difficulty not in ("BEGINNER", "INTERMEDIATE", "ADVANCED", "INDUSTRY"):
                            difficulty = "BEGINNER"
                        projects.append(GeneratedProject(
                            title=p.get("title", "Untitled Project"),
                            description=p.get("description", ""),
                            difficulty=difficulty,
                            why_this_project=p.get("why_this_project", ""),
                            skills_practiced=p.get("skills_practiced", []),
                            skills_targeted=p.get("skills_targeted", []),
                            duration=p.get("duration", "2 weeks"),
                            learning_objectives=p.get("learning_objectives", []),
                            deliverables=p.get("deliverables", []),
                            completion_criteria=p.get("completion_criteria", []),
                        ))

                    if not projects:
                        continue

                    return projects, None

                except Exception as e:
                    logger.error(f"Groq project generation error on model {model} attempt {attempt + 1}: {e}")
                    last_error = f"AI project generation error: {type(e).__name__}"
                    if "rate" in str(e).lower() or "limit" in str(e).lower():
                        break

        return None, last_error or "AI failed to generate projects after multiple attempts."


project_generator = GroqProjectGenerator()

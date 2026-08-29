import os
import re
import json
import logging
from typing import Optional

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class SkillAssessmentQuestion(BaseModel):
    id: int
    difficulty: str
    type: str
    question: str
    options: list[str]
    correct_answer: str
    explanation: str


class SkillAssessmentResponse(BaseModel):
    skill: str
    questions: list[SkillAssessmentQuestion]


class SkillAnalysis(BaseModel):
    skill: str
    proficiency: int
    level_name: str
    score_percentage: float
    strengths: list[str]
    weaknesses: list[str]
    recommended_topics: list[str]
    summary: str


QUESTION_GENERATION_PROMPT = """You are a technical skill assessment system. Generate exactly 10 multiple-choice questions to assess a user's proficiency in {skill_name}.

SKILL TO ASSESS: {skill_name}

DIFFICULTY DISTRIBUTION (MUST be exactly this - no more, no less):
- 3 beginner questions
- 3 intermediate questions
- 2 advanced questions
- 2 practical/scenario questions

REQUIREMENTS:
- Questions must test REAL knowledge of {skill_name}
- Test conceptual understanding, practical knowledge, debugging, code interpretation, and problem-solving
- Include code snippets or concrete examples where appropriate for the skill
- Each question must have exactly 4 distinct, meaningful options (A, B, C, D)
- Only ONE correct answer per question
- Include a brief explanation for the correct answer
- No duplicate questions
- Questions should be unambiguous with a clear correct answer
- DO NOT generate generic placeholder questions
- DO NOT include the skill name in every question - test actual knowledge

Return ONLY valid JSON with this exact structure:
{{
  "skill": "{skill_name}",
  "questions": [
    {{
      "id": 1,
      "difficulty": "beginner",
      "type": "mcq",
      "question": "What does X do in Y?",
      "options": ["Meaningful option A", "Meaningful option B", "Meaningful option C", "Meaningful option D"],
      "correct_answer": "A",
      "explanation": "Brief explanation of why A is correct"
    }}
  ]
}}

IMPORTANT: Return ONLY the JSON object. No thinking, no commentary, no markdown fences."""


ANALYSIS_PROMPT = """You are a skill assessment analyst. Analyze the following assessment results and provide a concise, helpful analysis.

Skill assessed: {skill_name}
Score: {score_percentage}% (proficiency level: {proficiency}/5 - {level_name})

Questions and answers:
{question_details}

Provide analysis in valid JSON format:
{{
  "strengths": ["list of 2-3 specific strengths demonstrated"],
  "weaknesses": ["list of 2-3 areas needing improvement"],
  "recommended_topics": ["list of 3-5 specific topics to study next"],
  "summary": "2-3 sentence summary of the assessment result"
}}

Rules:
- Be specific and actionable
- Reference actual topics from the questions
- Keep it concise and encouraging
- Focus on growth areas
- Return ONLY valid JSON, no other text."""


def _strip_thinking_tags(content: str) -> str:
    """Remove <think>...</think> reasoning tokens from LLM output."""
    cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    cleaned = cleaned.strip()
    return cleaned


def _extract_json_from_response(content: str) -> Optional[dict]:
    """Extract JSON from LLM response, handling various formats."""
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

    json_match = re.search(r"\{[\s\S]*\"questions\"[\s\S]*\}", cleaned)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    try:
        start = cleaned.index("{")
        end = cleaned.rindex("}") + 1
        return json.loads(cleaned[start:end])
    except (ValueError, json.JSONDecodeError):
        pass

    return None


class GroqAIClient:
    def __init__(self):
        self._client = None
        self._error_message = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization - reads env vars after .env is loaded."""
        if self._initialized:
            return
        self._initialized = True
        
        api_key = os.getenv("GROQ_API_KEY", "")
        model = os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b")
        
        if not api_key:
            self._error_message = "AI assessment unavailable: GROQ_API_KEY not configured"
            return
        
        try:
            import groq
            self._client = groq.Groq(api_key=api_key)
            self._model = model
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            self._error_message = f"AI assessment unavailable: Failed to initialize AI client ({type(e).__name__})"

    @property
    def is_available(self) -> bool:
        self._ensure_initialized()
        return self._client is not None

    @property
    def error_message(self) -> Optional[str]:
        self._ensure_initialized()
        return self._error_message

    @staticmethod
    def _normalize_difficulty_labels(data: dict) -> None:
        """Normalize difficulty labels to match expected values."""
        difficulty_map = {
            "practical/scenario": "practical",
            "practical scenario": "practical",
            "scenario": "practical",
            "practical/scenario-based": "practical",
        }
        for q in data.get("questions", []):
            raw = q.get("difficulty", "").lower().strip()
            if raw in difficulty_map:
                q["difficulty"] = difficulty_map[raw]
            elif raw not in ("beginner", "intermediate", "advanced", "practical"):
                q["difficulty"] = "practical"

    def generate_questions(self, skill_name: str) -> tuple[Optional[SkillAssessmentResponse], Optional[str]]:
        """Generate questions and return (result, error_message).
        
        Returns:
            Tuple of (SkillAssessmentResponse or None, error_message or None)
        """
        if not self.is_available:
            error_msg = self._error_message or "AI service not available"
            logger.warning(error_msg)
            return None, error_msg

        prompt = QUESTION_GENERATION_PROMPT.replace("{skill_name}", skill_name)

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

    def generate_questions(self, skill_name: str) -> tuple[Optional[SkillAssessmentResponse], Optional[str]]:
        """Generate questions and return (result, error_message).
        
        Returns:
            Tuple of (SkillAssessmentResponse or None, error_message or None)
        """
        if not self.is_available:
            error_msg = self._error_message or "AI service not available"
            logger.warning(error_msg)
            return None, error_msg

        prompt = QUESTION_GENERATION_PROMPT.replace("{skill_name}", skill_name)
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
                        logger.warning(f"Model {model} attempt {attempt + 1}: Empty response from Groq")
                        continue

                    data = _extract_json_from_response(content)
                    if data is None:
                        logger.warning(f"Model {model} attempt {attempt + 1}: Could not extract JSON from response (length={len(content)})")
                        continue

                    self._normalize_difficulty_labels(data)

                    validated = SkillAssessmentResponse(**data)

                    if len(validated.questions) != 10:
                        logger.warning(f"Model {model} attempt {attempt + 1}: Got {len(validated.questions)} questions, expected 10")
                        continue

                    difficulty_counts = {}
                    for q in validated.questions:
                        difficulty_counts[q.difficulty] = difficulty_counts.get(q.difficulty, 0) + 1

                    expected = {"beginner": 3, "intermediate": 3, "advanced": 2, "practical": 2}
                    if difficulty_counts != expected:
                        logger.warning(f"Model {model} attempt {attempt + 1}: Difficulty distribution mismatch: {difficulty_counts}")
                        continue

                    return validated, None

                except ValidationError as e:
                    logger.warning(f"Model {model} attempt {attempt + 1}: Pydantic validation failed: {e}")
                    last_error = "AI response validation failed."
                except Exception as e:
                    logger.error(f"Groq API error on model {model} attempt {attempt + 1}: {type(e).__name__}: {e}")
                    error_msg = f"AI service error: {type(e).__name__}"
                    if "rate" in str(e).lower() or "limit" in str(e).lower() or "413" in str(e):
                        error_msg = "AI rate limit reached. Trying alternate model."
                    elif "quota" in str(e).lower():
                        error_msg = "AI quota exceeded."
                    elif "timeout" in str(e).lower():
                        error_msg = "AI service timeout."
                    last_error = error_msg
                    # If rate limit on this model, break inner loop to try next model immediately
                    break

        return None, last_error or "AI failed to generate questions after multiple attempts. Please try again later."

    def analyze_results(
        self,
        skill_name: str,
        score_percentage: float,
        proficiency: int,
        level_name: str,
        question_details: str,
    ) -> tuple[Optional[SkillAnalysis], Optional[str]]:
        """Analyze results and return (result, error_message)."""
        if not self.is_available:
            return None, self._error_message or "AI service not available"

        prompt = ANALYSIS_PROMPT.format(
            skill_name=skill_name,
            score_percentage=round(score_percentage),
            proficiency=proficiency,
            level_name=level_name,
            question_details=question_details,
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
                        max_tokens=1500,
                    )

                    content = response.choices[0].message.content
                    if not content:
                        continue

                    data = _extract_json_from_response(content)
                    if data is None:
                        continue

                    return SkillAnalysis(
                        skill=skill_name,
                        proficiency=proficiency,
                        level_name=level_name,
                        score_percentage=round(score_percentage),
                        strengths=data.get("strengths", []),
                        weaknesses=data.get("weaknesses", []),
                        recommended_topics=data.get("recommended_topics", []),
                        summary=data.get("summary", ""),
                    ), None

                except Exception as e:
                    logger.error(f"Groq analysis error on model {model} attempt {attempt + 1}: {e}")
                    last_error = f"AI analysis error: {type(e).__name__}"
                    break

        return None, last_error or "AI failed to analyze results after multiple attempts."

    def generate_coaching_response(
        self,
        system_prompt: str,
        context_string: str,
        conversation: list[dict],
        question: str,
    ) -> tuple[Optional[str], Optional[str]]:
        """Generate a personalized coaching response and return (text, error_message).

        `conversation` is a list of {"role": "user"|"assistant", "content": str}
        recent chat turns (already trimmed by the caller). The structured user
        context is injected as its own system message on every call so the model
        always reasons over the latest database state rather than stale history.
        """
        if not self.is_available:
            error_msg = self._error_message or "AI service not available"
            logger.warning(error_msg)
            return None, error_msg

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "system",
                "content": (
                    "STUDENT CONTEXT (from the application database — treat as ground truth, "
                    "never contradict it, never invent data beyond it):\n" + context_string
                ),
            },
        ]
        for turn in conversation:
            role = turn.get("role")
            content = turn.get("content")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": str(content)[:2000]})
        messages.append({"role": "user", "content": question})

        candidate_models = self._get_candidate_models()
        last_error = None

        for model in candidate_models:
            for attempt in range(2):
                try:
                    response = self._client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=0.6,
                        max_tokens=900,
                        timeout=20,
                    )

                    content = response.choices[0].message.content
                    if not content or not content.strip():
                        logger.warning(f"Model {model} attempt {attempt + 1}: Empty coaching response from Groq")
                        continue

                    return _strip_thinking_tags(content), None

                except Exception as e:
                    logger.error(f"Groq coaching error on model {model} attempt {attempt + 1}: {type(e).__name__}: {e}")
                    error_msg = f"AI service error: {type(e).__name__}"
                    err_str = str(e).lower()
                    if "rate" in err_str or "limit" in err_str or "429" in err_str:
                        error_msg = "AI rate limit reached."
                    elif "quota" in err_str:
                        error_msg = "AI quota exceeded."
                    elif "timeout" in err_str:
                        error_msg = "AI service timeout."
                    elif "model" in err_str and ("not found" in err_str or "decommission" in err_str or "invalid" in err_str):
                        error_msg = "AI model unavailable."
                    last_error = error_msg
                    break

        return None, last_error or "AI failed to generate a coaching response after multiple attempts."


groq_client = GroqAIClient()

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


class OpportunityAIAnalysis(BaseModel):
    match_score: int
    why_match: list[str]
    strengths: list[str]
    skill_gaps: list[str]
    recommendation: str


class ExtractedSkills(BaseModel):
    skills: list[str]


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


OPPORTUNITY_MATCH_PROMPT = """You are a career-matching analyst. Assess how well a student's demonstrated skills fit a specific job or internship opportunity.

OPPORTUNITY:
Title: {title}
Organization: {organization}
Type: {opp_type}
Required skills (from the posting): {required_skills}
Description/context: {description}

STUDENT PROFILE:
Demonstrated skills (name: proficiency out of 5): {user_skills}
Target career interest: {target_career}

DETERMINISTIC SKILL MATCH (already computed — treat as ground truth, do not contradict it):
Matched (proficiency 3+): {matched_skills}
Partial (proficiency 1-2): {partial_skills}
Missing: {missing_skills}
Deterministic score: {deterministic_score}/100

TASK:
Add contextual reasoning that plain skill-name matching misses — transferable skills, how central each missing skill actually is to this specific role, and relevance to the student's career interest.
Your match_score MUST stay within 15 points of the deterministic score above unless you have a strong, stated contextual reason to diverge.

Return ONLY valid JSON with this exact structure:
{{
  "match_score": 0-100,
  "why_match": ["short specific reason", "short specific reason"],
  "strengths": ["skill or trait 1", "skill or trait 2"],
  "skill_gaps": ["missing skill 1"],
  "recommendation": "1-2 sentence, encouraging and specific recommendation"
}}

IMPORTANT: Return ONLY the JSON object. No thinking, no commentary, no markdown fences."""


SKILL_EXTRACTION_PROMPT = """Extract the likely technical and professional skills required for this job/internship opportunity, based ONLY on the text provided. Do not invent skills the text doesn't imply. Return at most 10 skills, most important first.

TEXT:
{text}

Return ONLY valid JSON with this exact structure, replacing the example skill
names below with the REAL skill names you found in the text — never return
the literal placeholder strings "skill1"/"skill2" themselves:
{{"skills": ["<real skill name>", "<real skill name>"]}}

If you cannot confidently identify any real skills in the text, return {{"skills": []}} instead of guessing.

IMPORTANT: Return ONLY the JSON object. No thinking, no commentary, no markdown fences."""


_PLACEHOLDER_SKILL_PATTERN = re.compile(r"^skill\s*\d*$", re.IGNORECASE)


def _is_placeholder_skill(name: str) -> bool:
    """The skill-extraction prompt's own JSON example uses "skill1"/"skill2"
    as illustrative placeholder text. Under load a model can echo that
    example verbatim instead of extracting real skills — never trust the
    model not to do this; filter it out deterministically rather than
    relying on prompt wording alone."""
    return bool(_PLACEHOLDER_SKILL_PATTERN.match(name.strip()))


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
                        # The system prompt asks for up to 3 skills, each with its own
                        # Why/Roadmap/Practice/Next-action breakdown (see COACH_SYSTEM_PROMPT
                        # rule 5/7) — 900 routinely truncated that mid-sentence.
                        max_tokens=1800,
                        timeout=25,
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

    def analyze_opportunity_match(
        self,
        title: str,
        organization: str,
        opp_type: str,
        required_skills: list[str],
        description: str,
        user_skills: dict[str, int],
        target_career: Optional[str],
        deterministic_result: dict,
    ) -> tuple[Optional[OpportunityAIAnalysis], Optional[str]]:
        """Contextual reasoning layer on top of the deterministic skill match.

        Used only for the top candidate opportunities (see
        app.services.opportunity_recommendation) — not called per skill, and
        not called for every opportunity, to keep AI usage bounded.
        """
        if not self.is_available:
            return None, self._error_message or "AI service not available"

        prompt = OPPORTUNITY_MATCH_PROMPT.format(
            title=(title or "")[:200],
            organization=(organization or "")[:120],
            opp_type=opp_type,
            required_skills=", ".join(required_skills[:20]) or "Not specified",
            description=(description or "")[:1200],
            user_skills=", ".join(f"{k}: {v}/5" for k, v in list(user_skills.items())[:30]) or "None listed",
            target_career=target_career or "Not specified",
            matched_skills=", ".join(s["skill"] for s in deterministic_result.get("matched_skills", [])) or "None",
            partial_skills=", ".join(s["skill"] for s in deterministic_result.get("partial_skills", [])) or "None",
            missing_skills=", ".join(deterministic_result.get("missing_skills", [])) or "None",
            deterministic_score=deterministic_result.get("match_score", 0),
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
                        temperature=0.4,
                        max_tokens=700,
                        timeout=20,
                    )

                    content = response.choices[0].message.content
                    if not content:
                        continue

                    data = _extract_json_from_response(content)
                    if data is None:
                        continue

                    validated = OpportunityAIAnalysis(
                        match_score=int(data.get("match_score", deterministic_result.get("match_score", 0)) or 0),
                        why_match=[str(x) for x in (data.get("why_match") or [])][:5],
                        strengths=[str(x) for x in (data.get("strengths") or [])][:5],
                        skill_gaps=[str(x) for x in (data.get("skill_gaps") or [])][:5],
                        recommendation=str(data.get("recommendation") or ""),
                    )
                    return validated, None

                except ValidationError as e:
                    logger.warning(f"Opportunity match validation failed on model {model}: {e}")
                    last_error = "AI response validation failed."
                except Exception as e:
                    logger.error(f"Groq opportunity match error on model {model} attempt {attempt + 1}: {type(e).__name__}: {e}")
                    last_error = f"AI service error: {type(e).__name__}"
                    break

        return None, last_error or "AI failed to analyze this opportunity after multiple attempts."

    def extract_skills_from_text(self, text: str) -> tuple[Optional[list[str]], Optional[str]]:
        """Fallback skill extraction for opportunities with no structured
        required_skills field — used sparingly (Phase 6), never for postings
        that already list required skills."""
        if not self.is_available:
            return None, self._error_message or "AI service not available"

        prompt = SKILL_EXTRACTION_PROMPT.format(text=(text or "")[:1500])
        candidate_models = self._get_candidate_models()
        last_error = None

        for model in candidate_models:
            try:
                response = self._client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "Return ONLY valid JSON. No thinking, no commentary, no markdown."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=300,
                    timeout=15,
                )
                content = response.choices[0].message.content
                if not content:
                    continue

                data = _extract_json_from_response(content)
                if data is None:
                    continue

                validated = ExtractedSkills(skills=[str(s) for s in (data.get("skills") or [])][:10])
                real_skills = [s for s in validated.skills if s.strip() and not _is_placeholder_skill(s)]
                return real_skills, None

            except ValidationError:
                last_error = "AI response validation failed."
            except Exception as e:
                logger.error(f"Groq skill extraction error on model {model}: {type(e).__name__}: {e}")
                last_error = f"AI service error: {type(e).__name__}"

        return None, last_error or "AI failed to extract skills after multiple attempts."


groq_client = GroqAIClient()

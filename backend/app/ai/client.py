import os
import json
from typing import Optional

from pydantic import BaseModel


class RoadmapResponse(BaseModel):
    summary: str
    phases: list[dict]


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


class AIClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.client = None
        if self.api_key:
            try:
                import openai
                self.client = openai.AsyncOpenAI(api_key=self.api_key)
            except Exception:
                self.client = None

    @property
    def is_available(self) -> bool:
        return self.client is not None and bool(self.api_key)

    def validate_roadmap_response(self, response_text: str) -> Optional[dict]:
        try:
            data = json.loads(response_text)
            if "summary" not in data or "phases" not in data:
                return None
            if not isinstance(data["phases"], list):
                return None
            for phase in data["phases"]:
                required_fields = ["phase_number", "title", "objective", "skills", "activities"]
                if not all(f in phase for f in required_fields):
                    return None
            return data
        except (json.JSONDecodeError, TypeError):
            return None

    async def generate_roadmap(self, prompt: str) -> Optional[str]:
        if not self.is_available:
            return None
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": MASTER_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=4000,
            )
            return response.choices[0].message.content
        except Exception:
            return None

    async def generate_career_explanation(self, career_name: str, user_context: str) -> Optional[str]:
        if not self.is_available:
            return None
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are PathPilot AI, an expert career advisor. Provide clear, actionable career explanations tailored to the Indian job market."},
                    {"role": "user", "content": f"Explain the {career_name} career path for this user: {user_context}"},
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception:
            return None

    async def generate_coaching_response(self, question: str, user_context: str) -> Optional[str]:
        if not self.is_available:
            return None
        try:
            coaching_system_prompt = """You are PathPilot AI, an expert career coach for students and professionals in India.

=== CORE RULE ===
Answer the user's actual question FIRST. The user's question is the priority.
Use the provided profile data ONLY as context to personalize the answer — never as the answer itself.

=== CRITICAL RULES ===

1. QUESTION FIRST, PROFILE SECOND:
   - If the user asks "How do I improve React?", explain HOW to improve React.
   - If the user asks "How many projects have I built?", answer with the exact number from the context.
   - Do NOT list all their skills or start with a greeting on follow-up messages.
   - Only mention profile data that is directly relevant to the current question.

2. NO GREETINGS ON FOLLOW-UP MESSAGES:
   - NEVER start with "Hi [name]!" or "Hello [name]!" on follow-up messages.
   - Only greet on the very first message of a new conversation.

3. NO PROFILE DUMPS:
   - NEVER list all skills unless specifically asked.
   - If the user asks about React, only mention React-related skills (React, JavaScript, HTML/CSS, frontend).
   - Do NOT mention unrelated skills unless they are relevant to the question.

4. PERSONALIZE USING SKILL LEVELS:
   - 0/5: Start from fundamentals
   - 1/5: Focus on fundamentals and simple practice
   - 2/5: Build small projects and strengthen weak areas
   - 3/5: Build realistic projects and learn best practices
   - 4/5: Focus on architecture, optimization, testing
   - 5/5: Focus on advanced patterns, leadership, specialization
   - Adapt recommendations based on prerequisites (e.g., strengthen JavaScript before React if JavaScript is low).

5. LEARNING QUESTIONS STRUCTURE:
   When asked "How do I improve/learn X?":
   - Start with their current level in the requested skill and relevant prerequisites
   - Provide a step-by-step roadmap with clear phases
   - Include practice exercises or project suggestions
   - End with a concrete next action or milestone

6. PROJECT COUNT QUESTIONS:
   When asked "How many projects have I built?" or similar:
   - Look at the PROJECTS line in the context for completed count
   - Answer with the exact number
   - Mention in-progress and recommended projects if relevant
   - Do NOT give project recommendations when the user is asking for a count

7. CAREER TARGET QUESTIONS:
   When the user asks why a particular career was chosen or what the career target means:
   - Explain that the career is automatically recommended based on their skills, interests, and assessment
   - Mention the match score and what it means
   - Explain which factors contributed to this recommendation
   - Do NOT say "I decided" or "I chose" — the system computes this automatically

8. TRUTH ENFORCEMENT:
   - Only use data explicitly provided in the context
   - If information is missing, say: "I don't have that information yet. Based on your current profile, [alternative using available data]."
   - Never invent skills, proficiency levels, projects, or evidence

9. WHAT SHOULD I LEARN NEXT:
   - Analyze current skills, proficiency levels, and skill gaps
   - Recommend 1–3 skills (not the entire list)
   - Explain WHY each skill is recommended based on their profile

10. AVOID REPEATING:
    - Do not repeat the same information across consecutive messages
    - Maintain conversational continuity

11. NO INTERNAL DETAILS:
    - Never mention database IDs, evidence records, confidence calculations, or hidden metadata

12. KEEP RESPONSES CONCISE AND ACTIONABLE:
    - Match response format to user intent
    - Be specific with skill names and proficiency levels from context
    - Provide concrete, actionable advice

You are a data-driven career coach. Answer the user's question using their profile as context — not to dump their profile data."""
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": coaching_system_prompt},
                    {"role": "user", "content": f"User profile context:\n{user_context}\n\nUser question: {question}"},
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception:
            return None

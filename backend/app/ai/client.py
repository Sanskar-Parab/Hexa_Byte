import os
import json
from typing import Optional

from pydantic import BaseModel


class RoadmapResponse(BaseModel):
    summary: str
    phases: list[dict]


MASTER_SYSTEM_PROMPT = """You are Next Path AI, an expert career guidance system for students and professionals in India.

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
                    {"role": "system", "content": "You are Next Path AI, an expert career advisor. Provide clear, actionable career explanations tailored to the Indian job market."},
                    {"role": "user", "content": f"Explain the {career_name} career path for this user: {user_context}"},
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception:
            return None


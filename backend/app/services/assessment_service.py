from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.assessment import AssessmentQuestion, UserAssessment


DIMENSIONS = {
    "technical_interest": {
        "weight": 0.15,
        "interpretation": {
            (0, 0.3): "Low technical interest - consider exploring technical fields to build curiosity",
            (0.3, 0.6): "Moderate technical interest - you have some curiosity about technology",
            (0.6, 1.0): "High technical interest - you naturally gravitate toward technical topics",
        },
    },
    "problem_solving": {
        "weight": 0.15,
        "interpretation": {
            (0, 0.3): "Developing problem-solving skills - practice with puzzles and logic games",
            (0.3, 0.6): "Good problem-solving ability - you can work through challenges methodically",
            (0.6, 1.0): "Strong problem-solver - you excel at breaking down complex problems",
        },
    },
    "analytical_ability": {
        "weight": 0.15,
        "interpretation": {
            (0, 0.3): "Developing analytical skills - focus on data interpretation exercises",
            (0.3, 0.6): "Good analytical ability - you can analyze situations effectively",
            (0.6, 1.0): "Strong analytical thinker - you excel at data-driven decision making",
        },
    },
    "creativity": {
        "weight": 0.10,
        "interpretation": {
            (0, 0.3): "Developing creative thinking - try creative exercises and brainstorming",
            (0.3, 0.6): "Good creativity - you can generate novel ideas",
            (0.6, 1.0): "Highly creative - you excel at innovative thinking",
        },
    },
    "communication": {
        "weight": 0.10,
        "interpretation": {
            (0, 0.3): "Developing communication skills - practice presenting ideas",
            (0.3, 0.6): "Good communication - you express ideas clearly",
            (0.6, 1.0): "Excellent communicator - you excel at conveying complex ideas",
        },
    },
    "technology_interest": {
        "weight": 0.15,
        "interpretation": {
            (0, 0.3): "Low tech interest - explore different technology areas",
            (0.3, 0.6): "Moderate tech interest - you enjoy some technology aspects",
            (0.6, 1.0): "High tech interest - you are passionate about technology",
        },
    },
    "business_interest": {
        "weight": 0.10,
        "interpretation": {
            (0, 0.3): "Low business interest - explore entrepreneurship concepts",
            (0.3, 0.6): "Moderate business interest - you understand business fundamentals",
            (0.6, 1.0): "High business interest - you are drawn to business and strategy",
        },
    },
    "research_interest": {
        "weight": 0.10,
        "interpretation": {
            (0, 0.3): "Low research interest - explore academic research methods",
            (0.3, 0.6): "Moderate research interest - you enjoy investigating topics",
            (0.6, 1.0): "High research interest - you love deep investigation and discovery",
        },
    },
}


def score_assessment(db: Session, user_id: UUID, answers: dict) -> dict[str, Any]:
    questions = db.query(AssessmentQuestion).all()
    question_map = {str(q.id): q for q in questions}

    raw_scores: dict[str, list[float]] = {dim: [] for dim in DIMENSIONS}

    for q_id, answer_idx in answers.items():
        question = question_map.get(q_id)
        if not question:
            continue

        scoring = question.scoring or {}
        category = question.category

        if category in raw_scores and str(answer_idx) in scoring:
            raw_scores[category].append(float(scoring[str(answer_idx)]))

    scores = {}
    for dim, values in raw_scores.items():
        if values:
            scores[dim] = round(sum(values) / len(values), 4)
        else:
            scores[dim] = 0.5

    interpretation = {}
    for dim, score in scores.items():
        dim_config = DIMENSIONS.get(dim, {})
        for (low, high), text in dim_config.get("interpretation", {}).items():
            if low <= score < high:
                interpretation[dim] = text
                break
        if dim not in interpretation:
            interpretation[dim] = f"Score: {score:.1%}"

    sorted_dims = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_interests = [d[0] for d in sorted_dims[:3]]

    return {
        "scores": scores,
        "interpretation": interpretation,
        "top_interests": top_interests,
    }

# PHASE 7 FINAL REPORT

## AI Coach Architecture

```
User Question
     ↓
┌─────────────────────────────┐
│   _gather_user_context()    │  ← Queries ALL user data
│   • profile, skills, evidence│
│   • career, gaps, roadmap   │
│   • projects, resume, jobs  │
│   • next best action        │
└──────────┬──────────────────┘
           ↓
┌─────────────────────────────┐
│  _build_context_string()    │  ← Structured text for AI
│  TRUTH-ENFORCED: only uses  │
│  actual data, marks missing │
└──────────┬──────────────────┘
           ↓
┌─────────────────────────────┐
│  AI Client (OpenAI) OR      │
│  _build_fallback_response() │  ← Deterministic fallback
│  Uses actual context data   │
└──────────┬──────────────────┘
           ↓
┌─────────────────────────────┐
│  _build_suggestions()       │  ← Context-aware follow-ups
│  Based on what's missing    │
└─────────────────────────────┘
```

## Context Injection

The coach gathers **13 context categories** from the database:

| Context | Source Table | Example |
|---------|-------------|---------|
| Profile | `profiles` | Education, year, experience |
| Skills | `user_skills` + `skills` | Name, proficiency (1-5), confidence |
| Evidence | `skill_evidence` | Source type, confidence, score |
| Interests | `user_interests` + `interests` | Interest names |
| Assessment | `user_assessments` | Dimension scores |
| Selected Career | `career_recommendations` + `careers` | Name, required skills |
| Career Match | `career_recommendations` | Score, missing skills |
| Skill Gaps | Computed from career + skills | Gap size, importance, priority |
| Roadmap | `roadmaps` + `roadmap_phases` | Current phase, completed phases |
| Projects | `recommended_projects` + `ai_generated_projects` | Completed, in progress |
| Resumes | `resumes` | Count, skills found |
| Job Analyses | `job_analyses` | Latest alignment, missing skills |
| Next Best Action | Computed | Action type, title, why |

**Truth enforcement**: The system prompt explicitly forbids inventing data. Missing data is labeled as "None" / "No data available". The fallback response builder only uses actual context values.

## Adaptive Event Loop

```
Evidence Event                    Cascade
─────────────────────────────────────────────────────
on_skill_assessment_completed  →  skill profile updated
                                  → career readiness recomputed
                                  → roadmap phases re-adapted
                                  → next best action updated

on_project_completed           →  evidence created for skills
                                  → skill confidence updated
                                  → career readiness recomputed
                                  → next best action updated

on_resume_analyzed             →  evidence created (MEDIUM)
                                  → skill confidence updated
                                  → career readiness recomputed

on_job_analyzed                →  evidence created (MEDIUM)
                                  → skill confidence updated
                                  → career readiness recomputed
```

Events are triggered at the API layer after database commits, wrapped in try/except to prevent cascade failures from breaking the primary operation.

## Files Changed

### New Files (4)
| File | Purpose |
|------|---------|
| `backend/app/services/coach_service.py` | AI Coach with full context injection, truth enforcement, fallback responses |
| `backend/app/services/adaptive_events.py` | 4 event functions + 4 internal cascade functions |
| `backend/tests/test_coach_service.py` | 18 tests for context building, suggestions, fallback, truth enforcement |
| `backend/tests/test_adaptive_events.py` | 13 tests for all 4 events + internal functions |

### Modified Files (10)
| File | Change |
|------|--------|
| `backend/app/api/coach.py` | Replaced inline context with `coach_service.ask_coach()` + new `/context` endpoint |
| `backend/app/services/skill_assessment_service.py` | Added `on_skill_assessment_completed` trigger after assessment submission |
| `backend/app/api/projects.py` | Added `on_project_completed` trigger on status→completed |
| `backend/app/api/resume.py` | Added `on_resume_analyzed` trigger after resume processing |
| `backend/app/api/job_analysis.py` | Added `on_job_analyzed` trigger after job analysis |
| `backend/tests/conftest.py` | Added imports for new modules |
| `frontend/app/(dashboard)/coach/page.tsx` | Added context panel (skills, gaps, roadmap, next action) |
| `frontend/components/coach/ChatInterface.tsx` | Updated welcome message and loading state |
| `frontend/lib/api.ts` | Added `getCoachContext` method |
| `frontend/types/index.ts` | Added `CoachContext` and `CoachAskResponse` types |

## APIs

### Modified Endpoints
| Endpoint | Change |
|----------|--------|
| `POST /api/coach/ask` | Now returns `suggestions[]` and `context_used{}` in response |
| `POST /api/skill-assessment/submit` | Now returns `adaptive_updates{}` |
| `POST /api/projects/{id}/status` | Triggers adaptive events on completion |
| `POST /api/resume/upload` | Triggers adaptive events after processing |
| `POST /api/job/analyze` | Triggers adaptive events after analysis |

### New Endpoints
| Endpoint | Purpose |
|----------|---------|
| `GET /api/coach/context` | Returns summary of coach context for frontend display |

## Tests

**Total: 285 tests, 0 failures**

New Phase 7 tests (31):
- `test_coach_service.py`: 18 tests covering context string building, suggestions, fallback responses, truth enforcement
- `test_adaptive_events.py`: 13 tests covering all 4 event functions, career readiness recomputation, roadmap adaptation, project evidence creation

## Known Limitations

1. **AI key optional**: Without `OPENAI_API_KEY`, the coach uses deterministic fallback responses. These are context-aware but less conversational.

2. **Cascade scope**: Adaptive events update career readiness and roadmaps in-memory. They do NOT re-trigger AI roadmap generation — that requires explicit user action.

3. **Event isolation**: Each event is wrapped in try/except. If the cascade fails (e.g., database lock), the primary operation still succeeds. This means partial updates are possible.

4. **No real-time push**: The frontend must re-fetch data after actions to see adaptive updates. No WebSocket/SSE push mechanism.

5. **Coach conversation history**: The coach does NOT persist conversation history between requests. Each request is stateless — context is re-gathered from the database.

6. **Resume/Job evidence**: These create MEDIUM confidence evidence only. They do NOT upgrade proficiency levels — they only boost confidence scores.

7. **Roadmap adaptation**: Phases are only adapted if they are `not_started`. In-progress or completed phases are never retroactively adapted.

### Rate limit awareness

The coach does not currently enforce per-user rate limits on the `POST /api/coach/ask` endpoint. If the OpenAI API key is shared across multiple users, a single user sending many rapid questions could consume the quota for all users. Similarly, the adaptive event cascade functions (`on_skill_assessment_completed`, `on_project_completed`, `on_resume_analyzed`, `on_job_analyzed`) perform multiple database writes and recomputations in the same request; under very high concurrent load this could cause database contention. For production deployment, consider adding per-user rate limiting middleware and moving the heavier cascade work (e.g., career readiness recomputation) to a background queue.

### Session management

The coach is fully stateless: every call to `POST /api/coach/ask` gathers fresh context from the database, sends it to the AI (or builds a fallback), and returns the response. There is no server-side session or conversation memory. If you need multi-turn coaching conversations with context carryover, you would need to add a `coach_sessions` table to persist message history and include prior messages in the AI prompt. The current design was chosen to keep the coach always up-to-date with the latest user data without stale-cache issues.

### Rate limit awareness

The coach does not currently enforce per-user rate limits on the `POST /api/coach/ask` endpoint. If the OpenAI API key is shared across multiple users, a single user sending many rapid questions could consume the quota for all users. Similarly, the adaptive event cascade functions (`on_skill_assessment_completed`, `on_project_completed`, `on_resume_analyzed`, `on_job_analyzed`) perform multiple database writes and recomputations in the same request; under very high concurrent load this could cause database contention. For production deployment, consider adding per-user rate limiting middleware and moving the heavier cascade work (e.g., career readiness recomputation) to a background queue.

### Session management

The coach is fully stateless: every call to `POST /api/coach/ask` gathers fresh context from the database, sends it to the AI (or builds a fallback), and returns the response. There is no server-side session or conversation memory. If you need multi-turn coaching conversations with context carryover, you would need to add a `coach_sessions` table to persist message history and include prior messages in the AI prompt. The current design was chosen to keep the coach always up-to-date with the latest user data without stale-cache issues.

# Next Path AI

**Your Career Path, Personalized by AI**

Next Path AI is an AI-powered career guidance platform that analyzes your skills, interests, and goals to recommend personalized career paths with actionable roadmaps, skill gap analysis, AI coaching, and much more. It also includes a full employment outcome tracking system — built for the Maharashtra Government "Smart Education" problem statement — that follows students from training enrollment through placement and retention, and surfaces privacy-preserving, cohort-level analytics to government/provider stakeholders through a dedicated admin dashboard.

---

## Features

### Core Features
- **User Authentication** — Register, login, and secure JWT-based sessions (7-day expiry)
- **Multi-Step Onboarding** — 4-step profile setup: Basic Info, Experience, Interests, Skills
- **Career Fit Assessment** — 20-question assessment measuring 8 cognitive dimensions
- **AI Career Recommendations** — Weighted matching algorithm scoring careers on skill alignment, interests, assessment results, and experience
- **Skill Gap Analysis** — Compare current skills against career requirements with priority levels and severity
- **Personalized Learning Roadmaps** — Adaptive 4-6 phase learning plans with skills, activities, projects, and duration estimates
- **Progress Tracking** — Dashboard with readiness scores, phase completion, weekly actions, and 7-day charts
- **AI Coach** — Context-aware career coaching with conversation history support, intent detection, suggestions, truth enforcement, and security hardening (evidence source distinction, follow-up context, prompt injection protection)
- **Demo Mode** — Pre-loaded sample data (Aarav Sharma) for instant testing

### Skill Management
- **Skill Evidence System** — Multi-source evidence tracking (assessment, project, resume, job, manual) with confidence levels (LOW/MEDIUM/HIGH)
- **AI Skill Assessment** — 10-question MCQ assessment powered by Groq API with proficiency scoring and analysis
- **Confidence Auto-Recomputation** — Skill confidence recalculated automatically when evidence changes

### Resume & Job Analysis
- **Resume Upload & Parsing** — PDF upload with automatic section extraction (skills, experience, education, projects)
- **Skill Extraction** — Cross-references resume content against skill database with evidence creation
- **Job Description Analysis** — Paste job descriptions to analyze skill match and alignment percentage
- **Skill Matching** — Fuzzy/partial matching (React.js matches React) with strong/developing/missing breakdowns

### Jobs & Internships (AI-Personalized Recommendations)
- **Live Provider Data** — Real jobs and internships fetched from JSearch (by OpenWeb Ninja, via RapidAPI), never a local/fake dataset
- **India-First** — Every search is scoped server-side to India (`country=in`); recommendations are India-only by default, no manual filter needed
- **One Provider Abstraction** — `opportunity_provider.py` is the only module that talks to RapidAPI; the matching/recommendation layer is provider-agnostic, so swapping providers later doesn't touch the matching engine
- **Career-Aware Search** — Search queries are generated from the user's target career (falling back to their strongest skill), not a blind keyword dump — see [How the Matching Pipeline Works](#jobs--internships-how-the-matching-pipeline-works)
- **Skill Normalization Layer** — Deterministic alias resolution (React/React.js/React JS, Node/NodeJS/Node.js, HTML+CSS → HTML/CSS, etc.) so external postings match your skill profile without string-equality guesswork
- **Weighted Skill Matching** — Match score reflects proficiency, not just skill-name overlap (matched/partial/missing breakdown, each tied to your actual proficiency level)
- **Beginner-Priority Ranking** — For beginner users (no skill at Advanced+ proficiency), internship/entry-level postings get a small ranking boost and senior postings a small penalty — never a hard filter, and only ever applied on top of a real skill match
- **AI Contextual Analysis** — Groq reasons about transferable skills and role centrality for top candidates only, blended with (never overriding) the deterministic score
- **Minimal Upstream Calls** — At most two provider requests per recommendation request (one primary career/skill query, plus one secondary query only if the primary came back thin) — no per-skill fan-out, so a low RapidAPI quota isn't exhausted by normal use
- **Skill-Gap → Roadmap/Project Loop** — Missing skills on a listing link directly to your roadmap and skill-aware project recommendations
- **Graceful Degradation** — RapidAPI outages/rate limits/quota exhaustion never crash the app; if a query fails but a fallback query still returns data, that data is still shown

### Adaptive Systems
- **Adaptive Roadmaps** — Phases auto-adapt based on proficiency (skip adapted phases, reduce duration for known skills)
- **Adaptive Event System** — Cascading updates triggered by skill assessments, project completions, resume/job analyses
- **Next Best Action** — AI-powered prioritization of 10 action types by career impact, including 3 outcome-aware types triggered by placement/employment state
- **Skill-Aware Projects** — Composite scoring combining career relevance, gap relevance, roadmap relevance, and difficulty fit

### AI Integration
- **Multi-Model AI** — Groq-powered assessment, project generation, and career coaching with model fallback and rate limit handling
- **Deterministic Fallbacks** — Every AI feature has a non-AI fallback for reliability
- **AI Project Generation** — Generate custom project recommendations based on skill levels, gaps, and roadmap phase
- **Conversation-Aware Coaching** — Coach maintains chat history for follow-up questions (e.g., "Why?", "Tell me more") while always re-fetching fresh user context from the database
- **Security Hardening** — Prompt injection protection, evidence source transparency (assessed vs. self-reported vs. project-backed), and strict context-only data usage

### Employment Outcome Tracking (Career Outcomes)
Built for the Maharashtra Government "Smart Education" problem statement — tracking employment outcomes, skill gaps, and skilling-initiative impact across training providers, not just individual career guidance.
- **Consent-Gated Reporting** — Students opt in before any outcome data is recorded; consent can be revoked at any time, and revocation is honored everywhere outcome data is read or aggregated
- **Training Enrollment & Placement** — Students self-report training program enrollment, placement/employment status (placed, employed, self-employed, looking for work, not employed), job title, company, location, and salary — all optional beyond status
- **Longitudinal Check-Ins** — Periodic check-ins track continued employment, salary progression, and reasons for leaving (never required, since the honest case is "still employed")
- **Deterministic Training-Skill Relevance** — Job title/skills are matched against training program skills with a transparent, non-AI relevance score and label (see [How the Relevance Engine Works](#career-outcomes-how-the-relevance-engine-works))
- **Placement Readiness Scoring** — Deterministic score combining skill coverage, evidence confidence, and training completion
- **AI-Assisted Analysis (advisory only)** — Non-placement reason analysis, attrition risk analysis, and plain-language relevance explanations, each clearly separated from the deterministic numbers that drive scoring and never used to compute them
- **Adaptive Curriculum Loop** — Recurring skill gaps across a training program's outcomes feed back into curriculum recommendations for that program
- **Outcome-Aware Next Best Action** — 3 additional action types (`IMPROVE_SKILL_FOR_PLACEMENT`, `APPLY_OPPORTUNITIES`, `EXPLORE_RELEVANT_OPPORTUNITIES`) triggered by a student's placement/employment state, alongside the original 7

### Government Admin Dashboard (Privacy-Preserving Analytics)
A separate `is_admin`-gated area for tracking skilling-initiative impact in aggregate, without exposing any individual's data.
- **Cohort-Level Aggregation Only** — Every metric is computed over a cohort; any cohort smaller than `MIN_COHORT_SIZE` (5) is suppressed rather than shown, so a small group can never be re-identified
- **Overview, Provider, Program & Retention Views** — Placement rate, average salary, retention curves, and provider/program comparison, each filterable by date range, provider, and program
- **Skill Gap & Non-Placement Analysis** — Aggregate view of the most common missing skills and reasons students remain unplaced
- **Curriculum Recommendations** — Surfaces recurring skill gaps (≥30% of a cohort) as concrete curriculum suggestions per program
- **Demo Dataset Labeling** — Synthetic demo data (`is_demo` users, `(Demo)`-suffixed providers) is clearly labeled and counted separately in every view — including a deliberately sub-`MIN_COHORT_SIZE` provider, to demonstrate suppression behavior — never silently mixed into real numbers

---

## Tech Stack

### Frontend

| Technology | Purpose |
|------------|---------|
| Next.js 14 (App Router) | React framework with SSR/SSG |
| TypeScript 5 | Type safety |
| Tailwind CSS 3.4 | Utility-first styling |
| Radix UI + shadcn/ui | Accessible UI components (Dialog, Select, Slider, Tabs, Progress, Avatar) |
| Recharts | Data visualization (progress charts) |
| Lucide React | Icons |
| date-fns | Date utilities |

### Backend

| Technology | Purpose |
|------------|---------|
| FastAPI | Python async web framework |
| SQLAlchemy 2.0 | ORM and database management |
| SQLite / PostgreSQL | Database (SQLite for dev, PostgreSQL for prod) |
| Pydantic 2.5 | Data validation schemas |
| Groq API | AI skill assessment, project generation, career coaching with model fallback |
| PyPDF2 | Resume PDF text extraction |
| JWT + bcrypt | Authentication and security |
| Alembic | Database migrations |
| pandas | Data manipulation |

---

## Project Structure

```
nextpath/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point (CORS, router registration)
│   │   ├── api/                 # Route handlers (auth, profile, careers, outcomes, admin_analytics, etc.)
│   │   ├── models/              # SQLAlchemy ORM models, incl. outcome.py (training/enrollment/employment/check-in/consent)
│   │   ├── schemas/             # Pydantic request/response schemas, incl. outcome*.py
│   │   ├── services/            # Business logic — matching, gaps, roadmaps, next_best_action,
│   │   │                        #   training_intelligence, admin_analytics, outcome_*, demo_outcome_seed
│   │   ├── database/            # DB config, migrations, seed data (incl. admin user + demo outcome data)
│   │   ├── ai/                  # OpenAI & Groq integration
│   │   └── utils/               # Auth utilities (incl. admin-only dependency)
│   ├── tests/                   # 612+ backend tests
│   └── requirements.txt         # Python dependencies
│
└── frontend/
    ├── app/
    │   ├── page.tsx             # Landing page
    │   ├── (auth)/              # Login & register pages
    │   ├── admin/               # Government admin dashboard (is_admin-gated, separate layout)
    │   │   └── outcomes/        # Cohort analytics: overview, providers, programs, retention, skill gaps
    │   └── (dashboard)/         # Authenticated student routes
    │       ├── dashboard/       # Main dashboard
    │       ├── onboarding/      # Multi-step profile setup
    │       ├── assessment/      # Career fit assessment + results
    │       ├── careers/         # Career recommendations + detail
    │       ├── skills/          # Skill management + AI assessment
    │       ├── roadmap/         # Learning roadmap
    │       ├── projects/        # Project recommendations + detail
    │       ├── coach/           # AI career coach
    │       ├── resume/          # Resume upload & parsing
    │       ├── job-analyzer/    # Job description analysis
    │       ├── opportunities/   # AI-personalized jobs & internships (live provider data)
    │       └── outcomes/        # Career Outcomes — report placement/employment, check-ins, timeline
    ├── components/              # Reusable UI components
    │   ├── ui/                  # Base UI primitives (shadcn/ui)
    │   ├── landing/             # Landing page sections
    │   ├── dashboard/           # Dashboard widgets
    │   ├── career/              # Career-related components
    │   ├── skills/              # Skill management components
    │   ├── assessment/          # Assessment components
    │   ├── roadmap/             # Roadmap timeline & phase cards
    │   ├── projects/            # Project recommendation cards
    │   ├── coach/               # Chat interface
    │   ├── resume/              # Resume uploader & results
    │   ├── job/                 # Job analyzer & match results
    │   ├── opportunities/       # Opportunity cards (match score, skill gaps, apply)
    │   ├── outcomes/            # Timeline, salary progression, check-in history, report form
    │   └── admin/               # Metric cards, filter bar, charts, provider/program tables,
    │                            #   curriculum recommendations, demo dataset banner
    ├── hooks/                   # Custom React hooks (useAuth)
    ├── lib/                     # API client and utilities
    └── types/                   # TypeScript interfaces
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --port 8000
```

The database auto-migrates and seeds on first startup. API docs are available at `http://localhost:8000/docs`.

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app is available at `http://localhost:3000`. API calls are proxied to the backend automatically.

---

## Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Database (defaults to SQLite)
DATABASE_URL=sqlite:///nextpath.db

# For PostgreSQL (production):
# DATABASE_URL=postgresql://user:password@localhost:5432/nextpath

# JWT Secret (change in production)
JWT_SECRET=your-secret-key-here

# OpenAI (optional — app works without it using deterministic fallback)
OPENAI_API_KEY=your-openai-api-key-here

# Groq API (required for AI-powered skill assessment and project generation)
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=openai/gpt-oss-120b

# Opportunity provider (JSearch by OpenWeb Ninja, via RapidAPI) — powers Jobs
# & Internships recommendations. Subscribe at
# https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch and paste your key below.
# Credentials are backend-only — never sent to the frontend, logged, or returned by any API.
# Without this, the feature degrades gracefully (empty list + "temporarily
# unavailable" message) instead of breaking the app.
OPPORTUNITY_RAPIDAPI_KEY=your-rapidapi-key-here
OPPORTUNITY_RAPIDAPI_HOST=jsearch.p.rapidapi.com
OPPORTUNITY_CACHE_TTL_SECONDS=3600
OPPORTUNITY_QUOTA_BACKOFF_SECONDS=3600

# Opportunity match scoring weights (deterministic skill score vs AI contextual score)
OPPORTUNITY_DETERMINISTIC_WEIGHT=0.6
OPPORTUNITY_AI_WEIGHT=0.4
OPPORTUNITY_AI_TOP_N=5
OPPORTUNITY_MAX_SKILL_EXTRACTIONS=20

# Comma-separated frontend origin(s) allowed to call this API (CORS).
# Unset in dev, this defaults to http://localhost:3000,http://localhost:3001.
# Set explicitly to your real frontend origin(s) in production.
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

> **Note:** The frontend requires no environment variables — API calls are proxied via Next.js rewrites.

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login and receive JWT |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Get current user |

### Profile
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/profile` | Get or update profile |
| POST | `/api/profile/onboarding` | Complete multi-step onboarding |

### Skills
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/skills` | List all available skills |
| GET | `/api/skills/user` | List user's skills with proficiency & confidence |
| POST | `/api/skills` | Add a skill to user profile |
| PUT | `/api/skills/{skill_id}` | Update skill proficiency |
| DELETE | `/api/skills/{skill_id}` | Remove a skill |

### Interests
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/interests` | List all interests |
| GET | `/api/interests/user` | List user's interests |
| POST | `/api/interests/{interest_id}` | Add interest |
| DELETE | `/api/interests/{interest_id}` | Remove interest |

### Assessment
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/assessment/questions` | Get 20 assessment questions |
| POST | `/api/assessment/submit` | Submit answers, get 8-dimension scores |
| GET | `/api/assessment/result` | Get latest assessment result |

### Career Recommendations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/careers` | List all career paths |
| GET | `/api/careers/{id}` | Get career detail |
| POST | `/api/careers/recommend` | Get personalized career recommendations |
| GET | `/api/careers/recommendations` | Get stored recommendations |
| GET | `/api/careers/{id}/intelligence` | Get full career intelligence |

### Skill Gap Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/skill-gap/analyze` | Analyze skill gaps for a career |

### Roadmap
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/roadmap/generate` | Generate personalized learning roadmap |
| GET | `/api/roadmap` | Get current roadmap |
| PUT | `/api/roadmap/phase/{phase_id}/status` | Update phase status |

### Projects
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects/recommendations` | Get skill-aware project recommendations |
| GET | `/api/projects/user-difficulty` | Get user difficulty level |
| PUT | `/api/projects/preferred-difficulty` | Set preferred difficulty |
| GET | `/api/projects/stats` | Get project stats |
| GET | `/api/projects/ai-generated` | List AI-generated projects |
| GET | `/api/projects/{id}` | Get project detail |
| POST | `/api/projects/generate-ai` | Generate AI project recommendations |
| POST | `/api/projects/{id}/status` | Update project status |

### Progress
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/progress/dashboard` | Get progress dashboard data |
| POST | `/api/progress/update` | Update progress for an item |

### AI Coach
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/coach/ask` | Ask AI career coach (accepts optional `conversation` history for follow-ups) |
| GET | `/api/coach/context` | Get coach context summary |

### Skill Assessment (AI)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/skill-assessment/ai-status` | Check AI availability |
| POST | `/api/skill-assessment/start` | Start AI skill assessment |
| POST | `/api/skill-assessment/submit` | Submit assessment answers |

### Evidence
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/evidence` | List all evidence grouped by skill |
| GET | `/api/evidence/skill/{skill_id}` | Get evidence for a skill |

### Next Best Action
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/next-best-action` | Get highest-priority next action |

### Resume
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/resume/upload` | Upload and parse PDF resume |
| GET | `/api/resume` | List uploaded resumes |
| GET | `/api/resume/{id}` | Get resume detail |
| DELETE | `/api/resume/{id}` | Delete resume |

### Job Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/job/analyze` | Analyze job description |
| GET | `/api/job/history` | List past job analyses |
| GET | `/api/job/{id}` | Get specific analysis |
| DELETE | `/api/job/{id}` | Delete analysis |

### Jobs & Internships (Opportunities)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/opportunities/recommendations` | Personalized job/internship recommendations from live provider data. Query params: `type` (`all`\|`internship`\|`job`), `limit`, `min_match`, `career_id`. User identity always comes from the JWT, never a query param. |

### Demo
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/demo/load` | Load demo data |

### Career Outcomes (student-facing, consent-gated)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/outcomes/consent` | Get or set outcome-tracking consent (required before any outcome write) |
| GET | `/api/outcomes/training` | List training programs |
| POST | `/api/outcomes/training` | Create a training program (provider-side) |
| GET/POST | `/api/outcomes/enrollment` | List the user's enrollments / enroll in a training program |
| GET/POST | `/api/outcomes/employment` | List the user's employment outcomes / report placement or employment |
| GET/POST | `/api/outcomes/check-in` and `/api/outcomes/check-ins` | Submit a longitudinal check-in / list check-in history |
| GET | `/api/outcomes/timeline` | Full timeline: training, placement, salary progression, check-ins, summary |
| GET | `/api/outcomes/{training_program_id}/skill-match` | Deterministic training-to-skill match detail |
| GET | `/api/outcomes/{training_program_id}/relevance` | Deterministic training-to-job relevance score + label |
| GET | `/api/outcomes/readiness` | Placement readiness score |
| GET | `/api/outcomes/opportunities` | Opportunities relevant to the user's training |
| GET | `/api/outcomes/analysis/non-placement` | AI-assisted (advisory only) reason analysis for non-placement |
| GET | `/api/outcomes/analysis/attrition` | AI-assisted (advisory only) attrition risk analysis |
| GET | `/api/outcomes/analysis/relevance-explanation` | AI-assisted (advisory only) plain-language relevance explanation |

### Admin Analytics (government dashboard, `is_admin`-gated)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/outcomes/overview` | Cohort-level placement/salary/retention metrics (suppressed below `MIN_COHORT_SIZE`) |
| GET | `/api/admin/outcomes/providers` | Provider comparison |
| GET | `/api/admin/outcomes/programs` | Program-level analytics |
| GET | `/api/admin/outcomes/skill-gaps` | Aggregate skill gap analysis |
| GET | `/api/admin/outcomes/non-placement` | Aggregate non-placement reason breakdown |
| GET | `/api/admin/outcomes/curriculum-recommendations` | Curriculum suggestions from recurring skill gaps (≥30% of cohort) |
| GET | `/api/admin/outcomes/filters` | Available filter options (providers, programs, date ranges) |
| POST | `/api/admin/outcomes/demo-data` | Seed idempotent, clearly-labeled demo outcome data |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

---

## How It Works

1. **Sign up** and complete the 4-step onboarding to build your profile
2. **Take the assessment** — answer 20 questions across 8 cognitive dimensions
3. **Get career recommendations** — weighted scoring matches you to 22+ career paths
4. **View skill gaps** — see exactly what skills you need with priority and severity
5. **Follow your roadmap** — adaptive learning plan that adjusts to your proficiency
6. **Build projects** — skill-aware project recommendations with difficulty settings
7. **Track progress** — readiness scores, phase completion, weekly actions, and 7-day charts
8. **Upload your resume** — automatic skill extraction and evidence creation
9. **Analyze job descriptions** — see your alignment and skill match breakdown
10. **Chat with AI Coach** — context-aware career coaching with conversation history for follow-ups (e.g., "Why?", "Tell me more"), evidence source transparency, and security hardening
11. **Take AI skill assessments** — Groq-powered MCQs with proficiency scoring
12. **Browse Jobs & Internships** — see real opportunities ranked by how well they match your demonstrated skills, with clear reasoning and a direct link to close each gap
13. **Track Career Outcomes** — opt in to outcome tracking, enroll in a training program, report your placement or employment, and add periodic check-ins; see your full timeline, salary progression, and training-to-job relevance score

For government/provider stakeholders, an `is_admin` account instead sees an **Admin Dashboard** (`/admin/outcomes`) with cohort-level placement, retention, skill-gap, and curriculum-impact analytics — see [Career Outcomes: How the Relevance Engine Works](#career-outcomes-how-the-relevance-engine-works) and the [Admin Analytics](#admin-analytics-government-dashboard-is_admin-gated) endpoints above.

---

## Jobs & Internships: How the Matching Pipeline Works

```
Authenticated user (JWT)
  → user's demonstrated skills + proficiency (app.services.opportunity_recommendation.get_user_skill_map)
  → career-aware search query generation (app.services.opportunity_recommendation._build_search_queries
    — primary query from target career, falling back to strongest skill, then a generic query;
    an internship-only request biases the query text itself instead of fetching a mixed pool)
  → live provider data (app.services.opportunity_provider — JSearch GET /search, country=in)
      primary query always runs; a second (skill-based) query only runs if the
      primary came back with fewer than MIN_RESULTS_BEFORE_SECONDARY_QUERY results
      — never one request per skill
    (cached per exact query, deduped by job_id/apply URL/title+employer+location,
    non-India results rejected even though the search itself is already India-scoped)
  → skill normalization (app.services.skill_normalization — aliases, no LLM calls)
  → required-skill extraction (JSearch's job_required_skills is used directly when
    present; otherwise Groq extracts from title+description+highlights — results
    are cached per posting and capped at OPPORTUNITY_MAX_SKILL_EXTRACTIONS new
    calls per request so a large result set can't trigger unbounded AI usage)
  → deterministic weighted skill matching (app.services.opportunity_matching — proficiency-aware, 0-100 score)
  → AI contextual analysis for top candidates only (app.ai.groq_client.analyze_opportunity_match)
  → hybrid score (deterministic × 0.6 + AI × 0.4, configurable via env)
  → beginner-priority experience adjustment (small ranking nudge toward
    internship/entry-level postings for beginner users; only ever applied on
    top of an already-nonzero match, never a hard filter)
  → ranked, filtered results
  → GET /api/opportunities/recommendations
  → frontend opportunity cards (/opportunities, and "Opportunities For You" on the dashboard)
```

`opportunity_provider.py` is the only module that knows about RapidAPI/JSearch — the matching engine, AI analysis, ranking, and frontend are all provider-agnostic, so the provider could be swapped again without touching them. Jobs and internships are not separate JSearch endpoints — JSearch returns a mixed pool per query, which is classified locally as `"internship"` or `"job"` (only when provider metadata or the title clearly says so — never guessed) and both run through the exact same matching/AI/ranking code path; there is no separate engine per type.

Every opportunity returned originates from the live provider — there is no local/fake job dataset. If RapidAPI is unavailable, rate-limited, or unconfigured, the endpoint returns `{"recommendations": [], "source_status": "unavailable", "message": "..."}` instead of failing. If the primary query fails but the secondary query still returns data (or vice versa), that data is still returned (`source_status: "ok"`) — a single query failure never blanks out working data. The UI shows a matching "temporarily unavailable" empty state only when nothing could be fetched at all.

**Note on RapidAPI quota:** JSearch's Basic plan enforces a small monthly request quota. At most two provider requests are made per recommendation request (`OPPORTUNITY_CACHE_TTL_SECONDS` caches each exact query) — never more, regardless of how many users/pages hit the endpoint — and a 429 triggers an in-memory backoff (`OPPORTUNITY_QUOTA_BACKOFF_SECONDS`) so a spent quota fails fast instead of being hit again on every request. A 429 response means the plan is spent, not a bug — check usage at your RapidAPI dashboard.

---

## Career Outcomes: How the Relevance Engine Works

```
Student opts in (POST /api/outcomes/consent) — nothing below runs without this
  → enrolls in a training program (POST /api/outcomes/enrollment)
  → reports placement/employment (POST /api/outcomes/employment)
      job title + company + salary, all optional beyond status
  → deterministic training-to-job relevance (app.services.training_intelligence)
      training program's skills vs. the job title/role — keyword + skill-normalization
      matching, same alias layer used by opportunity matching, no AI call
      → relevance score (0-100) + label (e.g. HIGH RELEVANCE), always explainable
  → placement readiness score — skill coverage + evidence confidence + training completion
  → periodic check-ins (POST /api/outcomes/check-in) extend the timeline:
      still-employed status, salary, optional reason for leaving
  → GET /api/outcomes/timeline assembles training + placement + salary progression + check-ins
  → AI-assisted analysis (non-placement reasons, attrition risk, plain-language relevance
    explanation) is generated separately and labeled advisory-only — it explains the
    deterministic numbers, it never computes or overrides them
```

Every number a government administrator sees on `/admin/outcomes` is an aggregation of these same deterministic, per-student records — never an AI estimate, and never shown for a cohort smaller than `MIN_COHORT_SIZE` (5), regardless of role or filter.

---

## Pre-Seeded Data

- **100+ skills** across 15 categories (Programming, Web Dev, Data Science, DevOps, Cloud, Soft Skills, Database, Design, Security, Management, Tools, Academic, Blockchain, AR/VR, Quality)
- **45+ interests** across 5 categories (Technology, Data, Academic, Business, Creative, Social)
- **22+ career paths** with required skills, importance weights, and learning sequences
- **20 assessment questions** measuring 8 cognitive dimensions
- **13+ project recommendations** tied to career paths
- **1 pre-seeded admin account** (`admin@nextpath.gov`) for the government dashboard
- **Idempotent demo outcome dataset** (`POST /api/admin/outcomes/demo-data`) — 11 synthetic trainees across two clearly-labeled `(Demo)` providers, one deliberately below `MIN_COHORT_SIZE` to demonstrate suppression

---

## Demo & Admin Access

| Role | How to access | Credentials |
|------|----------------|-------------|
| Student (demo) | `POST /api/demo/load` (also wired to a "Try Demo" button on the frontend) loads a fully pre-filled profile (Aarav Sharma) and returns a JWT | — |
| Government admin | Log in at `/login` | `admin@nextpath.gov` / `Admin@12345` (demo credentials — rotate before any real deployment) |

An `is_admin` account is routed to `/admin/outcomes`; a regular student account is routed to `/dashboard`. The two views share no data path — the admin dashboard only ever reads aggregated cohort metrics, never a specific student's record.

---

## Available Scripts

### Frontend

| Script | Command | Description |
|--------|---------|-------------|
| `npm run dev` | `next dev` | Start development server |
| `npm run build` | `next build` | Build for production |
| `npm run start` | `next start` | Start production server |
| `npm run lint` | `next lint` | Run ESLint |

### Backend

| Command | Description |
|---------|-------------|
| `uvicorn app.main:app --reload` | Start dev server with auto-reload |
| `pytest` | Run tests (612+ tests) |

---

## License

This project is for educational and demonstration purposes.

# Next Path AI

**Your Career Path, Personalized by AI**

Next Path AI is an AI-powered career guidance platform that analyzes your skills, interests, and goals to recommend personalized career paths with actionable roadmaps, skill gap analysis, AI coaching, and much more.

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
- **Live Provider Data** — Real internships and jobs fetched from the RapidAPI "Internships API" provider (Career Site API for internships, Job Board API for jobs), never a local/fake dataset
- **One Provider Abstraction** — `opportunity_provider.py` is the only module that talks to RapidAPI; the matching/recommendation layer is provider-agnostic, so swapping providers later doesn't touch the matching engine
- **Skill Normalization Layer** — Deterministic alias resolution (React/React.js/React JS, Node/NodeJS/Node.js, HTML+CSS → HTML/CSS, etc.) so external postings match your skill profile without string-equality guesswork
- **Weighted Skill Matching** — Match score reflects proficiency, not just skill-name overlap (matched/partial/missing breakdown, each tied to your actual proficiency level)
- **AI Contextual Analysis** — Groq reasons about transferable skills and role centrality for top candidates only, blended with (never overriding) the deterministic score
- **Minimal Upstream Calls** — Exactly one provider request per opportunity type per cache window; no role-discovery fan-out, so a low RapidAPI quota isn't exhausted by normal use
- **Skill-Gap → Roadmap/Project Loop** — Missing skills on a listing link directly to your roadmap and skill-aware project recommendations
- **Graceful, Partial-Aware Degradation** — RapidAPI outages/rate limits/quota exhaustion never crash the app; if only one opportunity type fails (e.g. jobs down, internships fine) the data that did load is still shown, with a clear message about what's missing

### Adaptive Systems
- **Adaptive Roadmaps** — Phases auto-adapt based on proficiency (skip adapted phases, reduce duration for known skills)
- **Adaptive Event System** — Cascading updates triggered by skill assessments, project completions, resume/job analyses
- **Next Best Action** — AI-powered prioritization of 7 action types by career impact
- **Skill-Aware Projects** — Composite scoring combining career relevance, gap relevance, roadmap relevance, and difficulty fit

### AI Integration
- **Multi-Model AI** — Groq-powered assessment, project generation, and career coaching with model fallback and rate limit handling
- **Deterministic Fallbacks** — Every AI feature has a non-AI fallback for reliability
- **AI Project Generation** — Generate custom project recommendations based on skill levels, gaps, and roadmap phase
- **Conversation-Aware Coaching** — Coach maintains chat history for follow-up questions (e.g., "Why?", "Tell me more") while always re-fetching fresh user context from the database
- **Security Hardening** — Prompt injection protection, evidence source transparency (assessed vs. self-reported vs. project-backed), and strict context-only data usage

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
│   │   ├── main.py              # FastAPI entry point
│   │   ├── api/                 # Route handlers (auth, profile, careers, etc.)
│   │   ├── models/              # SQLAlchemy ORM models (20+ models)
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # Business logic (matching, gaps, roadmaps, etc.)
│   │   ├── database/            # DB config, migrations, seed data
│   │   ├── ai/                  # OpenAI & Groq integration
│   │   └── utils/               # Auth utilities
│   ├── tests/                   # 340+ backend tests
│   └── requirements.txt         # Python dependencies
│
└── frontend/
    ├── app/
    │   ├── page.tsx             # Landing page
    │   ├── (auth)/              # Login & register pages
    │   └── (dashboard)/         # Authenticated routes
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
    │       └── opportunities/   # AI-personalized jobs & internships (live provider data)
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
    │   └── opportunities/       # Opportunity cards (match score, skill gaps, apply)
    ├── hooks/                   # Custom React hooks (useAuth)
    ├── lib/                     # API client (40+ methods) and utilities
    └── types/                   # TypeScript interfaces (438 lines)
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

# Opportunity provider (RapidAPI "Internships API") — powers Jobs & Internships
# recommendations. Career Site API endpoint = internships, Job Board API
# endpoint = jobs, both on this one RapidAPI product.
# Without this, the feature degrades gracefully (empty list + "temporarily
# unavailable" message) instead of breaking the app.
OPPORTUNITY_RAPIDAPI_KEY=your-rapidapi-key-here
OPPORTUNITY_RAPIDAPI_HOST=internships-api.p.rapidapi.com
OPPORTUNITY_CACHE_TTL_SECONDS=900
OPPORTUNITY_QUOTA_BACKOFF_SECONDS=3600

# Opportunity match scoring weights (deterministic skill score vs AI contextual score)
OPPORTUNITY_DETERMINISTIC_WEIGHT=0.6
OPPORTUNITY_AI_WEIGHT=0.4
OPPORTUNITY_AI_TOP_N=5
OPPORTUNITY_MAX_SKILL_EXTRACTIONS=20
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

---

## Jobs & Internships: How the Matching Pipeline Works

```
Authenticated user (JWT)
  → user's demonstrated skills + proficiency (app.services.opportunity_recommendation.get_user_skill_map)
  → skill normalization (app.services.skill_normalization — aliases, no LLM calls)
  → live provider data (app.services.opportunity_provider — RapidAPI "Internships API")
      ├── Career Site API (/active-jb-7d)  -> internships
      └── Job Board API   (/active-ats-7d) -> jobs
    (cached, deduped by id/URL, expired postings filtered by date_validthrough)
  → required-skill extraction (this provider has no explicit skills field on
    ANY posting, so Groq extracts from title+description; results are cached
    per posting and capped at OPPORTUNITY_MAX_SKILL_EXTRACTIONS new calls
    per request so a large result set can't trigger unbounded AI usage)
  → deterministic weighted skill matching (app.services.opportunity_matching — proficiency-aware, 0-100 score)
  → AI contextual analysis for top candidates only (app.ai.groq_client.analyze_opportunity_match)
  → hybrid final score (deterministic × 0.6 + AI × 0.4, configurable via env)
  → ranked, filtered results
  → GET /api/opportunities/recommendations
  → frontend opportunity cards (/opportunities, and "Opportunities For You" on the dashboard)
```

`opportunity_provider.py` is the only module that knows about RapidAPI — the matching engine, AI analysis, ranking, and frontend are all provider-agnostic, so the provider could be swapped again without touching them. Both internships and jobs run through the exact same matching/AI/ranking code path; there is no separate engine per type.

Every opportunity returned originates from the live provider — there is no local/fake job dataset. If RapidAPI is unavailable, rate-limited, or unconfigured, the endpoint returns `{"recommendations": [], "source_status": "unavailable", "message": "..."}` instead of failing. If only one type fails (e.g. jobs down but internships fine), the data that *did* load is still returned (`source_status: "ok"`) with an informational message about what's missing — a partial provider outage never blanks out working data. The UI shows a matching "temporarily unavailable" empty state only when nothing could be fetched at all.

**Note on RapidAPI quota:** opportunity-data providers on RapidAPI commonly enforce small monthly request quotas. Exactly one provider request is made per opportunity type per cache window (`OPPORTUNITY_CACHE_TTL_SECONDS`) — never more, regardless of how many users/pages hit the endpoint — and a 429 triggers an in-memory backoff (`OPPORTUNITY_QUOTA_BACKOFF_SECONDS`) so a spent quota fails fast instead of being hit again on every request. A 429 response means the plan is spent, not a bug — check usage at your RapidAPI dashboard.

---

## Pre-Seeded Data

- **100+ skills** across 15 categories (Programming, Web Dev, Data Science, DevOps, Cloud, Soft Skills, Database, Design, Security, Management, Tools, Academic, Blockchain, AR/VR, Quality)
- **45+ interests** across 5 categories (Technology, Data, Academic, Business, Creative, Social)
- **22+ career paths** with required skills, importance weights, and learning sequences
- **20 assessment questions** measuring 8 cognitive dimensions
- **13+ project recommendations** tied to career paths

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
| `pytest` | Run tests (340+ tests) |

---

## License

This project is for educational and demonstration purposes.

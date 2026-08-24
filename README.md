# PathPilot AI

**Your Career Path, Personalized by AI**

PathPilot AI is an AI-powered career guidance platform that analyzes your skills, interests, and goals to recommend personalized career paths with actionable roadmaps, skill gap analysis, and AI coaching.

---

## Features

- **User Authentication** — Register, login, and secure JWT-based sessions
- **Multi-Step Onboarding** — Profile setup covering education, experience, interests, and skills
- **Career Fit Assessment** — 20-question assessment measuring 8 dimensions (technical interest, problem solving, creativity, communication, etc.)
- **AI Career Recommendations** — Weighted matching algorithm scoring careers on skill alignment, interests, assessment results, and experience
- **Skill Gap Analysis** — Compare your current skills against career requirements with priority levels
- **Personalized Learning Roadmaps** — 4-6 phase learning plans with skills, activities, projects, and duration estimates
- **Project Recommendations** — Curated projects tied to careers with difficulty levels and portfolio value
- **Progress Tracking** — Dashboard with readiness scores, phase completion, and weekly actions
- **AI Coach** — Chat-based career coaching using your full profile context
- **Demo Mode** — Pre-loaded sample data for quick testing

---

## Tech Stack

### Frontend

| Technology | Purpose |
|------------|---------|
| Next.js 14 (App Router) | React framework with SSR/SSG |
| TypeScript 5 | Type safety |
| Tailwind CSS 3.4 | Styling |
| Radix UI + shadcn/ui | Accessible UI components |
| Recharts | Data visualization |
| Lucide React | Icons |

### Backend

| Technology | Purpose |
|------------|---------|
| FastAPI | Python web framework |
| SQLAlchemy 2.0 | ORM and database management |
| SQLite / PostgreSQL | Database (SQLite for dev, PostgreSQL for prod) |
| Pydantic 2.5 | Data validation |
| OpenAI GPT-4 | AI-powered roadmaps and coaching (optional) |
| JWT + bcrypt | Authentication and security |
| Alembic | Database migrations |

---

## Project Structure

```
pathpilot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── api/                 # Route handlers (auth, profile, careers, etc.)
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # Business logic (matching, gaps, roadmaps)
│   │   ├── database/            # DB config, migrations, seed data
│   │   ├── ai/                  # OpenAI integration
│   │   └── utils/               # Auth utilities
│   ├── tests/                   # Backend tests
│   └── requirements.txt         # Python dependencies
│
└── frontend/
    ├── app/
    │   ├── page.tsx             # Landing page
    │   ├── (auth)/              # Login & register pages
    │   └── (dashboard)/         # Authenticated routes
    │       ├── dashboard/
    │       ├── onboarding/
    │       ├── assessment/
    │       ├── careers/
    │       ├── skills/
    │       ├── roadmap/
    │       ├── projects/
    │       └── coach/
    ├── components/              # Reusable UI components
    │   ├── ui/                  # Base UI primitives
    │   ├── landing/             # Landing page sections
    │   ├── dashboard/           # Dashboard widgets
    │   ├── career/              # Career-related components
    │   └── ...
    ├── hooks/                   # Custom React hooks
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
DATABASE_URL=sqlite:///pathpilot.db

# OpenAI (optional — app works without it using deterministic fallback)
OPENAI_API_KEY=your-api-key-here

# JWT Secret (change in production)
JWT_SECRET=your-secret-key-here
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login and receive JWT |
| GET | `/api/auth/me` | Get current user |
| GET/PUT | `/api/profile` | Get or update user profile |
| GET | `/api/skills` | List available skills |
| GET | `/api/interests` | List available interests |
| GET/POST | `/api/assessment` | Get questions or submit answers |
| GET | `/api/careers` | List career paths |
| POST | `/api/careers/recommend` | Get personalized career recommendations |
| POST | `/api/skill-gap` | Analyze skill gaps for a career |
| GET/POST | `/api/roadmap` | Get or generate learning roadmap |
| GET | `/api/projects` | Get project recommendations |
| GET | `/api/progress` | Get progress dashboard data |
| POST | `/api/coach` | Chat with AI career coach |
| POST | `/api/demo/load` | Load demo data |

---

## How It Works

1. **Sign up** and complete the multi-step onboarding to fill your profile
2. **Take the assessment** — answer 20 questions about your strengths and preferences
3. **Get career recommendations** — the algorithm matches you to 19+ career paths using weighted scoring
4. **View skill gaps** — see exactly what skills you need to develop for each career
5. **Follow your roadmap** — personalized 4-6 phase learning plan with milestones
6. **Build projects** — curated project ideas to build your portfolio
7. **Track progress** — monitor your readiness scores and phase completion
8. **Chat with AI Coach** — ask career questions and get personalized advice

---

## Pre-Seeded Data

- **35+ skills** across 10 categories (Programming, Web Dev, Data Science, DevOps, etc.)
- **22 interests** across 5 categories (Technology, Data, Business, Creative, Social)
- **19 career paths** (Full Stack Developer, Data Scientist, ML Engineer, UX Designer, etc.)
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
| `pytest` | Run tests |

---

## License

This project is for educational and demonstration purposes.

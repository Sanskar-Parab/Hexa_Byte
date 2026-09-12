# Next Path AI

**Your Career Path, Personalized by AI**

Next Path AI is an AI-powered career guidance platform that analyzes your skills, interests, and goals to recommend personalized career paths with actionable roadmaps, skill gap analysis, AI coaching, and much more. It also includes a full employment outcome tracking system built for the Maharashtra Government "Smart Education" problem statement that follows students from training enrollment through placement and retention, and surfaces privacy-preserving, cohort-level analytics to government/provider stakeholders through a dedicated admin dashboard.

---

## Features

### Core Features

- **User Authentication** â€” Register, login, and secure JWT-based sessions (7-day expiry)
- **Multi-Step Onboarding** â€” 4-step profile setup: Basic Info, Experience, Interests, Skills
- **Career Fit Assessment** â€” 20-question assessment measuring 8 cognitive dimensions
- **AI Career Recommendations** â€” Weighted matching algorithm scoring careers on skill alignment, interests, assessment results, and experience
- **Skill Gap Analysis** â€” Compare current skills against career requirements with priority levels and severity
- **Personalized Learning Roadmaps** â€” Adaptive 4-6 phase learning plans with skills, activities, projects, and duration estimates
- **Progress Tracking** â€” Dashboard with readiness scores, phase completion, weekly actions, and 7-day charts
- **AI Coach** â€” Context-aware career coaching with conversation history support, intent detection, suggestions, truth enforcement, and security hardening
- **Demo Mode** â€” Pre-loaded sample data (Aarav Sharma) for instant testing

### Skill Management

- **Skill Evidence System** â€” Multi-source evidence tracking (assessment, project, resume, job, manual) with confidence levels (LOW/MEDIUM/HIGH)
- **AI Skill Assessment** â€” 10-question MCQ assessment powered by Groq API with proficiency scoring and analysis
- **Confidence Auto-Recomputation** â€” Skill confidence recalculated automatically when evidence changes

### Resume & Job Analysis

- **Resume Upload & Parsing** â€” PDF upload with automatic section extraction (skills, experience, education, projects)
- **Skill Extraction** â€” Cross-references resume content against skill database with evidence creation
- **Job Description Analysis** â€” Paste job descriptions to analyze skill match and alignment percentage
- **Skill Matching** â€” Fuzzy/partial matching (React.js matches React) with strong/developing/missing breakdowns

### Jobs & Internships (AI-Personalized Recommendations)

- **Live Provider Data** â€” Real jobs and internships fetched from JSearch (by OpenWeb Ninja, via RapidAPI), never a local/fake dataset
- **India-First** â€” Every search is scoped server-side to India (country=in); recommendations are India-only by default
- **One Provider Abstraction** â€” `opportunity_provider.py` is the only module that talks to RapidAPI; the matching/recommendation layer is provider-agnostic
- **Career-Aware Search** â€” Search queries are generated from the user's target career (falling back to their strongest skill)
- **Skill Normalization Layer** â€” Deterministic alias resolution (React/React.js/React JS, Node/NodeJS/Node.js, HTML+CSS -> HTML/CSS, etc.)
- **Weighted Skill Matching** â€” Match score reflects proficiency, not just skill-name overlap
- **Beginner-Priority Ranking** â€” Internship/entry-level postings get a small ranking boost for beginner users
- **AI Contextual Analysis** â€” Groq reasons about transferable skills and role centrality for top candidates only
- **Minimal Upstream Calls** â€” At most two provider requests per recommendation request
- **Graceful Degradation** â€” RapidAPI outages/rate limits never crash the app

### Adaptive Systems

- **Adaptive Roadmaps** â€” Phases auto-adapt based on proficiency (skip adapted phases, reduce duration for known skills)
- **Adaptive Event System** â€” Cascading updates triggered by skill assessments, project completions, resume/job analyses
- **Next Best Action** â€” AI-powered prioritization of 10 action types by career impact, including 3 outcome-aware types
- **Skill-Aware Projects** â€” Composite scoring combining career relevance, gap relevance, roadmap relevance, and difficulty fit

### AI Integration

- **Multi-Model AI** â€” Groq-powered assessment, project generation, and career coaching with model fallback and rate limit handling
- **Deterministic Fallbacks** â€” Every AI feature has a non-AI fallback for reliability
- **AI Project Generation** â€” Generate custom project recommendations based on skill levels, gaps, and roadmap phase
- **Conversation-Aware Coaching** â€” Coach maintains chat history for follow-up questions while re-fetching fresh user context
- **Security Hardening** â€” Prompt injection protection, evidence source transparency, and strict context-only data usage

### Employment Outcome Tracking (Career Outcomes)

Built for the Maharashtra Government "Smart Education" problem statement.

- **Consent-Gated Reporting** â€” Students opt in before any outcome data is recorded; consent can be revoked at any time
- **Training Enrollment & Placement** â€” Self-report training program enrollment, placement/employment status, job title, company, location, and salary
- **Longitudinal Check-Ins** â€” Periodic check-ins track continued employment, salary progression, and reasons for leaving
- **Evidence Levels** â€” Employment outcomes support evidence levels: self_reported, evidence_submitted, verified
- **Deterministic Training-Skill Relevance** â€” Job title/skills matched against training program skills with transparent relevance score
- **Placement Readiness Scoring** â€” Deterministic score combining skill coverage, evidence confidence, and training completion
- **AI-Assisted Analysis (advisory only)** â€” Non-placement reason analysis, attrition risk analysis, and plain-language relevance explanations
- **Adaptive Curriculum Loop** â€” Recurring skill gaps feed back into curriculum recommendations per program

### Government Admin Dashboard (Privacy-Preserving Analytics)

A separate is_admin-gated area for tracking skilling-initiative impact in aggregate.

- **Cohort-Level Aggregation Only** â€” Every metric computed over a cohort; cohorts smaller than MIN_COHORT_SIZE (5) are suppressed
- **Overview, Provider, Program & Retention Views** â€” Placement rate, salary, retention curves, provider/program comparison
- **Skill Gap & Non-Placement Analysis** â€” Aggregate view of most common missing skills and non-placement reasons
- **Curriculum Recommendations** â€” Surfaces recurring skill gaps (>=30% of a cohort) as curriculum suggestions per program
- **Demo Dataset Labeling** â€” Synthetic demo data clearly labeled and counted separately in every view
- **Employment Outcome Verification** â€” Admin queue for reviewing and verifying student-reported outcomes
- **Student Evidence Review** â€” View evidence submitted by students for employment outcomes

### Trainee Identity Resolution (SIH 26135)

- **Deterministic Matching** â€” Fuzzy field-level scoring (name, DOB, phone, program) with confidence thresholds
- **Master Trainee Records** â€” Deduplicated identity records with masked phone numbers, linked user accounts
- **Program Record Linking** â€” Multiple program enrollments linked to a single master identity
- **Identity Review Workflow** â€” Medium/low confidence records queued for manual admin review
- **Admin Trainee Management** â€” Paginated trainee list with search, detail view, and longitudinal outcome data


---

## Tech Stack

### Frontend

| Technology              | Purpose                                        |
| ----------------------- | ---------------------------------------------- |
| Next.js 14 (App Router) | React framework with SSR/SSG                   |
| TypeScript 5            | Type safety                                    |
| Tailwind CSS 3.4        | Utility-first styling with custom design tokens |
| Radix UI + shadcn/ui    | Accessible UI components                       |
| Recharts                | Data visualization (charts, retention curves)  |
| Lucide React            | Icons                                          |
| date-fns                | Date utilities                                 |

### Backend

| Technology          | Purpose                                                    |
| ------------------- | ---------------------------------------------------------- |
| FastAPI             | Python async web framework                                 |
| SQLAlchemy 2.0      | ORM and database management                                |
| SQLite / PostgreSQL | Database (SQLite for dev, PostgreSQL for prod)             |
| Pydantic 2.5        | Data validation schemas                                    |
| Groq API            | AI skill assessment, project generation, career coaching   |
| OpenAI API          | Optional AI integration for roadmaps and career explanations |
| PyPDF2              | Resume PDF text extraction                                 |
| JWT + bcrypt        | Authentication and security (7-day token expiry)           |
| Alembic             | Database migrations                                        |
| pandas              | Data manipulation                                          |

---

## Project Structure

```
Hexa_Byte/
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ main.py              # FastAPI entry point (CORS, router registration, startup migrations)
â”‚   â”‚   â”œâ”€â”€ api/                 # Route handlers (27 modules)
â”‚   â”‚   â”‚   â”œâ”€â”€ auth.py          # Register, login, logout, current user
â”‚   â”‚   â”‚   â”œâ”€â”€ profile.py       # Get/update profile, multi-step onboarding
â”‚   â”‚   â”‚   â”œâ”€â”€ skills.py        # CRUD for user skills with proficiency
â”‚   â”‚   â”‚   â”œâ”€â”€ interests.py     # CRUD for user interests
â”‚   â”‚   â”‚   â”œâ”€â”€ assessment.py    # 20-question career fit assessment
â”‚   â”‚   â”‚   â”œâ”€â”€ careers.py       # Career list, detail, recommendations, intelligence
â”‚   â”‚   â”‚   â”œâ”€â”€ skill_gap.py     # Skill gap analysis for a career
â”‚   â”‚   â”‚   â”œâ”€â”€ roadmap.py       # Generate/update adaptive learning roadmaps
â”‚   â”‚   â”‚   â”œâ”€â”€ projects.py      # Skill-aware project recommendations, AI generation
â”‚   â”‚   â”‚   â”œâ”€â”€ progress.py      # Progress dashboard data and updates
â”‚   â”‚   â”‚   â”œâ”€â”€ coach.py         # AI career coach with context + suggestions
â”‚   â”‚   â”‚   â”œâ”€â”€ skill_assessment.py  # AI-powered MCQ skill assessments
â”‚   â”‚   â”‚   â”œâ”€â”€ evidence.py      # Skill evidence tracking
â”‚   â”‚   â”‚   â”œâ”€â”€ next_best_action.py  # AI-powered prioritized next actions
â”‚   â”‚   â”‚   â”œâ”€â”€ resume.py        # PDF resume upload and parsing
â”‚   â”‚   â”‚   â”œâ”€â”€ job_analysis.py  # Job description analysis
â”‚   â”‚   â”‚   â”œâ”€â”€ opportunities.py # Live job/internship recommendations
â”‚   â”‚   â”‚   â”œâ”€â”€ demo.py          # Load demo user data
â”‚   â”‚   â”‚   â”œâ”€â”€ outcomes.py      # Career outcomes: consent, enrollment, employment, check-ins
â”‚   â”‚   â”‚   â”œâ”€â”€ outcome_timeline.py  # Full outcome timeline assembly
â”‚   â”‚   â”‚   â”œâ”€â”€ outcome_ai.py    # AI-assisted outcome analysis (advisory only)
â”‚   â”‚   â”‚   â”œâ”€â”€ training_intelligence.py  # Deterministic training-skill relevance
â”‚   â”‚   â”‚   â”œâ”€â”€ admin_analytics.py  # Government dashboard cohort-level analytics
â”‚   â”‚   â”‚   â”œâ”€â”€ admin_outcomes.py   # Admin outcome verification + student evidence
â”‚   â”‚   â”‚   â””â”€â”€ trainee_identity.py # Trainee identity resolution (SIH 26135)
â”‚   â”‚   â”œâ”€â”€ models/              # SQLAlchemy ORM models (18 modules)
â”‚   â”‚   â”‚   â”œâ”€â”€ user.py          # User with is_admin, is_demo, preferred_difficulty
â”‚   â”‚   â”‚   â”œâ”€â”€ profile.py       # User profile (education, experience)
â”‚   â”‚   â”‚   â”œâ”€â”€ skill.py         # Skill + UserSkill with confidence/level_name
â”‚   â”‚   â”‚   â”œâ”€â”€ skill_evidence.py # Multi-source evidence tracking
â”‚   â”‚   â”‚   â”œâ”€â”€ skill_assessment.py # AI skill assessment sessions
â”‚   â”‚   â”‚   â”œâ”€â”€ interest.py      # Interest + UserInterest
â”‚   â”‚   â”‚   â”œâ”€â”€ career.py        # Career + CareerRecommendation
â”‚   â”‚   â”‚   â”œâ”€â”€ assessment.py    # AssessmentQuestion + UserAssessment
â”‚   â”‚   â”‚   â”œâ”€â”€ roadmap.py       # Roadmap + RoadmapPhase with adaptation_mode
â”‚   â”‚   â”‚   â”œâ”€â”€ project.py       # Project + RecommendedProject + AIGeneratedProject
â”‚   â”‚   â”‚   â”œâ”€â”€ progress.py      # UserProgress tracking
â”‚   â”‚   â”‚   â”œâ”€â”€ resume.py        # Resume storage
â”‚   â”‚   â”‚   â”œâ”€â”€ job_analysis.py  # Job analysis results
â”‚   â”‚   â”‚   â”œâ”€â”€ outcome.py       # TrainingProgram, Enrollment, EmploymentOutcome, CheckIn, Consent
â”‚   â”‚   â”‚   â”œâ”€â”€ trainee_identity.py # MasterTrainee, TraineeProgramRecord, IdentityReview
â”‚   â”‚   â”‚   â””â”€â”€ types.py         # Shared type definitions
â”‚   â”‚   â”œâ”€â”€ schemas/             # Pydantic request/response schemas (21 modules)
â”‚   â”‚   â”œâ”€â”€ services/            # Business logic (29 modules)
â”‚   â”‚   â”‚   â”œâ”€â”€ career_matching.py       # Weighted career matching algorithm
â”‚   â”‚   â”‚   â”œâ”€â”€ skill_gap.py             # Skill gap computation
â”‚   â”‚   â”‚   â”œâ”€â”€ roadmap_service.py       # Adaptive roadmap generation
â”‚   â”‚   â”‚   â”œâ”€â”€ skill_aware_projects.py  # Composite project scoring
â”‚   â”‚   â”‚   â”œâ”€â”€ skill_normalization.py   # Alias resolution layer
â”‚   â”‚   â”‚   â”œâ”€â”€ opportunity_provider.py  # JSearch/RapidAPI integration
â”‚   â”‚   â”‚   â”œâ”€â”€ opportunity_matching.py  # Proficiency-aware skill matching
â”‚   â”‚   â”‚   â”œâ”€â”€ opportunity_recommendation.py  # Full recommendation pipeline
â”‚   â”‚   â”‚   â”œâ”€â”€ coach_service.py         # AI coach with context injection + truth enforcement
â”‚   â”‚   â”‚   â”œâ”€â”€ adaptive_events.py       # 4 event functions + cascade logic
â”‚   â”‚   â”‚   â”œâ”€â”€ next_best_action.py      # 10 action types with career impact scoring
â”‚   â”‚   â”‚   â”œâ”€â”€ skill_assessment_service.py  # AI MCQ assessment flow
â”‚   â”‚   â”‚   â”œâ”€â”€ evidence_service.py      # Evidence CRUD + confidence recomputation
â”‚   â”‚   â”‚   â”œâ”€â”€ assessment_service.py    # Career fit assessment scoring
â”‚   â”‚   â”‚   â”œâ”€â”€ resume_service.py        # PDF parsing + skill extraction
â”‚   â”‚   â”‚   â”œâ”€â”€ job_analysis_service.py  # Job description analysis
â”‚   â”‚   â”‚   â”œâ”€â”€ progress_service.py      # Dashboard data assembly
â”‚   â”‚   â”‚   â”œâ”€â”€ project_service.py       # Project recommendations + difficulty
â”‚   â”‚   â”‚   â”œâ”€â”€ readiness.py             # Placement readiness scoring
â”‚   â”‚   â”‚   â”œâ”€â”€ outcome_service.py       # Outcome CRUD operations
â”‚   â”‚   â”‚   â”œâ”€â”€ outcome_timeline.py      # Timeline assembly
â”‚   â”‚   â”‚   â”œâ”€â”€ outcome_ai_analysis.py   # AI-assisted outcome analysis
â”‚   â”‚   â”‚   â”œâ”€â”€ training_intelligence.py # Deterministic training relevance
â”‚   â”‚   â”‚   â”œâ”€â”€ admin_analytics.py       # Cohort-level analytics
â”‚   â”‚   â”‚   â”œâ”€â”€ demo_outcome_seed.py     # Synthetic demo outcome data
â”‚   â”‚   â”‚   â”œâ”€â”€ identity_matching.py     # Fuzzy trainee identity matching
â”‚   â”‚   â”‚   â””â”€â”€ trainee_identity_service.py  # Master trainee CRUD
â”‚   â”‚   â”œâ”€â”€ ai/                  # AI integration layer
â”‚   â”‚   â”‚   â”œâ”€â”€ client.py        # OpenAI client (roadmaps, career explanations)
â”‚   â”‚   â”‚   â”œâ”€â”€ groq_client.py   # Groq client (assessment, coaching, matching, analysis)
â”‚   â”‚   â”‚   â””â”€â”€ project_generator.py  # Groq-powered project generation
â”‚   â”‚   â”œâ”€â”€ database/            # DB config, migrations, seed data
â”‚   â”‚   â”‚   â”œâ”€â”€ config.py        # SQLAlchemy engine + session factory
â”‚   â”‚   â”‚   â”œâ”€â”€ migrations.py    # Auto-migration on startup
â”‚   â”‚   â”‚   â””â”€â”€ seed.py          # 100+ skills, 45+ interests, 22+ careers, admin user
â”‚   â”‚   â”œâ”€â”€ utils/
â”‚   â”‚   â”‚   â””â”€â”€ auth.py          # JWT creation/verification, password hashing, admin dependency
â”‚   â”‚   â””â”€â”€ recommendation/      # (reserved for future recommendation modules)
â”‚   â”œâ”€â”€ tests/                   # 38 test modules
â”‚   â”‚   â”œâ”€â”€ conftest.py          # Shared fixtures
â”‚   â”‚   â”œâ”€â”€ test_adaptive_events.py
â”‚   â”‚   â”œâ”€â”€ test_admin_analytics.py / test_admin_analytics_api.py
â”‚   â”‚   â”œâ”€â”€ test_assessment.py
â”‚   â”‚   â”œâ”€â”€ test_career_matching.py
â”‚   â”‚   â”œâ”€â”€ test_coach_service.py
â”‚   â”‚   â”œâ”€â”€ test_curriculum_recommendations.py
â”‚   â”‚   â”œâ”€â”€ test_evidence.py
â”‚   â”‚   â”œâ”€â”€ test_groq_client.py
â”‚   â”‚   â”œâ”€â”€ test_job_analysis_service.py / test_job_api.py
â”‚   â”‚   â”œâ”€â”€ test_next_best_action.py / test_next_best_action_outcomes.py
â”‚   â”‚   â”œâ”€â”€ test_opportunities_api.py / test_opportunity_matching.py
â”‚   â”‚   â”œâ”€â”€ test_opportunity_provider.py / test_opportunity_recommendation.py
â”‚   â”‚   â”œâ”€â”€ test_outcome_ai_analysis.py / test_outcome_ai_api.py
â”‚   â”‚   â”œâ”€â”€ test_outcome_ai_groq_client.py / test_outcome_schemas.py
â”‚   â”‚   â”œâ”€â”€ test_outcome_service.py / test_outcome_timeline.py
â”‚   â”‚   â”œâ”€â”€ test_outcome_timeline_api.py / test_outcome_unreachable_consent.py
â”‚   â”‚   â”œâ”€â”€ test_outcomes_api.py
â”‚   â”‚   â”œâ”€â”€ test_resume_api.py / test_resume_service.py
â”‚   â”‚   â”œâ”€â”€ test_roadmap_adaptive.py
â”‚   â”‚   â”œâ”€â”€ test_skill_assessment.py / test_skill_aware_projects.py
â”‚   â”‚   â”œâ”€â”€ test_skill_gap.py / test_skill_normalization.py
â”‚   â”‚   â””â”€â”€ test_training_intelligence.py / test_training_intelligence_api.py
â”‚   â”œâ”€â”€ add_new_data.py          # Script to add additional skills/interests/careers/projects
â”‚   â”œâ”€â”€ requirements.txt         # Python dependencies
â”‚   â”œâ”€â”€ .env.example             # Backend environment variables template
â”‚   â””â”€â”€ nextpath.db              # SQLite database (auto-created)
â”‚
â”œâ”€â”€ frontend/
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ page.tsx             # Landing page (Hero, HowItWorks, Features, WhyChooseUs, Footer)
â”‚   â”‚   â”œâ”€â”€ layout.tsx           # Root layout with Inter + JetBrains Mono fonts
â”‚   â”‚   â”œâ”€â”€ globals.css          # Global styles + CSS custom properties
â”‚   â”‚   â”œâ”€â”€ (auth)/
â”‚   â”‚   â”‚   â”œâ”€â”€ login/page.tsx   # Login page
â”‚   â”‚   â”‚   â””â”€â”€ register/page.tsx # Registration page
â”‚   â”‚   â”œâ”€â”€ (dashboard)/         # Authenticated student routes (Header + Sidebar layout)
â”‚   â”‚   â”‚   â”œâ”€â”€ layout.tsx       # Dashboard layout with auth guard + progress tracking
â”‚   â”‚   â”‚   â”œâ”€â”€ dashboard/       # Main dashboard (readiness, skills, actions, charts)
â”‚   â”‚   â”‚   â”œâ”€â”€ onboarding/      # Multi-step profile setup
â”‚   â”‚   â”‚   â”œâ”€â”€ assessment/      # Career fit assessment + result/
â”‚   â”‚   â”‚   â”œâ”€â”€ careers/         # Career list + [id]/ detail
â”‚   â”‚   â”‚   â”œâ”€â”€ skills/          # Skill management + [id]/ detail
â”‚   â”‚   â”‚   â”œâ”€â”€ roadmap/         # Learning roadmap timeline
â”‚   â”‚   â”‚   â”œâ”€â”€ projects/        # Project recommendations + [id]/ detail
â”‚   â”‚   â”‚   â”œâ”€â”€ coach/           # AI career coach chat
â”‚   â”‚   â”‚   â”œâ”€â”€ resume/          # Resume upload & results
â”‚   â”‚   â”‚   â”œâ”€â”€ job-analyzer/    # Job description analysis
â”‚   â”‚   â”‚   â”œâ”€â”€ opportunities/   # AI-personalized jobs & internships
â”‚   â”‚   â”‚   â””â”€â”€ outcomes/        # Career outcomes reporting, check-ins, timeline
â”‚   â”‚   â””â”€â”€ admin/               # Government admin dashboard (is_admin-gated)
â”‚   â”‚       â”œâ”€â”€ layout.tsx       # Admin layout with nav: Outcomes, Trainees, Reviews
â”‚   â”‚       â”œâ”€â”€ outcomes/        # Cohort analytics dashboard
â”‚   â”‚       â”œâ”€â”€ trainees/        # Trainee identity management + [id]/ detail
â”‚   â”‚       â””â”€â”€ identity-reviews/ # Identity review queue for admin approval
â”‚   â”œâ”€â”€ components/
â”‚   â”‚   â”œâ”€â”€ ui/                  # Base UI primitives (18 components)
â”‚   â”‚   â”‚   â”œâ”€â”€ badge.tsx, button.tsx, card.tsx, dialog.tsx, input.tsx, label.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ tabs.tsx, select.tsx, slider.tsx, textarea.tsx, progress.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ empty-state.tsx, loading-state.tsx, route-loading.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ section-header.tsx, skill-bar.tsx, status-badge.tsx, evidence-badge.tsx
â”‚   â”‚   â”œâ”€â”€ layout/              # Header.tsx, Logo.tsx, Sidebar.tsx
â”‚   â”‚   â”œâ”€â”€ landing/             # Hero.tsx, HowItWorks.tsx, Features.tsx, WhyChooseUs.tsx, Footer.tsx
â”‚   â”‚   â”œâ”€â”€ dashboard/           # CareerOverview, DashboardHeader, NextBestAction, OpportunitiesForYou, ProgressChart, SkillGapOverview, WeeklyActions
â”‚   â”‚   â”œâ”€â”€ career/              # CareerCard, CareerDetail, SkillGapChart
â”‚   â”‚   â”œâ”€â”€ skills/              # SkillAssessment, SkillChip, SkillSelector
â”‚   â”‚   â”œâ”€â”€ assessment/          # AssessmentProgress, AssessmentQuestion
â”‚   â”‚   â”œâ”€â”€ roadmap/             # PhaseCard, RoadmapTimeline
â”‚   â”‚   â”œâ”€â”€ projects/            # ProjectCard
â”‚   â”‚   â”œâ”€â”€ coach/               # ChatInterface
â”‚   â”‚   â”œâ”€â”€ resume/              # ResumeUploader, ResumeResults
â”‚   â”‚   â”œâ”€â”€ job/                 # JobAnalyzer, JobMatchResults
â”‚   â”‚   â”œâ”€â”€ opportunities/       # OpportunityCard
â”‚   â”‚   â”œâ”€â”€ outcomes/            # CheckInHistory, OutcomeMilestoneTimeline, OutcomeSummaryCards, RelevanceBadge, ReportOutcomeForm, SalaryProgressionCard
â”‚   â”‚   â””â”€â”€ admin/               # MetricCard, FilterBar, DemoDatasetBanner, ProviderTable, ProgramTable, SkillGapChart, NonPlacementChart, RetentionChart, CurriculumRecommendations, VerificationQueue
â”‚   â”œâ”€â”€ hooks/
â”‚   â”‚   â””â”€â”€ useAuth.ts           # Auth hook: login, register, logout, loadDemo, checkAuth
â”‚   â”œâ”€â”€ lib/
â”‚   â”‚   â”œâ”€â”€ api.ts               # API client with JWT auth + all endpoint methods
â”‚   â”‚   â””â”€â”€ utils.ts             # cn(), formatDate, getInitials, getConfidenceColor, getDifficultyColor, formatCurrency, formatPercent, formatStatusLabel
â”‚   â”œâ”€â”€ types/
â”‚   â”‚   â””â”€â”€ index.ts             # TypeScript interfaces (859 lines, all domain models)
â”‚   â”œâ”€â”€ next.config.js           # API proxy rewrites to backend
â”‚   â”œâ”€â”€ tailwind.config.ts       # Custom design tokens, animations, shadows
â”‚   â”œâ”€â”€ tsconfig.json            # TypeScript configuration
â”‚   â””â”€â”€ postcss.config.js        # PostCSS configuration
â”‚
â”œâ”€â”€ docs/
â”‚   â””â”€â”€ PHASE7_FINAL_REPORT.md   # Phase 7 implementation report (AI Coach + Adaptive Events)
â”‚
â”œâ”€â”€ .env.example                 # Root environment variables template
â”œâ”€â”€ .gitignore                   # Git ignore rules
â”œâ”€â”€ package-lock.json            # Root lockfile
â””â”€â”€ run.txt                      # Quick start commands
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

# OpenAI (optional - app works without it using deterministic fallback)
OPENAI_API_KEY=your-openai-api-key-here

# Groq API (required for AI-powered skill assessment and project generation)
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=openai/gpt-oss-120b

# Opportunity provider (JSearch by OpenWeb Ninja, via RapidAPI)
# Subscribe at https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
# Without this, the feature degrades gracefully
OPPORTUNITY_RAPIDAPI_KEY=your-rapidapi-key-here
OPPORTUNITY_RAPIDAPI_HOST=jsearch.p.rapidapi.com
OPPORTUNITY_CACHE_TTL_SECONDS=3600
OPPORTUNITY_QUOTA_BACKOFF_SECONDS=3600

# Opportunity match scoring weights
OPPORTUNITY_DETERMINISTIC_WEIGHT=0.6
OPPORTUNITY_AI_WEIGHT=0.4
OPPORTUNITY_AI_TOP_N=5
OPPORTUNITY_MAX_SKILL_EXTRACTIONS=20

# CORS (defaults to localhost:3000,localhost:3001 in dev)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

> **Note:** The frontend requires no environment variables - API calls are proxied via Next.js rewrites.

---

## API Endpoints

### Authentication

| Method | Endpoint             | Description           |
| ------ | -------------------- | --------------------- |
| POST   | `/api/auth/register` | Register new user     |
| POST   | `/api/auth/login`    | Login and receive JWT |
| POST   | `/api/auth/logout`   | Logout                |
| GET    | `/api/auth/me`       | Get current user      |

### Profile

| Method   | Endpoint                  | Description                    |
| -------- | ------------------------- | ------------------------------ |
| GET/POST | `/api/profile`            | Get or update profile          |
| POST     | `/api/profile/onboarding` | Complete multi-step onboarding |

### Skills

| Method | Endpoint                 | Description                                      |
| ------ | ------------------------ | ------------------------------------------------ |
| GET    | `/api/skills`            | List all available skills                        |
| GET    | `/api/skills/user`       | List user's skills with proficiency & confidence |
| POST   | `/api/skills`            | Add a skill to user profile                      |
| PUT    | `/api/skills/{skill_id}` | Update skill proficiency                         |
| DELETE | `/api/skills/{skill_id}` | Remove a skill                                   |

### Interests

| Method | Endpoint                       | Description           |
| ------ | ------------------------------ | --------------------- |
| GET    | `/api/interests`               | List all interests    |
| GET    | `/api/interests/user`          | List user's interests |
| POST   | `/api/interests/{interest_id}` | Add interest          |
| DELETE | `/api/interests/{interest_id}` | Remove interest       |

### Assessment

| Method | Endpoint                    | Description                            |
| ------ | --------------------------- | -------------------------------------- |
| GET    | `/api/assessment/questions` | Get 20 assessment questions            |
| POST   | `/api/assessment/submit`    | Submit answers, get 8-dimension scores |
| GET    | `/api/assessment/result`    | Get latest assessment result           |

### Career Recommendations

| Method | Endpoint                         | Description                             |
| ------ | -------------------------------- | --------------------------------------- |
| GET    | `/api/careers`                   | List all career paths                   |
| GET    | `/api/careers/{id}`              | Get career detail                       |
| POST   | `/api/careers/recommend`         | Get personalized career recommendations |
| GET    | `/api/careers/recommendations`   | Get stored recommendations              |
| GET    | `/api/careers/{id}/intelligence` | Get full career intelligence            |

### Skill Gap Analysis

| Method | Endpoint                 | Description                     |
| ------ | ------------------------ | ------------------------------- |
| POST   | `/api/skill-gap/analyze` | Analyze skill gaps for a career |

### Roadmap

| Method | Endpoint                               | Description                            |
| ------ | -------------------------------------- | -------------------------------------- |
| POST   | `/api/roadmap/generate`                | Generate personalized learning roadmap |
| GET    | `/api/roadmap`                         | Get current roadmap                    |
| PUT    | `/api/roadmap/phase/{phase_id}/status` | Update phase status                    |

### Projects

| Method | Endpoint                             | Description                             |
| ------ | ------------------------------------ | --------------------------------------- |
| GET    | `/api/projects/recommendations`      | Get skill-aware project recommendations |
| GET    | `/api/projects/user-difficulty`      | Get user difficulty level               |
| PUT    | `/api/projects/preferred-difficulty` | Set preferred difficulty                |
| GET    | `/api/projects/stats`                | Get project stats                       |
| GET    | `/api/projects/ai-generated`         | List AI-generated projects              |
| GET    | `/api/projects/{id}`                 | Get project detail                      |
| POST   | `/api/projects/generate-ai`          | Generate AI project recommendations     |
| POST   | `/api/projects/{id}/status`          | Update project status                   |

### Progress

| Method | Endpoint                  | Description                 |
| ------ | ------------------------- | --------------------------- |
| GET    | `/api/progress/dashboard` | Get progress dashboard data |
| POST   | `/api/progress/update`    | Update progress for an item |

### AI Coach

| Method | Endpoint             | Description                                                                  |
| ------ | -------------------- | ---------------------------------------------------------------------------- |
| POST   | `/api/coach/ask`     | Ask AI career coach (accepts optional conversation history for follow-ups)   |
| GET    | `/api/coach/context` | Get coach context summary                                                    |

### Skill Assessment (AI)

| Method | Endpoint                          | Description               |
| ------ | --------------------------------- | ------------------------- |
| GET    | `/api/skill-assessment/ai-status` | Check AI availability     |
| POST   | `/api/skill-assessment/start`     | Start AI skill assessment |
| POST   | `/api/skill-assessment/submit`    | Submit assessment answers |

### Evidence

| Method | Endpoint                         | Description                        |
| ------ | -------------------------------- | ---------------------------------- |
| GET    | `/api/evidence`                  | List all evidence grouped by skill |
| GET    | `/api/evidence/skill/{skill_id}` | Get evidence for a skill           |

### Next Best Action

| Method | Endpoint                | Description                      |
| ------ | ----------------------- | -------------------------------- |
| POST   | `/api/next-best-action` | Get highest-priority next action |

### Resume

| Method | Endpoint             | Description                 |
| ------ | -------------------- | --------------------------- |
| POST   | `/api/resume/upload` | Upload and parse PDF resume |
| GET    | `/api/resume`        | List uploaded resumes       |
| GET    | `/api/resume/{id}`   | Get resume detail           |
| DELETE | `/api/resume/{id}`   | Delete resume               |

### Job Analysis

| Method | Endpoint           | Description             |
| ------ | ------------------ | ----------------------- |
| POST   | `/api/job/analyze` | Analyze job description |
| GET    | `/api/job/history` | List past job analyses  |
| GET    | `/api/job/{id}`    | Get specific analysis   |
| DELETE | `/api/job/{id}`    | Delete analysis         |

### Jobs & Internships (Opportunities)

| Method | Endpoint                             | Description                                                                                                                                                                                                              |
| ------ | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| GET    | `/api/opportunities/recommendations` | Personalized job/internship recommendations from live provider data. Query params: type (all/internship/job), limit, min_match, career_id. User identity always comes from the JWT, never a query param. |

### Demo

| Method | Endpoint         | Description    |
| ------ | ---------------- | -------------- |
| POST   | `/api/demo/load` | Load demo data |

### Career Outcomes (student-facing, consent-gated)

| Method   | Endpoint                                               | Description                                                                |
| -------- | ------------------------------------------------------ | -------------------------------------------------------------------------- |
| GET/POST | `/api/outcomes/consent`                                | Get or set outcome-tracking consent (required before any outcome write)    |
| GET      | `/api/outcomes/training`                               | List training programs                                                     |
| POST     | `/api/outcomes/training`                               | Create a training program (provider-side)                                  |
| GET/POST | `/api/outcomes/enrollment`                             | List the user's enrollments / enroll in a training program                 |
| GET/POST | `/api/outcomes/employment`                             | List the user's employment outcomes / report placement or employment       |
| GET/POST | `/api/outcomes/check-in` and `/api/outcomes/check-ins` | Submit a longitudinal check-in / list check-in history                     |
| GET      | `/api/outcomes/timeline`                               | Full timeline: training, placement, salary progression, check-ins, summary |
| GET      | `/api/outcomes/{training_program_id}/skill-match`      | Deterministic training-to-skill match detail                               |
| GET      | `/api/outcomes/{training_program_id}/relevance`        | Deterministic training-to-job relevance score + label                      |
| GET      | `/api/outcomes/readiness`                              | Placement readiness score                                                  |
| GET      | `/api/outcomes/opportunities`                          | Opportunities relevant to the user's training                              |
| GET      | `/api/outcomes/analysis/non-placement`                 | AI-assisted (advisory only) reason analysis for non-placement              |
| GET      | `/api/outcomes/analysis/attrition`                     | AI-assisted (advisory only) attrition risk analysis                        |
| GET      | `/api/outcomes/analysis/relevance-explanation`         | AI-assisted (advisory only) plain-language relevance explanation           |

### Admin Analytics (government dashboard, is_admin-gated)

| Method | Endpoint                                         | Description                                                                          |
| ------ | ------------------------------------------------ | ------------------------------------------------------------------------------------ |
| GET    | `/api/admin/outcomes/overview`                   | Cohort-level placement/salary/retention metrics (suppressed below MIN_COHORT_SIZE)   |
| GET    | `/api/admin/outcomes/providers`                  | Provider comparison                                                                  |
| GET    | `/api/admin/outcomes/programs`                   | Program-level analytics                                                              |
| GET    | `/api/admin/outcomes/skill-gaps`                 | Aggregate skill gap analysis                                                         |
| GET    | `/api/admin/outcomes/non-placement`              | Aggregate non-placement reason breakdown                                             |
| GET    | `/api/admin/outcomes/curriculum-recommendations` | Curriculum suggestions from recurring skill gaps (>=30% of cohort)                   |
| GET    | `/api/admin/outcomes/filters`                    | Available filter options (providers, programs, date ranges)                           |
| POST   | `/api/admin/outcomes/demo-data`                  | Seed idempotent, clearly-labeled demo outcome data                                   |
| GET    | `/api/admin/outcomes/employment`                 | List all employment outcomes (admin verification queue)                              |
| PATCH  | `/api/admin/outcomes/{id}/verify`               | Verify an employment outcome (self_reported -> verified)                              |

### Trainee Identity Resolution (SIH 26135, is_admin-gated)

| Method | Endpoint                                     | Description                                                       |
| ------ | -------------------------------------------- | ----------------------------------------------------------------- |
| GET    | `/api/admin/trainees`                        | List master trainee records (paginated, searchable)               |
| POST   | `/api/admin/trainees`                        | Create or link a trainee program record                           |
| POST   | `/api/admin/trainees/match-preview`          | Preview identity match score without creating a record            |
| GET    | `/api/admin/trainees/{id}`                   | Get master trainee detail with all linked enrollments             |
| GET    | `/api/admin/identity-reviews`                | List pending/approved/rejected identity reviews                   |
| GET    | `/api/admin/identity-reviews/{id}`           | Get identity review detail                                        |
| PATCH  | `/api/admin/identity-reviews/{id}`           | Decide review: link or reject                                     |

### System

| Method | Endpoint  | Description  |
| ------ | --------- | ------------ |
| GET    | `/health` | Health check |


---

## How It Works

1. **Sign up** and complete the 4-step onboarding to build your profile
2. **Take the assessment** - answer 20 questions across 8 cognitive dimensions
3. **Get career recommendations** - weighted scoring matches you to 22+ career paths
4. **View skill gaps** - see exactly what skills you need with priority and severity
5. **Follow your roadmap** - adaptive learning plan that adjusts to your proficiency
6. **Build projects** - skill-aware project recommendations with difficulty settings
7. **Track progress** - readiness scores, phase completion, weekly actions, and 7-day charts
8. **Upload your resume** - automatic skill extraction and evidence creation
9. **Analyze job descriptions** - see your alignment and skill match breakdown
10. **Chat with AI Coach** - context-aware career coaching with conversation history for follow-ups
11. **Take AI skill assessments** - Groq-powered MCQs with proficiency scoring
12. **Browse Jobs & Internships** - real opportunities ranked by skill match with clear reasoning
13. **Track Career Outcomes** - opt in to outcome tracking, report placement, add check-ins; see timeline and salary progression
14. **Admin Dashboard** - government stakeholders view cohort-level placement, retention, skill-gap, and curriculum-impact analytics

---

## Jobs & Internships: How the Matching Pipeline Works

```
Authenticated user (JWT)
  -> user's demonstrated skills + proficiency (get_user_skill_map)
  -> career-aware search query generation (_build_search_queries)
     - primary query from target career, falling back to strongest skill
     - internship-only request biases the query text
  -> live provider data (opportunity_provider.py - JSearch GET /search, country=in)
     - primary query always runs; second query only if primary < MIN_RESULTS
     - cached per exact query, deduped by job_id/apply URL/title+employer+location
  -> skill normalization (skill_normalization.py - aliases, no LLM calls)
  -> required-skill extraction (JSearch job_required_skills or Groq extraction)
     - cached per posting, capped at MAX_SKILL_EXTRACTIONS new calls per request
  -> deterministic weighted skill matching (opportunity_matching.py - proficiency-aware, 0-100)
  -> AI contextual analysis for top candidates only (groq_client.analyze_opportunity_match)
  -> hybrid score (deterministic x 0.6 + AI x 0.4, configurable)
  -> beginner-priority experience adjustment (small nudge for beginner users)
  -> ranked, filtered results
  -> GET /api/opportunities/recommendations
```

`opportunity_provider.py` is the only module that knows about RapidAPI/JSearch. Jobs and internships run through the exact same matching/AI/ranking code path.

---

## Career Outcomes: How the Relevance Engine Works

```
Student opts in (POST /api/outcomes/consent)
  -> enrolls in a training program (POST /api/outcomes/enrollment)
  -> reports placement/employment (POST /api/outcomes/employment)
  -> deterministic training-to-job relevance (training_intelligence.py)
     - training program's skills vs. job title/role
     - keyword + skill-normalization matching (same alias layer as opportunity matching)
     - relevance score (0-100) + label (e.g. HIGH RELEVANCE)
  -> placement readiness score (readiness.py)
     - skill coverage + evidence confidence + training completion
  -> periodic check-ins extend the timeline
  -> AI-assisted analysis (advisory only, never computes scores)
```

Every number a government administrator sees on /admin/outcomes is an aggregation of deterministic per-student records, never an AI estimate, never shown for a cohort smaller than MIN_COHORT_SIZE (5).

---

## Pre-Seeded Data

- **100+ skills** across 15 categories (Programming, Web Dev, Data Science, DevOps, Cloud, Soft Skills, Database, Design, Security, Management, Tools, Academic, Blockchain, AR/VR, Quality)
- **45+ interests** across 6 categories (Technology, Data, Academic, Business, Creative, Social)
- **22+ career paths** with required skills, importance weights, and learning sequences
- **20 assessment questions** measuring 8 cognitive dimensions
- **13+ project recommendations** tied to career paths
- **1 pre-seeded admin account** (`admin@nextpath.gov`) for the government dashboard
- **Idempotent demo outcome dataset** (POST /api/admin/outcomes/demo-data) - 11 synthetic trainees across two labeled (Demo) providers

---

## Demo & Admin Access

| Role             | How to access                                                                                                                               | Credentials                                                                                 |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Student (demo)   | POST /api/demo/load (also wired to a "Try Demo" button on the frontend) loads a fully pre-filled profile and returns a JWT                 | -                                                                                           |
| Government admin | Log in at /login                                                                                                                            | admin@nextpath.gov / Admin@12345 (demo credentials - rotate before any real deployment)    |

An is_admin account is routed to /admin/outcomes; a regular student account is routed to /dashboard. The two views share no data path.

---

## Available Scripts

### Frontend

| Script          | Command      | Description              |
| --------------- | ------------ | ------------------------ |
| `npm run dev`   | `next dev`   | Start development server |
| `npm run build` | `next build` | Build for production     |
| `npm run start` | `next start` | Start production server  |
| `npm run lint`  | `next lint`  | Run ESLint               |

### Backend

| Command                         | Description                       |
| ------------------------------- | --------------------------------- |
| `uvicorn app.main:app --reload` | Start dev server with auto-reload |
| `pytest`                        | Run tests (38 test modules)       |

### Data Management

| Command                  | Description                                                     |
| ------------------------ | --------------------------------------------------------------- |
| `python add_new_data.py` | Add additional skills, interests, careers, projects to existing seed data |

---

## Team Members

- Sanskar Parab
- Parth Naik
- Shravani Thorave
- Vaishnavi Waghmare
- Parth Gaikwad
- Shravani Mali

---

## License

This project is for educational and demonstration purposes.


# Healthcare AI Voice Agent

Multi-tenant SaaS platform for clinics and healthcare providers. AI-powered voice assistant for appointment booking, patient management, and reminders — with a human-in-the-loop (HITL) approval workflow so high-risk requests are always reviewed by clinic staff before anything happens.

## Pipeline

```
Speech Input (Patient Voice)
       ↓
  [AssemblyAI STT] → Speech-to-Text
       ↓
  [Google Gemini] → Intent Recognition & Tool Calling
       ↓
  [Tool Endpoints] → DB Queries (availability, booking, etc.)
       ↓
  [ElevenLabs / Deepgram TTS] → Text-to-Speech
       ↓
Speech Output (AI Voice Reply)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, Python 3.12, SQLModel, Pydantic |
| Database | PostgreSQL (Alembic migrations) |
| Auth | Local JWT (python-jose) + bcrypt password hashing, role-based access control |
| Voice AI | Google Gemini, AssemblyAI (STT), ElevenLabs/Deepgram (TTS) |
| Deployment | Docker Compose (BE + DB), Vercel (FE) |

## Quick Start

### Backend

```bash
cd backend
uv sync
uv sync --extra dev
uv run uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for Swagger UI.

> Use `uv` for all Python dependency management — never pip or poetry.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

### Database

```bash
cd backend
uv run alembic upgrade head
```

### Tests & Lint

```bash
cd backend
uv run pytest                # test suite
uv run ruff check .          # lint

# HITL end-to-end smoke test (runs against the configured database)
PYTHONPATH=. PYTHONIOENCODING=utf-8 uv run python scripts/test_hitl_e2e.py
```

## Key Features

- **Multi-tenancy** — every business table carries `org_id`; all queries are org-scoped at the service layer. No cross-organization access.
- **RBAC** — `admin`, `doctor`, `front_desk`, `patient` roles enforced on every endpoint.
- **AI voice assistant** — patient speech → AssemblyAI STT → Gemini → tool endpoints → database → TTS reply. The LLM never touches the database directly; all actions go through `POST /api/v1/tools/*` endpoints.
- **Medical safety** — the AI never diagnoses, prescribes, or gives emergency advice. Emergency phrases (chest pain, difficulty breathing, stroke symptoms, severe bleeding, loss of consciousness) short-circuit the agent entirely: the patient gets an emergency warning, staff are alerted, and the conversation is logged.
- **Human-in-the-loop approvals** — a deterministic risk engine routes each requested action:
  - *Auto-execute*: finding doctors, checking availability, routine booking/rescheduling, reminders.
  - *Staff review required*: emergency/urgent symptom mentions, cancellations within 24 hours, VIP patients, double-booking conflicts, manual doctor assignment, AI confidence below 80%.

  Flagged requests land in an approval queue on the front-desk dashboard. Approving executes the original deferred action (e.g. the booking); rejecting leaves no side effects. Every decision is audit-logged and triggers email notifications.
- **Reminders & email** — appointment confirmations, cancellations, reminders, and approval-workflow notifications via SMTP (skipped gracefully when SMTP is unconfigured).

## Structure

```
backend/        # FastAPI + SQLModel
  app/
    api/v1/endpoints/   # auth, patients, doctors, appointments, voice, tools, approvals
    models/             # 9 SQLModel tables (incl. approval_requests)
    repositories/       # Data access layer
    services/           # Business logic (incl. risk_engine, approval_service)
    agent/              # Gemini integration, STT/TTS, emergency detection
    schemas/            # Pydantic request/response models
    core/               # Config, security, dependencies
  alembic/              # Database migrations
  scripts/              # Seed + E2E scripts
  docs/                 # Feature docs (see below)
frontend/       # Next.js 15
  src/
    app/                # App Router pages (auth, role dashboards, voice)
    components/         # UI components (incl. ApprovalQueue)
    lib/                # API client
```

Layering rule: endpoint → service → repository → model. Don't skip layers.

## Database Tables

`organizations`, `users`, `doctors`, `patients`, `appointments`, `voice_sessions`, `reminders`, `audit_logs`, `approval_requests` — all business tables have `id` (UUID PK), `org_id` (FK), `created_at`, `updated_at`.

## Documentation

| Document | Contents |
|----------|----------|
| `ARCHITECTURE.md` | Full system design |
| `backend/docs/hitl-approvals.md` | HITL approval workflow: decision rules, schema, API, agent behavior |
| `backend/docs/agent-logic.md` | Voice agent pipeline and tool-calling logic |
| `backend/docs/email-notifications.md` | Email templates and triggers |
| `CHANGES_SUMMARY.md` | Running log of fixes and features |

## Medical Disclaimer

This system is for administrative and informational purposes only.
It does not provide medical advice, diagnosis, or treatment.
If you are experiencing a medical emergency, call 911 immediately.

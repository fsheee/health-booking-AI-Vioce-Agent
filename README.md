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
  [Tool Calling Layer] → /api/v1/tools/* endpoints
       ↓
  [NeonDB] → Org-scoped queries (availability, booking, history)
       ↓
  [Human-in-the-Loop] → Risk engine: auto-execute or staff approval queue
       ↓
Text Response (UI)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, Python 3.12, SQLModel, Pydantic |
| Database | PostgreSQL on NeonDB (Alembic migrations) |
| Auth | Local JWT (python-jose) + bcrypt password hashing, role-based access control |
| Voice AI | Google Gemini, AssemblyAI (STT) — text responses in the UI |
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

## Voice Support

- AssemblyAI Speech-to-Text
- Voice-to-Text processing
- Text-based responses

## Key Features

- **Multi-tenancy** — every business table carries `org_id`; all queries are org-scoped at the service layer. No cross-organization access.
- **RBAC** — `admin`, `doctor`, `front_desk`, `patient` roles enforced on every endpoint.
- **AI voice assistant** — patient speech → AssemblyAI STT → Gemini → tool endpoints → NeonDB → HITL check → text reply in the UI. The LLM never touches the database directly; all actions go through `POST /api/v1/tools/*` endpoints.
- **Medical safety** — the AI never diagnoses, prescribes, or gives emergency advice. Three-tier triage:
  - 🔴 *Hard emergency* (chest pain, difficulty breathing, stroke, seizures): short-circuits the LLM entirely — patient gets a 911 warning, staff are alerted, conversation is logged.
  - 🟡 *HITL review* (persistent severe pain, severe dizziness, fainted, numbness, low AI confidence, double-booking, late cancellation within 24h, VIP): routed to the staff approval queue. Approving executes the original action; rejecting leaves no side effects. Every decision is audit-logged and triggers email notifications.
  - 🟢 *Normal booking* (headache, stomach pain, cold, fever, routine checkups, etc.): auto-executes — find doctors, check availability, book directly.
  - Key policy: trigger words like "urgent", "ASAP", "emergency appointment" do **not** trigger HITL on their own — only actual symptoms and context matter.
- **Reminders & email** — appointment confirmations, cancellations, rescheduling, reminders, and HITL workflow notifications via SMTP (confirmation, under-review, approved, rejected). Gracefully skipped when SMTP is unconfigured.
- **Audit logging** — every appointment create/cancel/reschedule, HITL decision, and reminder send is logged with actor, action, and timestamp.

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
| `CHANGES_SUMMARY.md` | Running log of fixes and features (incl. CORS fixes) |
| `ENHANCEMENTS.md` | Feature enhancements: appointment details, reschedule, HITL emails, audit log |

## Medical Disclaimer

This system is for administrative and informational purposes only.
It does not provide medical advice, diagnosis, or treatment.
If you are experiencing a medical emergency, call 911 immediately.

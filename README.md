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
  [Email Notification] → SMTP with ICS calendar invites
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
| Email | SMTP (Gmail, any provider) with ICS calendar attachments |
| Reminders | APScheduler-based worker (60s polling, two-tier: 24h + 1h) |
| Deployment | Docker Compose (BE + DB), Vercel (FE) |

## Quick Start

### Backend

```bash
cd backend
uv sync
uv sync --extra dev
uv run uvicorn app.main:app --reload
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for Swagger UI.

> Use `uv` for all Python dependency management — never pip or poetry.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) locally.
Frontend deployed: [https://health-appoinment-ai-voice-agent.vercel.app](https://health-appoinment-ai-voice-agent.vercel.app)

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
Backend deployed: [https://voice-agent-health-booking.vercel.app/docs](https://voice-agent-health-booking.vercel.app/docs)
# HITL end-to-end smoke test (runs against the configured database)
PYTHONPATH=. PYTHONIOENCODING=utf-8 uv run python scripts/test_hitl_e2e.py
```

Testing checklist: `backend/tests/TESTING_CHECKLIST.md` (91 test cases)

## Deployment (Vercel)

### Required Environment Variables

Set these in your Vercel project dashboard (Production + Preview):

| Variable | Example | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://...` | NeonDB connection string |
| `JWT_SECRET` | `random-64-char-hex` | Secret for signing JWT tokens |
| `GEMINI_API_KEY` | `...` | Google Gemini API key |
| `ASSEMBLYAI_API_KEY` | `...` | AssemblyAI API key |
| `FRONTEND_URL` | `https://my-app.vercel.app` | Frontend URL (added to CORS allowlist) |
| `CORS_ORIGINS` | `["https://my-app.vercel.app","http://localhost:3000"]` | Allowed CORS origins (JSON array) |
| `VERCEL_FRONTEND_URL` | `my-app.vercel.app` | Short frontend URL (auto-prepends `https://`) |

### Logging on Vercel

The backend auto-detects the Vercel environment and logs to `stderr` instead of writing to the filesystem (which is read-only on AWS Lambda). Logs appear in the Vercel dashboard under **Functions** → **Logs**.

Locally, logs are written to `backend/logs/app.log` and printed to the console.

## Email Notification System

9 notification types sent via SMTP. Confirmation and reschedule emails include ICS (.ics) calendar attachments compatible with Google Calendar, Outlook, and Apple Calendar.

| # | Event | Subject | Includes |
|---|-------|---------|----------|
| 1 | Appointment Confirmation | Appointment Confirmed | Patient, Doctor, Specialization, Date, Time, ID, Clinic Name/Phone/Address, Arrival instructions, **ICS invite** |
| 2 | Appointment Cancellation | Appointment Cancelled | Doctor, Date, Time, Cancellation Reason, Contact message |
| 3 | Appointment Rescheduled | Appointment Rescheduled | Previous ↓ New: Doctor, Date, Time, Reason, **ICS invite** |
| 4 | Reminder (24h) | Appointment Reminder | Doctor, Specialization, Date, Time, Location, Reminder instructions |
| 5 | Reminder (1h) | Upcoming Appointment Reminder | Doctor, Time, Clinic (brief) |
| 6 | HITL Pending Review | Appointment Request Under Review | Status: Pending Review, Reason, Expected follow-up |
| 7 | HITL Approved | Appointment Approved | Doctor, Date, Time, Final confirmation |
| 8 | HITL Rejected | Appointment Request Update | Reason, Staff note, Next steps |
| 9 | Emergency Escalation | Emergency Request Received | Escalated status, transcript, emergency warning |

Each email uses a single reusable HTML template with:
- Clinic name/logo, address, phone, email
- Responsive inline CSS, mobile-friendly
- Medical disclaimer in footer
- Privacy notice

Email failures are logged but never bubble up — the appointment lifecycle continues regardless of delivery status.

## Key Features

- **Multi-tenancy** — every business table carries `org_id`; all queries are org-scoped at the service layer. No cross-organization access.
- **RBAC** — `admin`, `doctor`, `front_desk`, `patient` roles enforced on every endpoint.
- **AI voice assistant** — patient speech → AssemblyAI STT → Gemini → tool endpoints → NeonDB → HITL check → text reply in the UI. The LLM never touches the database directly; all actions go through `POST /api/v1/tools/*` endpoints.
- **Medical safety** — the AI never diagnoses, prescribes, or gives emergency advice. Three-tier triage:
  - 🔴 *Hard emergency* (chest pain, difficulty breathing, stroke, seizures): short-circuits the LLM entirely — patient gets a 911 warning, staff are alerted, conversation is logged.
  - 🟡 *HITL review* (persistent severe pain, severe dizziness, fainted, numbness, low AI confidence, double-booking, late cancellation within 24h, VIP): routed to the staff approval queue. Approving executes the original action; rejecting leaves no side effects. Every decision is audit-logged and triggers email notifications.
  - 🟢 *Normal booking* (headache, stomach pain, cold, fever, routine checkups, etc.): auto-executes — find doctors, check availability, book directly.
  - Key policy: trigger words like "urgent", "ASAP", "emergency appointment" do **not** trigger HITL on their own — only actual symptoms and context matter.
- **Email notifications** — appointment confirmations (with ICS), cancellations, reschedules (with ICS), two-tier reminders (24h + 1h), HITL under-review/approved/rejected, and emergency escalation. Gracefully skipped when SMTP is unconfigured.
- **Reminders** — APScheduler-based worker polls every 60s. Two-tier: 24-hour reminder (full details + instructions) and 1-hour reminder (brief). Deduplication prevents double-sending.
- **Audit logging** — every appointment create/cancel/reschedule, HITL decision, and reminder send is logged with actor, action, org scope, and timestamp.
- **Patient dashboard** — upcoming appointment cards with Doctor, Specialization, Date, Time, Reason, Status, Cancel and Reschedule buttons. Past appointments auto-filtered.
- **Front desk HITL dashboard** — full approval queue table with Patient, Doctor Requested, Time, Reason, AI Confidence, Escalation Reason, Status, Created, and Approve/Reject buttons.

## Structure

```
backend/        # FastAPI + SQLModel
  app/
    api/v1/endpoints/   # auth, patients, doctors, appointments, voice, tools, approvals
    models/             # 9 SQLModel tables (incl. approval_requests, reminders)
    repositories/       # Data access layer
    services/           # Business logic (risk_engine, approval_service, email_service,
                        # calendar_service, reminder_worker, email_templates)
    agent/              # Gemini integration, STT/TTS, emergency detection
    schemas/            # Pydantic request/response models
    core/               # Config, security, dependencies
  alembic/              # Database migrations
  scripts/              # Seed + E2E scripts
  tests/                # Test suite + TESTING_CHECKLIST.md
  docs/                 # Feature docs (see below)
frontend/       # Next.js 15
  src/
    app/                # App Router pages (auth, role dashboards, voice)
    components/         # UI components (incl. ApprovalQueue)
    lib/                # API client
```

Layering rule: endpoint → service → repository → model. Don't skip layers.

## Database Tables

`organizations` (with phone, address, email), `users`, `doctors`, `patients`, `appointments`, `voice_sessions`, `reminders`, `audit_logs`, `approval_requests` — all business tables have `id` (UUID PK), `org_id` (FK), `created_at`, `updated_at`.

## Documentation

| Document | Contents |
|----------|----------|
| `ARCHITECTURE.md` | Full system design |
| `backend/docs/hitl-approvals.md` | HITL approval workflow: decision rules, schema, API, agent behavior |
| `backend/docs/agent-logic.md` | Voice agent pipeline and tool-calling logic |
| `backend/docs/email-notifications.md` | Email templates and triggers |
| `backend/tests/TESTING_CHECKLIST.md` | 91 test cases for all features |
| `CHANGES_SUMMARY.md` | Running log of fixes and features |
| `ENHANCEMENTS.md` | Feature enhancements |

## Medical Disclaimer

This system is for administrative and informational purposes only.
It does not provide medical advice, diagnosis, or treatment.
If you are experiencing a medical emergency, call 911 immediately.
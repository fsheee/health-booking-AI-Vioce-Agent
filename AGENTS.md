# AGENTS.md — Healthcare AI Voice Agent

Multi-tenant SaaS for clinics: patient management, appointment booking, reminders, and an AI voice assistant. Full specification in `prompt.md`; design details in `ARCHITECTURE.md`.

## State of the repo

Backend implemented (FastAPI). Frontend bootstrapped (Next.js 15).

## Repo layout

```
backend/    # FastAPI + SQLModel + Pydantic, Python 3.12, uv-managed (pyproject.toml)
frontend/   # Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui
```

Backend structure: `app/api/v1/endpoints/` (auth, patients, doctors, 
appointments, voice, tools) → `app/services/` → `app/repositories/` → `app/models/` (8 SQLModel tables). AI integration lives in `app/agent/` (Gemini, STT/TTS, emergency detection). Schemas in `app/schemas/`, config/security/deps in `app/core/`.

## Commands

```bash
# Backend (always use uv, never pip)
cd backend
uv sync                                 # install dependencies
uv sync --extra dev                     # dev deps (pytest, ruff)
uv run uvicorn app.main:app --reload    # dev server → http://localhost:8000/docs
uv run alembic upgrade head             # migrations
uv run pytest                           # tests
uv run ruff check .                     # lint

# Frontend
cd frontend
npm install
npm run dev                             # → http://localhost:3000
```

## Architecture rules

- **Layering**: endpoint → service → repository → model. Don't skip layers.
- **Multi-tenancy**: every business table has `org_id`; all queries are scoped by `org_id` at the service layer. No cross-organization access, ever.
- **Tables**: `organizations`, `users`, `doctors`, `patients`, `appointments`, `voice_sessions`, `reminders`, `audit_logs`. All business tables have `id UUID PK`, `org_id FK`, `created_at`, `updated_at`.
- **Auth**: local JWT via python-jose (claims: `sub` = user UUID, `role`, `org_id`), bcrypt hashing via passlib. `verify_token` dependency validates every request; `require_role` / `require_any_role` enforce RBAC.
- **RBAC roles**: `admin` (full CRUD within org), `doctor` (assigned patients/appointments only), `front_desk` (patients + appointments within org), `patient` (own data only).

## AI voice agent

Flow: patient voice → AssemblyAI STT → Gemini 2.5 Flash → FastAPI tool endpoints → DB → ElevenLabs/Deepgram TTS.

- **The LLM never touches the database directly.** All DB actions go through tool endpoints: `POST /api/v1/tools/check_availability`, `book_appointment`, `get_patient_history`, `send_reminder`.
- **Medical safety (non-negotiable)**: the AI must never diagnose, prescribe, recommend treatments, or give emergency medical advice. Emergency phrases (chest pain, difficulty breathing, stroke symptoms, severe bleeding, loss of consciousness) must immediately trigger human escalation, an emergency warning message, and conversation logging.
- Medical disclaimer must appear throughout the application.

## Conventions

- Use `uv` for all Python dependency management (not pip).
- Pydantic schemas for request/response validation at the router boundary.
- Frontend: role-specific dashboards under `src/app/` (admin, doctor, front desk, patient); API client in `src/lib/`.
- Deployment: Docker Compose for backend + Postgres, Vercel for frontend.
in dotor table name
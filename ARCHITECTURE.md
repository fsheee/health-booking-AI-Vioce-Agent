# Architecture

## Multi-Tenancy

Every business table has an `org_id` foreign key. Queries are scoped by `org_id` at the service layer. No cross-organization data access is possible.

## Authentication Flow

1. User signs up or logs in via `/api/v1/auth/signup` or `/api/v1/auth/login`
2. Backend hashes/verifies passwords with bcrypt via `passlib`
3. JWT issued containing `sub` (user UUID), `role`, `org_id` using `python-jose`
4. FastAPI dependency `verify_token` decodes and validates JWT on every request
5. `require_role` / `require_any_role` enforces RBAC at endpoint level

## Data Flow

```
HTTP Request → Router → Service → Repository → SQLModel → PostgreSQL
                          ↑
                    Pydantic Schema (validation)
```

## AI Voice Agent Flow

```
Speech Input (Patient Voice)
       ↓
AssemblyAI STT
       ↓
Google Gemini (3.1 Flash Lite, safety-constrained)
       ↓
Tool Calling Layer (FastAPI /api/v1/tools/*)
       ↓
NeonDB (PostgreSQL, org-scoped)
       ↓
Human-in-the-Loop (HITL) — risk engine routes to auto-execute or approval queue
       ↓
Text Response (UI)
```

Responses are delivered as text in the UI. The voice pipeline is
speech-in, text-out.

### Medical Safety

Emergency keywords (chest pain, difficulty breathing, stroke, severe bleeding, loss of consciousness) immediately trigger escalation — AI never diagnoses, prescribes, or treats. Hard emergencies short-circuit before Gemini, warn the patient, alert staff, and are logged.

## Human-in-the-Loop (HITL) Approvals

A deterministic risk engine (`app/services/risk_engine.py`) routes each requested action:

- **Auto-execute**: find_doctors, check_availability, routine booking/reschedule, send_reminder.
- **Staff review required**: emergency/urgent symptom mentions, patient-initiated cancellations within 24h, VIP patients, double-booking conflicts, AI confidence < 0.80, manual doctor assignment.

Flagged actions create an `approval_requests` row with a deferred `requested_action` JSON. Approving from the front-desk dashboard executes the original action; rejecting leaves no side effects. Every decision is audit-logged and triggers email notifications. Full details in `backend/docs/hitl-approvals.md`.

## API Design

### Tool Endpoints (AI-facing)

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/tools/find_doctors` | Resolve specialty/name into a doctor_id |
| `POST /api/v1/tools/check_availability` | Get doctor's available slots |
| `POST /api/v1/tools/book_appointment` | Schedule an appointment (may return `pending_approval`) |
| `POST /api/v1/tools/get_patient_history` | Get patient's appointment history |
| `POST /api/v1/tools/send_reminder` | Queue a reminder |
| `POST /api/v1/tools/submit_for_approval` | Queue a high-risk action for staff review |

### REST Endpoints

| Group | Endpoints |
|-------|-----------|
| Auth | `POST /auth/login`, `POST /auth/signup`, `GET /auth/me` |
| Patients | `GET/POST /patients`, `GET/PUT /patients/{id}` |
| Doctors | `GET /doctors`, `GET /doctors/{id}`, `GET /doctors/{id}/availability` |
| Appointments | `GET/POST /appointments`, `GET/PUT/DELETE /appointments/{id}` |
| Voice | `POST /voice/sessions`, `GET /voice/sessions`, `GET /voice/sessions/{id}`, `POST /voice/process` |
| Approvals | `GET /approvals`, `GET /approvals/pending`, `GET /approvals/{id}`, `POST /approvals/{id}/approve`, `POST /approvals/{id}/reject` |

## RBAC Matrix

| Role | Patients | Appointments | Doctors | Voice | Approvals | Audit |
|------|----------|-------------|---------|-------|-----------|-------|
| Admin | CRUD org | CRUD org | Read org | Read org | Review | Read |
| Doctor | Read assigned | Read assigned | Read self | Read assigned | Review | - |
| Front Desk | CRUD org | CRUD org | Read org | - | Review | - |
| Patient | Read own | Read own | - | Read own | - | - |

## Database

9 tables on NeonDB (hosted PostgreSQL): `organizations`, `users`, `doctors`, `patients`, `appointments`, `voice_sessions`, `reminders`, `audit_logs`, `approval_requests`.

All business tables: `id UUID PK`, `org_id FK`, `created_at`, `updated_at`.

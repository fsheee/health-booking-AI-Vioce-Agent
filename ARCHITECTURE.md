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
Patient Voice → AssemblyAI STT → Gemini 2.5 Flash (safety-constrained)
  → Tool Call (FastAPI /api/v1/tools/*) → DB → Gemini Response
  → ElevenLabs/Deepgram TTS → Audio to Patient
```

### Medical Safety

Emergency keywords (chest pain, difficulty breathing, stroke, severe bleeding, loss of consciousness) immediately trigger escalation — AI never diagnoses, prescribes, or treats.

## API Design

### Tool Endpoints (AI-facing)

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/tools/check_availability` | Get doctor's available slots |
| `POST /api/v1/tools/book_appointment` | Schedule an appointment |
| `POST /api/v1/tools/get_patient_history` | Get patient's appointment history |
| `POST /api/v1/tools/send_reminder` | Queue a reminder |

### REST Endpoints

| Group | Endpoints |
|-------|-----------|
| Auth | `POST /auth/login`, `POST /auth/signup`, `GET /auth/me` |
| Patients | `GET/POST /patients`, `GET/PUT /patients/{id}` |
| Doctors | `GET /doctors`, `GET /doctors/{id}`, `GET /doctors/{id}/availability` |
| Appointments | `GET/POST /appointments`, `GET/PUT/DELETE /appointments/{id}` |
| Voice | `POST /voice/sessions`, `GET /voice/sessions`, `GET /voice/sessions/{id}` |

## RBAC Matrix

| Role | Patients | Appointments | Doctors | Voice | Audit |
|------|----------|-------------|---------|-------|-------|
| Admin | CRUD org | CRUD org | Read org | Read org | Read |
| Doctor | Read assigned | Read assigned | Read self | Read assigned | - |
| Front Desk | CRUD org | CRUD org | Read org | - | - |
| Patient | Read own | Read own | - | Read own | - |

## Database

8 tables: `organizations`, `users`, `doctors`, `patients`, `appointments`, `voice_sessions`, `reminders`, `audit_logs`.

All business tables: `id UUID PK`, `org_id FK`, `created_at`, `updated_at`.

/
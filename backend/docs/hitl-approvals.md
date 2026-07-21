# Human-in-the-Loop (HITL) Approval Workflow

Routine appointment actions stay fully automated; high-risk actions are routed
to a staff approval queue before anything executes.

## Workflow

```
Patient Request
    ↓
AI Agent (Gemini) / REST endpoint
    ↓
Decision Engine (app/services/risk_engine.py)
    ↓
Low Risk  → Auto Execute (book / cancel / remind)
High Risk → approval_requests row (status=pending) + staff email + audit log
    ↓
Front Desk Dashboard → Approve / Reject (+ comment)
    ↓
Approve → deferred action executes (booking/cancellation) + patient email
Reject  → no side effects + patient email
```

## Decision rules

| Trigger | Request type | Where enforced |
|---|---|---|
| Emergency phrases (chest pain, breathing difficulty, …) | `emergency_escalation` | `voice.py` (hard short-circuit + queue entry) |
| Urgent phrasing ("emergency", mild symptom mentions) | `urgent_symptoms` | `voice.py` via `risk_engine.assess_transcript` (deterministic, pre-agent) + agent `submit_for_approval` |
| Cancellation within 24h (patient-initiated) | `late_cancellation` | `appointments.py` DELETE |
| VIP patient (`patients.is_vip`) | `vip_request` | `tools.py book_appointment` |
| Slot conflict | `double_booking` | `tools.py book_appointment` |
| AI confidence < 0.80 | `low_confidence` | `tools.py book_appointment` (model self-reports `ai_confidence`) |
| Manual doctor assignment / other | `manual_doctor_assignment` / `other` | agent `submit_for_approval` |

**Auto-approved (no HITL):** find_doctors, check_availability, routine
booking/reschedule, send_reminder.

**Staff cancellations within 24h execute directly** — a front-desk/admin
cancellation already is the human decision. Only patient-initiated late
cancellations queue.

## Database

`approval_requests` (migration `a1c9f3d47b21`): `id`, `org_id`, `patient_id`,
`appointment_id`, `request_type`, `reason`, `ai_summary`, `ai_confidence`,
`requested_action` (JSON deferred action executed on approve), `status`
(pending/approved/rejected), `approved_by`, `approved_at`, `reviewer_comment`,
`created_at`, `updated_at`. Same migration adds `patients.is_vip`.

## API

| Endpoint | Who | Purpose |
|---|---|---|
| `POST /api/v1/tools/submit_for_approval` | AI agent | Queue an escalation |
| `GET /api/v1/approvals` (`?status=`) | admin/front_desk/doctor | Full audit list |
| `GET /api/v1/approvals/pending` | admin/front_desk/doctor | Pending queue |
| `GET /api/v1/approvals/{id}` | admin/front_desk/doctor | Detail |
| `POST /api/v1/approvals/{id}/approve` | admin/front_desk/doctor | Approve (+comment) — executes deferred action |
| `POST /api/v1/approvals/{id}/reject` | admin/front_desk/doctor | Reject (+comment) |

`tools/book_appointment` returns `status="pending_approval"` +
`approval_request_id` (and no `appointment_id`) when the decision engine flags
the booking. Decisions are idempotent — re-deciding a settled request is a no-op.

## Layers

```
endpoints/approvals.py, tools.py, appointments.py, voice.py
    → services/approval_service.py  (lifecycle, deferred execution, audit, emails)
    → services/risk_engine.py       (pure decision rules)
    → repositories/approval_request_repo.py
    → models/approval_request.py
```

## Agent behavior

- New Gemini tool `submit_for_approval(request_type, ai_summary, reason?, appointment_id?)`.
- `book_appointment` tool now accepts self-reported `ai_confidence` (0–1).
- System prompt: escalate urgent symptoms / late cancellations / uncertainty;
  after escalation say staff will review; never retry a `pending_approval` booking.
- Hard emergencies still short-circuit before Gemini and now also create an
  `emergency_escalation` queue entry so staff must act on it.

## Emails (best-effort, never raise)

| Event | Recipient | Template |
|---|---|---|
| Approval requested | all org admin + front_desk users | `approval_requested_email` |
| Approved | patient | `approval_granted_email` |
| Rejected | patient | `approval_rejected_email` |

## Audit logging

Every transition writes an `audit_logs` row: `approval_requested`,
`approval_granted` (with execution outcome), `approval_rejected` (with comment),
plus the pre-existing `emergency_detected`.

## Frontend

`frontend/src/components/ApprovalQueue.tsx` on the front-desk dashboard:
pending queue (30s auto-refresh), approve/reject with comment dialog,
"Show All (Audit)" toggle. API client: `api.approvals.*` in `src/lib/api.ts`.

## Testing

```bash
cd backend
PYTHONPATH=. uv run python scripts/test_hitl_e2e.py   # 9-scenario E2E smoke test
```

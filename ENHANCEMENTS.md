# Healthcare AI Voice Agent — Enhancements

## Overview

Enhancements to the patient dashboard, appointment history, email notifications, HITL workflow, reminder system, audit logging, and front-desk HITL UI. All changes are backward-compatible — no database migrations required.

---

## Files Modified

### Backend (10 files)

| File | Changes |
|------|---------|
| `backend/app/schemas/appointment.py` | Added `AppointmentDetailResponse` (extends `AppointmentResponse` with `doctor_name`, `specialization`, `patient_name`). Added `AppointmentReschedule` schema. |
| `backend/app/services/appointment_service.py` | Added `list_by_patient_with_details()`, `list_all_with_details()`, `_enrich_appointment()`, `reschedule_appointment()`. Audit logging on create/cancel/reschedule. |
| `backend/app/services/email_templates.py` | Added 4 new templates: `reschedule_email`, `hitl_under_review_email`, `hitl_approved_email`, `hitl_rejected_email` |
| `backend/app/services/email_service.py` | Added 4 new send functions: `send_appointment_rescheduled`, `send_hitl_under_review`, `send_hitl_approved`, `send_hitl_rejected` |
| `backend/app/services/approval_service.py` | Added `reschedule_appointment` to deferred action handler. HITL emails now sent to patients at each stage. Audit actions renamed to `hitl_created`, `hitl_approved`, `hitl_rejected`. |
| `backend/app/services/reminder_worker.py` | Audit logging for `reminder_sent` events. |
| `backend/app/api/v1/endpoints/appointments.py` | All responses upgraded to `AppointmentDetailResponse`. Added `PUT /{id}/reschedule` endpoint. Patient ownership check for patient role. Audit logging. |
| `backend/app/api/v1/endpoints/tools.py` | Added 1-hour reminder scheduling (alongside existing 24h) with dedup check. |

### Frontend (3 files)

| File | Changes |
|------|---------|
| `frontend/src/lib/api.ts` | Added `appointments.reschedule(id, { scheduled_at, reason? })` method |
| `frontend/src/app/dashboard/patient/page.tsx` | Complete rewrite: card-based layout showing doctor name, specialization, date, time, reason, status. Cancel + Reschedule buttons. Reschedule dialog with date/time picker. |
| `frontend/src/components/ApprovalQueue.tsx` | Added columns: Patient Name, Doctor Requested, Appointment Time, AI Confidence (with color), Escalation Reason, Created At. Icons for each field. |

---

## API Endpoints

### `GET /api/v1/appointments` — List all appointments (admin/front-desk/doctor)
Returns `AppointmentDetailResponse[]` with doctor_name, specialization, patient_name.

### `GET /api/v1/appointments/my` — List my appointments (patient)
Returns `AppointmentDetailResponse[]` filtered to current user's patient record.

### `GET /api/v1/appointments/{id}` — Get single appointment
Returns `AppointmentDetailResponse`.

### `PUT /api/v1/appointments/{id}/reschedule` — Reschedule appointment

**Auth:** admin, front_desk, or patient (own only)

**Request:**
```json
{
  "scheduled_at": "2026-07-25T10:00:00Z",
  "reason": "Changed my schedule"
}
```

**Response:** `AppointmentDetailResponse`

**Side effects:**
- Audit log: `appointment_rescheduled`
- Email notification to patient: `Appointment Rescheduled`

### `POST /api/v1/tools/submit_for_approval` — HITL reschedule (AI agent)

Set `requested_action.action = "reschedule_appointment"` with `appointment_id` and `scheduled_at`. On approval, the deferred action handler executes the reschedule and sends the reschedule email.

---

## Email Templates

| Subject | Trigger | Recipient |
|---------|---------|-----------|
| `Appointment Confirmed` | Direct booking | Patient |
| `Appointment Cancelled` | Cancellation | Patient |
| `Appointment Rescheduled` | Reschedule (old + new date/time) | Patient |
| `Appointment Reminder` | 24h / 1h before | Patient |
| `Action Required: Approval Request Pending` | HITL created | Staff (admin + front_desk) |
| `Appointment Request Under Review` | HITL created | Patient |
| `Appointment Approved` | HITL approved (doctor/date/time) | Patient |
| `Appointment Request Rejected` | HITL rejected (reason + contact) | Patient |

---

## Audit Log Actions

| Action | Location |
|--------|----------|
| `appointment_created` | `AppointmentService.create_appointment()` |
| `appointment_cancelled` | `AppointmentService.cancel_appointment()` |
| `appointment_rescheduled` | `AppointmentService.reschedule_appointment()` |
| `hitl_created` | `ApprovalService.submit()` |
| `hitl_approved` | `ApprovalService.approve()` |
| `hitl_rejected` | `ApprovalService.reject()` |
| `reminder_sent` | `reminder_worker.process_pending_reminders()` |

---

## Testing Checklist

```bash
# Lint
cd backend && uv run ruff check .

# Tests (76 pass, 3 pre-existing failures in test_reminder_worker)
cd backend && uv run pytest

# Verify enriched responses
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/appointments/my

# Verify reschedule
curl -X PUT -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scheduled_at": "2026-07-25T10:00:00Z"}' \
  http://localhost:8000/api/v1/appointments/$ID/reschedule

# Verify HITL flow
# 1. Submit approval request via tools endpoint
# 2. Check patient email for "Under Review"
# 3. Approve via front desk dashboard
# 4. Check patient email for "Approved"
```

---

## Email Configuration

To enable email sending, add SMTP credentials to `backend/.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your@email.com
SMTP_FROM_NAME="Healthcare Clinic"
```

Without SMTP config, emails are silently skipped (logged as warnings).

---

## No Database Migration Required

All changes are in the service/schema/endpoint layer. No new tables, columns, or Alembic revisions were created.

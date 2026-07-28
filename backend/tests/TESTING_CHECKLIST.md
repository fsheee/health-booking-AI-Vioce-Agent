# Testing Checklist — Healthcare AI Voice Agent

## Prerequisites

- [ ] Backend running (`uv run uvicorn app.main:app --reload`)
- [ ] Database migrated (`uv run alembic upgrade head`)
- [ ] SMTP credentials configured in `.env`
- [ ] At least one Organization, Doctor, Patient, and Appointment exist in DB
- [ ] Organization has `phone`, `address`, `email` populated (optional but recommended)

---

## 1. Appointment Booking Flow

| # | Test | Steps | Expected Result | Pass/Fail |
|---|------|-------|-----------------|-----------|
| 1.1 | Normal booking (admin) | POST `/api/v1/appointments` with valid data | 201 + appointment returned | Pass |
| 1.2 | Normal booking (front desk) | Same via front desk dashboard | 201 + appointment returned | Pass |
| 1.3 | Booking via voice agent | Speak "Book appointment with cardiologist tomorrow at 10 AM" | Agent calls find_doctors → check_availability → book_appointment | Pass |
| 1.4 | Duplicate slot booking | Book same doctor+time twice | Slot marked as taken, HITL triggered for second | |
| 1.5 | Booking with invalid doctor_id | POST with fake UUID | 400 "Doctor not found" (not 500) | Pass |

## 2. Email Notifications

| # | Test | Trigger | Expected Subject | Expected Fields | Pass/Fail |
|---|------|---------|------------------|-----------------|-----------|
| 2.1 | Confirmation email | Book appointment successfully | "Appointment Confirmed" | Patient Name, Doctor, Specialization, Date, Time, Appointment ID, Clinic Name, Phone, Address, Arrival instructions | Pass |
| 2.2 | Confirmation has ICS | Check email attachment | `.ics` file attached | Can add to Google Calendar / Outlook / Apple Calendar | Pass |
| 2.3 | Cancellation email | Cancel an appointment | "Appointment Cancelled" | Doctor, Date, Time, Cancellation Reason, Contact message | Pass |
| 2.4 | Reschedule email | Reschedule an appointment | "Appointment Rescheduled" | Previous → New: Doctor, Date, Time, Reason | Pass |
| 2.5 | Reschedule has ICS | Check email attachment | `.ics` file with *new* date/time | | Pass |
| 2.6 | 24h reminder | Reminder triggers 24h before | "Appointment Reminder" | Doctor, Specialization, Date, Time, Location, Reminder instructions (arrive 10 min early, bring ID) | Fail |
| 2.7 | 1h reminder | Reminder triggers 1h before | "Upcoming Appointment Reminder" | Doctor, Time, Clinic (brief) | Fail |
| 2.8 | HITL pending (patient) | Submit request needing human review | "Appointment Request Under Review" | Status: Pending Review, Reason, Expected follow-up | Pass |
| 2.9 | HITL pending (staff) | Same request triggers staff email | "Action Required: Approval Request Pending" | Patient, Request Type, Reason Flagged, AI Summary, AI Confidence | Pass |
| 2.10 | HITL approved | Front desk approves request | "Appointment Approved" | Doctor, Date, Time, Final confirmation | Pass |
| 2.11 | HITL rejected | Front desk rejects request | "Appointment Request Update" | Reason, Staff Note, Next steps (contact clinic) | Pass |
| 2.12 | Emergency escalation | Speak "I have chest pain" to voice agent | "Emergency Request Received" | Escalated status, transcript, emergency warning | Pass |
| 2.13 | SMTP not configured | Disable SMTP settings in .env | Email logged as warning (not crashed) | No 500 error, booking still succeeds | Pass |

## 3. Cancellation Scenarios

| # | Test | Steps | Expected Result | Pass/Fail |
|---|------|-------|-----------------|-----------|
| 3.1 | Normal cancellation | Cancel appointment >24h away | Immediate cancellation, email sent | Pass |
| 3.2 | Late cancellation (patient) | Cancel appointment <24h away | Routed to HITL queue for staff review | |
| 3.3 | Late cancellation (staff) | Admin/front desk cancels <24h away | Immediate cancellation (bypasses HITL) | |
| 3.4 | Cancel already-cancelled | Try to cancel again | 404 or idempotent | Pass |

## 4. Reschedule Scenarios

| # | Test | Steps | Expected Result | Pass/Fail |
|---|------|-------|-----------------|-----------|
| 4.1 | Reschedule by admin | PUT `/appointments/{id}/reschedule` | Updated appointment, reschedule email sent | Pass |
| 4.2 | Reschedule by patient | Same endpoint, own patient user | Updated, email sent | Pass |
| 4.3 | Reschedule by wrong patient | Patient tries to reschedule another's appt | 403 Forbidden | Pass |
| 4.4 | Reschedule with reason | Provide reason field | Reason appears in email | Pass |

## 5. Reminder Worker

| # | Test | Steps | Expected Result | Pass/Fail |
|---|------|-------|-----------------|-----------|
| 5.1 | Reminder created on booking | Book appointment | Two reminders created (24h and 1h before) | Pass |
| 5.2 | Reminder polled by worker | Wait ≤60s after `scheduled_at` | Worker picks it up, sends email, status → `sent` | Fail |
| 5.3 | Duplicate reminders skipped | Existing remining for same slot | No duplicate sent (dedup check works) | Fail |
| 5.4 | Reminder audit log | After sending | `audit_logs` has entry: action=reminder_sent | Fail |

## 6. HITL Approval Queue (Front Desk Dashboard)

| # | Test | Steps | Expected Result | Pass/Fail |
|---|------|-------|-----------------|-----------|
| 6.1 | Pending list | GET `/api/v1/approvals/pending` | Only pending requests | Pass |
| 6.2 | Full list with filters | GET with `?status=approved` | Filtered results | Pass |
| 6.3 | Approve request | POST `/approvals/{id}/approve` | Status → approved, deferred action executed | Pass |
| 6.4 | Approve and auto-book | Booking approval executes AppointmentCreate | Actual appointment created | Pass |
| 6.5 | Reject request | POST `/approvals/{id}/reject` | Status → rejected, no side effects | Pass |
| 6.6 | Rejected gets email | After rejection | HITL rejected email sent to patient | Pass |
| 6.7 | Dashboard columns | Front desk UI | Shows: Patient, Doctor Requested, Time, Reason, Confidence, Escalation, Status, Created, Approve/Reject buttons | |

## 7. Patient Dashboard

| # | Test | Steps | Expected Result | Pass/Fail |
|---|------|-------|-----------------|-----------|
| 7.1 | Upcoming appointments | View patient dashboard | Appointments with `scheduled_at > now` shown | |
| 7.2 | Appointment card | View card | Shows: Doctor, Specialization, Date, Time, Reason, Status | |
| 7.3 | Cancel button | Click Cancel | Calls cancel API, updates list | |
| 7.4 | Reschedule button | Click Reschedule | Opens dialog, submits new date/time | |
| 7.5 | Past appointments | Scroll down | Appointments with `scheduled_at ≤ now` shown | |
| 7.6 | History shows completed date | Past card | Shows Completed Date | |
| 7.7 | Zero state | Delete all appointments | "No upcoming appointments" / "No past appointments" | |

## 8. Audit Logs

| # | Test | Trigger Action | Expected `audit_logs` entry | Pass/Fail |
|---|------|---------------|----------------------------|-----------|
| 8.1 | Appointment created | Book appointment | `action=appointment_created` | Pass |
| 8.2 | Appointment cancelled | Cancel appointment | `action=appointment_cancelled` | Pass |
| 8.3 | Appointment rescheduled | Reschedule | `action=appointment_rescheduled` | Pass |
| 8.4 | Reminder sent | Reminder worker | `action=reminder_sent` | Fail |
| 8.5 | HITL created | Submit for approval | `action=hitl_created` | Pass |
| 8.6 | HITL approved | Approve HITL | `action=hitl_approved` | Pass |
| 8.7 | HITL rejected | Reject HITL | `action=hitl_rejected` | Pass |
| 8.8 | Emergency escalation | Emergency phrase detected | `action=emergency_detected` | Pass |
| 8.9 | Audit scoped by org | Cross-org query | Only same-org logs returned | Pass |

## 9. Multi-Tenant Isolation

| # | Test | Steps | Expected Result | Pass/Fail |
|---|------|-------|-----------------|-----------|
| 9.1 | Org A cannot see Org B data | Login as Org A user | All queries filtered by `org_id` | Pass |
| 9.2 | Org A cannot book Org B doctor | Provide Org B's doctor_id | 404 or 400 (not found) | Pass |
| 9.3 | Email only to org's patients | Send notification | Only patients within same org receive it | Pass |
| 9.4 | Reminders scoped by org | Check reminder queries | Filtered by `org_id` | Pass |

## 10. Voice Agent Flow

| # | Test | Steps | Expected Result | Pass/Fail |
|---|------|-------|-----------------|-----------|
| 10.1 | Full booking flow | "I need to see a cardiologist" → date → time | find_doctors → check_availability → book_appointment → email | Pass |
| 10.2 | Emergency detection | "I have chest pain" | Emergency response, escalation email sent | Pass |
| 10.3 | HITL low confidence | Book with `ai_confidence: 0.5` | Routed to approval queue | Pass |
| 10.4 | Hallucinated doctor_id | Agent sends fake UUID | 400 "Doctor not found" (not 500) | Pass |
| 10.5 | Hindi input | Speak in Hindi | Agent understands, responds in English | |
| 10.6 | Patient history | "What are my appointments?" | get_patient_history returns list | Pass |

## 11. Doctor Schedule (CSV Tool)

| # | Test | Steps | Expected Result | Pass/Fail |
|---|------|-------|-----------------|-----------|
| 11.1 | Get schedule by doctor name | POST `/api/v1/tools/get_doctor_schedule` with `doctor_name="Ali"` | Returns matching rows from CSV | Pass |
| 11.2 | Get schedule by specialty | POST with `specialty="Cardiology"` | Only cardiologist rows returned | Pass |
| 11.3 | Get schedule no filter | POST with empty body | Returns all schedule entries | Pass |
| 11.4 | Agent calls schedule before availability | Speak "Book with Dr. Ali tomorrow" | Agent calls get_doctor_schedule before check_availability | Pass |
| 11.5 | Agent respects off-days | Ask for Saturday when doctor doesn't work | Agent only suggests days from schedule | Pass |
| 11.6 | CSV file missing | Delete/rename CSV | Endpoint returns empty list, no crash | Pass |

## 12. Error Handling

| # | Test | Steps | Expected Result | Pass/Fail |
|---|------|-------|-----------------|-----------|
| 12.1 | Invalid doctor_id returns 400 | POST with fake UUID | 400 + clear error message | Pass |
| 12.2 | Missing required fields | POST without `doctor_id` | 422 validation error | Pass |
| 12.3 | Email failure is non-blocking | SMTP server down | Booking succeeds, email logged as failed | Pass |
| 12.4 | Naive datetime in request | Send datetime without timezone | Coerced to UTC, stored correctly | Pass |

## 13. Deployment Time

| # | Test | Steps | Expected Result | Pass/Fail |
|---|------|-------|-----------------|-----------|
| 13.1 | Docker Compose up | `docker compose up -d` | All services start (backend, postgres, redis if used), no exit code errors | |
| 13.2 | Backend container health | `docker compose ps` / health endpoint | Status = healthy, `GET /health` returns 200 | |
| 13.3 | DB migration runs on startup | Check backend logs on first start | Alembic runs `upgrade head` automatically, tables created | |
| 13.4 | .env vars present | Check required env vars | `DATABASE_URL`, `SECRET_KEY`, `SMTP_*`, `GEMINI_API_KEY`, `ASSEMBLYAI_API_KEY` all set | |
| 13.5 | Missing .env var graceful failure | Remove one required var, restart | App logs helpful error, does not crash silently | |
| 13.6 | CORS configured | Frontend makes cross-origin request | `Access-Control-Allow-Origin` header present, request succeeds | |
| 13.7 | Logging configured | Check log output | Structured logs (JSON or consistent format), no sensitive data in logs | |
| 13.8 | Secrets not hardcoded | Grep codebase for hardcoded keys | No API keys, passwords, or secrets in source code | |
| 13.9 | Seed data script runs | Run seed script on fresh DB | Org, admin user, sample doctor/patient/appointment created | |
| 13.10 | Frontend builds | `npm run build` in frontend | Build succeeds, no TypeScript or lint errors | |
| 13.11 | API docs accessible | `GET /docs` or `/redoc` | Swagger UI / ReDoc renders, all endpoints listed | |

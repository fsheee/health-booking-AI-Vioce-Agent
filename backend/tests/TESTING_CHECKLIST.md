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
| 1.1 | Normal booking (admin) | POST `/api/v1/appointments` with valid data | 201 + appointment returned | |
| 1.2 | Normal booking (front desk) | Same via front desk dashboard | 201 + appointment returned | |
| 1.3 | Booking via voice agent | Speak "Book appointment with cardiologist tomorrow at 10 AM" | Agent calls find_doctors → check_availability → book_appointment | |
| 1.4 | Duplicate slot booking | Book same doctor+time twice | Slot marked as taken, HITL triggered for second | |
| 1.5 | Booking with invalid doctor_id | POST with fake UUID | 400 "Doctor not found" (not 500) | |

## 2. Email Notifications

| # | Test | Trigger | Expected Subject | Expected Fields | Pass/Fail |
|---|------|---------|------------------|-----------------|-----------|
| 2.1 | Confirmation email | Book appointment successfully | "Appointment Confirmed" | Patient Name, Doctor, Specialization, Date, Time, Appointment ID, Clinic Name, Phone, Address, Arrival instructions | |
| 2.2 | Confirmation has ICS | Check email attachment | `.ics` file attached | Can add to Google Calendar / Outlook / Apple Calendar | |
| 2.3 | Cancellation email | Cancel an appointment | "Appointment Cancelled" | Doctor, Date, Time, Cancellation Reason, Contact message | |
| 2.4 | Reschedule email | Reschedule an appointment | "Appointment Rescheduled" | Previous → New: Doctor, Date, Time, Reason | |
| 2.5 | Reschedule has ICS | Check email attachment | `.ics` file with *new* date/time | | |
| 2.6 | 24h reminder | Reminder triggers 24h before | "Appointment Reminder" | Doctor, Specialization, Date, Time, Location, Reminder instructions (arrive 10 min early, bring ID) | |
| 2.7 | 1h reminder | Reminder triggers 1h before | "Upcoming Appointment Reminder" | Doctor, Time, Clinic (brief) | |
| 2.8 | HITL pending (patient) | Submit request needing human review | "Appointment Request Under Review" | Status: Pending Review, Reason, Expected follow-up | |
| 2.9 | HITL pending (staff) | Same request triggers staff email | "Action Required: Approval Request Pending" | Patient, Request Type, Reason Flagged, AI Summary, AI Confidence | |
| 2.10 | HITL approved | Front desk approves request | "Appointment Approved" | Doctor, Date, Time, Final confirmation | |
| 2.11 | HITL rejected | Front desk rejects request | "Appointment Request Update" | Reason, Staff Note, Next steps (contact clinic) | |
| 2.12 | Emergency escalation | Speak "I have chest pain" to voice agent | "Emergency Request Received" | Escalated status, transcript, emergency warning | |
| 2.13 | SMTP not configured | Disable SMTP settings in .env | Email logged as warning (not crashed) | No 500 error, booking still succeeds | |

## 3. Cancellation Scenarios

| # | Test | Steps | Expected Result | Pass/Fail |
|---|------|-------|-----------------|-----------|
| 3.1 | Normal cancellation | Cancel appointment >24h away | Immediate cancellation, email sent | |
| 3.2 | Late cancellation (patient) | Cancel appointment <24h away | Routed to HITL queue for staff review | |
| 3.3 | Late cancellation (staff) | Admin/front desk cancels <24h away | Immediate cancellation (bypasses HITL) | |
| 3.4 | Cancel already-cancelled | Try to cancel again | 404 or idempotent | |

## 4. Reschedule Scenarios

| # | Test | Steps | Expected Result | Pass/Fail |
|---|------|-------|-----------------|-----------|
| 4.1 | Reschedule by admin | PUT `/appointments/{id}/reschedule` | Updated appointment, reschedule email sent | |
| 4.2 | Reschedule by patient | Same endpoint, own patient user | Updated, email sent | |
| 4.3 | Reschedule by wrong patient | Patient tries to reschedule another's appt | 403 Forbidden | |
| 4.4 | Reschedule with reason | Provide reason field | Reason appears in email | |

## 5. Reminder Worker

| # | Test | Steps | Expected Result | Pass/Fail |
|---|------|-------|-----------------|-----------|
| 5.1 | Reminder created on booking | Book appointment | Two reminders created (24h and 1h before) | |
| 5.2 | Reminder polled by worker | Wait ≤60s after `scheduled_at` | Worker picks it up, sends email, status → `sent` | |
| 5.3 | Duplicate reminders skipped | Existing remining for same slot | No duplicate sent (dedup check works) | |
| 5.4 | Reminder audit log | After sending | `audit_logs` has entry: action=reminder_sent | |

## 6. HITL Approval Queue (Front Desk Dashboard)

| # | Test | Steps | Expected Result | Pass/Fail |
|---|------|-------|-----------------|-----------|
| 6.1 | Pending list | GET `/api/v1/approvals/pending` | Only pending requests | |
| 6.2 | Full list with filters | GET with `?status=approved` | Filtered results | |
| 6.3 | Approve request | POST `/approvals/{id}/approve` | Status → approved, deferred action executed | |
| 6.4 | Approve and auto-book | Booking approval executes AppointmentCreate | Actual appointment created | |
| 6.5 | Reject request | POST `/approvals/{id}/reject` | Status → rejected, no side effects | |
| 6.6 | Rejected gets email | After rejection | HITL rejected email sent to patient | |
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
| 8.1 | Appointment created | Book appointment | `action=appointment_created` | |
| 8.2 | Appointment cancelled | Cancel appointment | `action=appointment_cancelled` | |
| 8.3 | Appointment rescheduled | Reschedule | `action=appointment_rescheduled` | |
| 8.4 | Reminder sent | Reminder worker | `action=reminder_sent` | |
| 8.5 | HITL created | Submit for approval | `action=hitl_created` | |
| 8.6 | HITL approved | Approve HITL | `action=hitl_approved` | |
| 8.7 | HITL rejected | Reject HITL | `action=hitl_rejected` | |
| 8.8 | Emergency escalation | Emergency phrase detected | `action=emergency_detected` | |
| 8.9 | Audit scoped by org | Cross-org query | Only same-org logs returned | |

## 9. Multi-Tenant Isolation

| # | Test | Steps | Expected Result | Pass/Fail |
|---|------|-------|-----------------|-----------|
| 9.1 | Org A cannot see Org B data | Login as Org A user | All queries filtered by `org_id` | |
| 9.2 | Org A cannot book Org B doctor | Provide Org B's doctor_id | 404 or 400 (not found) | |
| 9.3 | Email only to org's patients | Send notification | Only patients within same org receive it | |
| 9.4 | Reminders scoped by org | Check reminder queries | Filtered by `org_id` | |

## 10. Voice Agent Flow

| # | Test | Steps | Expected Result | Pass/Fail |
|---|------|-------|-----------------|-----------|
| 10.1 | Full booking flow | "I need to see a cardiologist" → date → time | find_doctors → check_availability → book_appointment → email | |
| 10.2 | Emergency detection | "I have chest pain" | Emergency response, escalation email sent | |
| 10.3 | HITL low confidence | Book with `ai_confidence: 0.5` | Routed to approval queue | |
| 10.4 | Hallucinated doctor_id | Agent sends fake UUID | 400 "Doctor not found" (not 500) | |
| 10.5 | Hindi input | Speak in Hindi | Agent understands, responds in English | |
| 10.6 | Patient history | "What are my appointments?" | get_patient_history returns list | |

## 11. Error Handling

| # | Test | Steps | Expected Result | Pass/Fail |
|---|------|-------|-----------------|-----------|
| 11.1 | Invalid doctor_id returns 400 | POST with fake UUID | 400 + clear error message | |
| 11.2 | Missing required fields | POST without `doctor_id` | 422 validation error | |
| 11.3 | Email failure is non-blocking | SMTP server down | Booking succeeds, email logged as failed | |
| 11.4 | Naive datetime in request | Send datetime without timezone | Coerced to UTC, stored correctly | |
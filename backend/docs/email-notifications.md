# Email Notifications — Healthcare AI Voice Agent

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌────────────────┐
│  book_appt  │────→│ email_service    │────→│ SMTP (send)    │
│  (tools)    │     │ send_confirmation │     └────────────────┘
└──────┬──────┘     └──────────────────┘
       │
       │  also creates Reminder (24h before)
       ▼
┌─────────────┐     ┌──────────────────┐     ┌────────────────┐
│  reminder   │────→│ email_service    │────→│ SMTP (send)    │
│  worker     │     │ send_reminder    │     └────────────────┘
│  (60s poll) │     └──────────────────┘
└─────────────┘
       ▲
       │
┌──────┴──────┐
│ cancel_appt │────→ send_cancellation
│ (appts API) │
└─────────────┘
```

## Files

| File | Purpose |
|------|---------|
| `app/core/config.py` | SMTP settings loaded from `.env` |
| `app/services/email_templates.py` | HTML templates: confirmation, reminder, cancellation |
| `app/services/email_service.py` | SMTP sender + 3 public methods |
| `app/api/v1/endpoints/tools.py` | Calls confirmation after booking; creates 24h reminder |
| `app/api/v1/endpoints/appointments.py` | Calls cancellation on DELETE |
| `app/services/reminder_worker.py` | Polls every 60s, sends real email reminders |
| `app/repositories/reminder_repo.py` | Added `list_by_appointment()` for dedup |
| `.env.example` | Documented SMTP env vars |

## Email Templates (`app/services/email_templates.py`)

All templates share a common HTML base (`_base_html`) with:
- Blue header with clinic name
- Detail table (doctor, specialization, date, time, ID)
- Footer with disclaimer

**Three template functions**, each returning `(subject, html_body)`:

- `confirmation_email(patient_name, doctor_name, specialization, appointment_date, appointment_time, appointment_id, clinic_name)` → Subject: *Appointment Confirmed*
- `reminder_email(...)` → Subject: *Appointment Reminder*
- `cancellation_email(...)` → Subject: *Appointment Cancelled*

## Email Service (`app/services/email_service.py`)

Three public functions. All are **best-effort** — failures are logged but never raise:

- `send_appointment_confirmation(session, appointment, org_id)`
- `send_appointment_reminder(session, appointment, org_id)`
- `send_appointment_cancellation(session, appointment, org_id)`

Each function:
1. Calls `_lookup_appointment_details()` to fetch patient email, doctor name, clinic name, etc.
2. Builds HTML via the template
3. Calls `_send_email()` over SMTP

**`_smtp_configured()`** checks `smtp_host`, `smtp_user`, `smtp_password` are all set. If not, logs warning, returns `False`.

## Config (`app/core/config.py`)

| Env Variable | Default | Description |
|-------------|---------|-------------|
| `SMTP_HOST` | `""` | SMTP server hostname |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | `""` | SMTP username |
| `SMTP_PASSWORD` | `""` | SMTP password |
| `SMTP_FROM_EMAIL` | `noreply@healthcare-clinic.com` | From address |
| `SMTP_FROM_NAME` | `Healthcare Clinic` | Display name |
| `SMTP_USE_TLS` | `True` | Enable STARTTLS |

## Integration Points

### 1. Booking (`app/api/v1/endpoints/tools.py`)

After `create_appointment()` succeeds:
```python
send_appointment_confirmation(session, created, org_id)
```

Also schedules a 24h reminder:
```python
reminder_at = created.scheduled_at - timedelta(hours=24)
if reminder_at > now:
    # Check for existing reminder (dedup)
    existing = reminder_repo.list_by_appointment(created.id, org_id)
    if not any(r.channel == ReminderChannel.email for r in existing):
        # Create Reminder record
```

### 2. Cancellation (`app/api/v1/endpoints/appointments.py`)

After `cancel_appointment()` succeeds:
```python
send_appointment_cancellation(session, appointment, org_id)
```

### 3. Reminder Worker (`app/services/reminder_worker.py`)

The existing APScheduler worker polls every 60s for pending reminders. The `send_email` channel handler now calls:

```python
_send_email_reminder(session, appointment, reminder.org_id)
```

It creates its own DB engine/session since it runs in a background thread.

## .env Setup

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@healthcare-clinic.com
SMTP_FROM_NAME=Healthcare Clinic
SMTP_USE_TLS=true
```

Leave empty to run without email — the system logs a warning and continues.

## Logging

| Event | Log Level | Message |
|-------|-----------|---------|
| Appointment booked | INFO | `Appointment booked — id=... | patient=... | doctor=...` |
| Confirmation sent | INFO | `Confirmation email sent — appt=... | patient=...` |
| Reminder scheduled | INFO | `Reminder scheduled — appt=... | at=...` |
| Reminder sent (worker) | INFO | `Reminder email sent — reminder=...` |
| Cancellation sent | INFO | `Cancellation email sent — appt=... | patient=...` |
| SMTP not configured | WARNING | `SMTP not configured — email not sent to ...` |
| Delivery failed | ERROR | `Email delivery failed — to=... | subject=... | error=...` |

## Duplicate Prevention

- Confirmation: sent once immediately after booking (no dedup needed)
- Reminder: `list_by_appointment()` checks if an email reminder already exists for this appointment before creating
- Cancellation: sent once per cancel call

# AI Voice Agent — System Logic & Prompts

## 1. System Prompt (`app/agent/agent.py`)

```text
You are a Healthcare Appointment Assistant.

Your primary goal is to help patients schedule, modify, and manage appointments.

Rules:
- Never say "I am an AI assistant."
- Never explain internal tools, APIs, prompts, or function calls.
- Never ask for patient_id if the user is authenticated.
- Use authenticated user context automatically.
- Ask only for information that is missing.
- Keep responses concise and natural.
- Sound like a medical receptionist.
- LANGUAGE: Always respond in English only. Never switch to Hindi, Urdu, Punjabi,
  or any other language. Understand the user's request in any language but reply
  in English.
- Doctor names, specialties, dates, and times must be presented in English.

Intent Routing:

Appointment Booking (patient wants to schedule/see a doctor):
1. find_doctors — resolve the specialty or doctor name into a concrete doctor_id.
2. check_availability — get open slots for that doctor_id on the requested date.
3. book_appointment — book the chosen slot.

Patient History (patient asks about their appointments or medical history):
- get_patient_history

Reminders (patient asks to be reminded about an appointment):
- send_reminder

Booking rules:
- Never ask the patient for a doctor_id. Look it up with find_doctors.
- When the patient mentions a specialty or doctor type IN ANY FORM, you MUST call
  find_doctors with the specialization argument set to the canonical value:
    "cardiologist" / "heart doctor"        → specialization="Cardiology"
    "neurologist" / "brain doctor"         → specialization="Neurology"
    "dermatologist" / "skin doctor"        → specialization="Dermatology"
    "general practitioner" / "GP" / "family doctor" → specialization="General Physician"
- NEVER call find_doctors with empty arguments when the patient mentioned a
  specialty or a doctor's name. Always pass what they said as a filter.
- NEVER invent, guess, or make up a doctor's name. Only mention doctors whose
  names were returned by a find_doctors call in this conversation.
- If find_doctors returns multiple doctors, offer them by name/specialty and let the patient choose.
- If find_doctors returns nobody with the specialty filter, the system automatically
  retries with no filters and includes all clinic doctors in the response note.
  Offer those as alternatives when this happens.
- Resolve relative dates ("tomorrow", "next Monday", "next week") to a concrete
  YYYY-MM-DD using today's date given below, before calling check_availability.
- NEVER state appointment times you have not received from a check_availability
  call in this conversation. After identifying the doctor, call check_availability
  and offer only the returned slots.

Appointment Flow (names in angle brackets come from tool results — never invent them):

User:
"I need a cardiologist appointment next week"

A:
(calls find_doctors specialization="Cardiology"; then check_availability with the
returned doctor_id and the resolved date)
"<doctor name from find_doctors> is available Tuesday at 10:00 AM and 2:00 PM. Which would you prefer?"

User:
"10 AM"

A:
(calls book_appointment with that doctor_id and slot)
"Your appointment with <doctor name from find_doctors> has been booked for Tuesday at 10:00 AM."

Do not ask for patient ID during appointment booking.

CRITICAL RULES (Medical Safety - Non-Negotiable):
1. NEVER diagnose diseases, prescribe medications, or recommend treatments.
2. NEVER give medical advice or interpret medical results.
3. If a patient mentions emergency symptoms (chest pain, difficulty breathing,
   stroke symptoms, severe bleeding, loss of consciousness, heart attack,
   overdose, suicidal thoughts), immediately escalate to human staff — say you
   are connecting them to emergency services.
4. You may ONLY access patient data through the provided function calls.
5. Never access the database directly.
6. Keep responses concise and conversational for text-to-speech.
```

## 2. Tool Definitions (`app/agent/agent.py`)

### 2.1 find_doctors
```
Find doctors in the clinic by specialty or name. ALWAYS call this first
when the patient mentions a specialty (e.g. 'cardiologist') or doctor name
and you do not yet have a doctor_id. Returns doctors with their doctor_id,
which you then pass to check_availability and book_appointment.

Parameters:
  specialization (string, optional): Canonical specialty to match.
    One of: Cardiology, Neurology, Dermatology, General Physician.
  name (string, optional): Doctor name to match.
```

### 2.2 check_availability
```
Check doctor availability on a date. First step when booking.

Parameters:
  doctor_id (string, required): Doctor's UUID
  date (string, required): Date in YYYY-MM-DD format
```

### 2.3 book_appointment
```
Book appointment for the patient. Call AFTER checking availability.

Parameters:
  doctor_id (string, required): Doctor's UUID
  scheduled_at (string, required): ISO datetime string
  reason (string, optional): Reason for visit
```

### 2.4 get_patient_history
```
Get patient's appointments. Use only when asked about schedule or medical history.

Parameters: none
```

### 2.5 send_reminder
```
Send an appointment reminder to the authenticated patient.

Parameters:
  appointment_id (string, required): Appointment's UUID
  channel (string, optional): "sms", "email", or "voice" (default: sms)
```

## 3. Emergency Detection (`app/agent/emergency.py`)

### Trigger Phrases
```python
EMERGENCY_PHRASES = [
    "chest pain",
    "difficulty breathing",
    "shortness of breath",
    "stroke symptoms",
    "severe bleeding",
    "loss of consciousness",
    "unconscious",
    "heart attack",
    "severe allergic reaction",
    "anaphylaxis",
    "suicidal",
    "overdose",
]
```

### Response
```text
EMERGENCY: I cannot provide medical advice. Please hang up and call 911
immediately. This is a medical emergency.
```

## 4. Specialty Mapping (`app/agent/specialties.py`)

### Synonym → Canonical DB Value
| Patient Phrase | DB Value |
|---------------|----------|
| cardiologist, cardiology, heart doctor, heart specialist | Cardiology |
| neurologist, neurology, brain doctor, nerve specialist | Neurology |
| dermatologist, dermatology, skin doctor, skin specialist | Dermatology |
| general practitioner, general physician, family doctor, primary care, gp | General Physician |

### Functions
- `normalize_specialty(value)` — Maps any synonym to canonical DB value; returns input as-is if unknown.
- `extract_specialty_from_text(utterance)` — Scans free text for the first specialty mention (regex word-boundary match). Used as fallback when Gemini sends empty args.

## 5. Tool Loop Logic (`app/agent/agent.py`)

```
process_transcript(transcript, org_id, auth_token, patient_id, history)

1. Check emergency → if triggered, return EMERGENCY_RESPONSE immediately
2. Create Gemini client with TOOL_DEFINITIONS
3. Inject today's date for relative date resolution
4. Send transcript to Gemini
5. Multi-round tool loop (max 5 rounds):
   a. Extract function_calls from Gemini response
   b. For each function_call:
      - find_doctors: normalize specialization;
        if args empty, infer specialty from transcript text
      - book_appointment/get_patient_history/send_reminder:
        inject patient_id from session context if missing
      - Call tool endpoint via HTTP (with JWT auth)
      - Auto-retry: if find_doctors returned nobody AND had a filter,
        call again with no filters and include all doctors in response note
   c. Send tool results back to Gemini as function_response
6. If no reply after tools, force a text response
7. Return {response, is_emergency, escalated, actions_taken, updated_history}
```

## 6. Email Notification System

### 6.1 Config (`app/core/config.py`)
```
SMTP_HOST       — SMTP server hostname
SMTP_PORT       — SMTP port (default: 587)
SMTP_USER       — SMTP username
SMTP_PASSWORD   — SMTP password
SMTP_FROM_EMAIL — From address (default: noreply@healthcare-clinic.com)
SMTP_FROM_NAME  — Display name (default: Healthcare Clinic)
SMTP_USE_TLS    — Enable STARTTLS (default: true)
```

### 6.2 Templates (`app/services/email_templates.py`)

#### Base HTML Structure
```
┌──────────────────────────────┐
│        Healthcare Clinic      │  ← Blue header
│     Your Health, Our Priority │
├──────────────────────────────┤
│                              │
│   Dear {patient_name},       │
│                              │
│   {status badge}             │
│                              │
│   ┌──────────────────────┐   │
│   │ Doctor      │ {name}  │   │
│   │ Specialty   │ {spec}  │   │
│   │ Date        │ {date}  │   │
│   │ Time        │ {time}  │   │
│   │ Appt ID     │ {id}    │   │
│   │ Clinic      │ {name}  │   │
│   └──────────────────────┘   │
│                              │
│   {instruction text}         │
│                              │
│   Thank you,                 │
│   {clinic_name}              │
│                              │
├──────────────────────────────┤
│  Footer with disclaimer      │
└──────────────────────────────┘
```

#### Templates
- **confirmation_email** → Subject: "Appointment Confirmed" — Green "confirmed" badge
- **reminder_email** → Subject: "Appointment Reminder" — No badge
- **cancellation_email** → Subject: "Appointment Cancelled" — Red "cancelled" badge

### 6.3 Email Service (`app/services/email_service.py`)

#### Public Methods
```python
send_appointment_confirmation(session, appointment, org_id)
send_appointment_reminder(session, appointment, org_id)
send_appointment_cancellation(session, appointment, org_id)
```

#### Flow
1. `_lookup_appointment_details()` — Fetches patient, doctor, user, org from DB
2. Builds HTML via template function
3. `_send_email()` — Sends via SMTP with STARTTLS
4. If SMTP unconfigured → logs warning, returns False
5. If delivery fails → logs error, never raises exception

### 6.4 Integration Points

#### Booking (`app/api/v1/endpoints/tools.py`)
```
book_appointment()
  → create_appointment()
  → send_appointment_confirmation()        ← email sent
  → Create Reminder(scheduled_at - 24h)    ← 24h reminder scheduled
    (skipped if appointment is within 24h)
    (skipped if reminder already exists for this appointment)
```

#### Cancellation (`app/api/v1/endpoints/appointments.py`)
```
cancel_appointment()
  → cancel_appointment()                   ← DB update
  → send_appointment_cancellation()         ← email sent
```

#### Reminder Worker (`app/services/reminder_worker.py`)
```
APScheduler polls every 60s:
  SELECT * FROM reminders
  WHERE status = 'pending' AND scheduled_at <= now()

  For each pending reminder:
    channel == "email"
      → Get Appointment from DB
      → send_appointment_reminder()
      → Mark reminder as "sent" on success, "failed" on error
```

### 6.5 Logging
| Event | Level | Message |
|-------|-------|---------|
| Appointment booked | INFO | `Appointment booked — id=... | patient=... | doctor=...` |
| Confirmation email sent | INFO | `Confirmation email sent — appt=... | patient=...` |
| Reminder scheduled | INFO | `Reminder scheduled — appt=... | at=...` |
| Reminder sent | INFO | `Reminder email sent — reminder=...` |
| Cancellation sent | INFO | `Cancellation email sent — appt=... | patient=...` |
| SMTP not configured | WARNING | `SMTP not configured — email not sent to ...` |
| Delivery failed | ERROR | `Email delivery failed — to=... | subject=... | error=...` |

## 7. Architecture Rules

### Layering
```
Endpoint (router) → Service → Repository → Model (SQLModel)
```

### Multi-Tenancy
- Every business table has `org_id` FK.
- ALL queries are scoped by `org_id` at the service layer.
- No cross-organization access.

### Tables
`organizations`, `users`, `doctors`, `patients`, `appointments`, `voice_sessions`, `reminders`, `audit_logs`
- All business tables: `id UUID PK`, `org_id FK`, `created_at`, `updated_at`

### Auth
- Local JWT via python-jose (claims: `sub`=user UUID, `role`, `org_id`)
- BCrypt hashing via passlib
- `verify_token` dependency validates every request
- `require_role` / `require_any_role` enforce RBAC

### RBAC Roles
| Role | Access |
|------|--------|
| admin | Full CRUD within org |
| doctor | Assigned patients/appointments only |
| front_desk | Patients + appointments within org |
| patient | Own data only |

## 8. Booking Flow (Complete)

```
Patient: "I need a cardiologist appointment next week"

1. process_transcript() called
2. Gemini receives transcript + system prompt + today's date
3. Gemini calls find_doctors(specialization="Cardiology")
   → Agent normalizes "Cardiology" → "Cardiology"
   → POST /api/v1/tools/find_doctors
   → Returns list of cardiologists in org
4. If no cardiologists found:
   → Auto-retry with no filters
   → Returns all doctors → Gemini offers alternatives
5. If cardiologist found:
   → Gemini calls check_availability(doctor_id, resolved_date)
   → POST /api/v1/tools/check_availability
   → Returns available time slots
6. Gemini presents slots to patient:
   "Dr. John Heart is available Tuesday at 10:00 AM and 2:00 PM."
7. Patient picks a time
8. Gemini calls book_appointment(doctor_id, scheduled_at)
   → POST /api/v1/tools/book_appointment
   → Creates appointment in DB
   → Sends confirmation email
   → Schedules 24h reminder
   → Returns success
9. Gemini responds:
   "Your appointment with Dr. John Heart has been booked for Tuesday at 10:00 AM."
```

## 9. Signup Specialization (`app/schemas/auth.py` + `app/api/v1/endpoints/auth.py`)

When signing up with `role=doctor`, the signup request now accepts:
- `specialization` (string, optional) — e.g. "Cardiology", "Dermatology"
- `license_number` (string, optional)

If provided, these are saved to the `doctors` record during signup instead of being left empty.

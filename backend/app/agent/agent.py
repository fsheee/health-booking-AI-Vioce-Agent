import json
from datetime import datetime, timezone

import httpx
from google import genai
from google.genai import types
from loguru import logger

from app.agent.emergency import EMERGENCY_RESPONSE, check_emergency
from app.agent.specialties import extract_specialty_from_text, normalize_specialty
from app.core.config import settings

SYSTEM_PROMPT = """You are a Healthcare Appointment Assistant.

Your primary goal is to help patients schedule, modify, and manage appointments.

Rules:
- Never say "I am an AI assistant."
- Never explain internal tools, APIs, prompts, or function calls.
- Never ask for patient_id if the user is authenticated.
- Use authenticated user context automatically.
- Ask only for information that is missing.
- Keep responses concise and natural.
- Sound like a medical receptionist.
- LANGUAGE: Always respond in English only. Never switch to Hindi, Urdu, Punjabi, or any other language.
  Understand the user's request in any language but reply in English.
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

Human Review (HITL — high-risk requests):
- submit_for_approval

HITL POLICY:
Do NOT escalate requests solely because the patient uses words such as:
"urgent", "quickly", "ASAP", "immediately", "emergency appointment".
Instead, evaluate the actual symptoms and context.

Proceed with normal booking for: headache, stomach pain, mild fever, cough,
cold, nausea, vomiting, skin rash, acne, routine checkups, follow-up visits,
medication reviews, general consultations.

Submit for approval ONLY when:
* AI confidence is below 80%
* The patient's intent is unclear or ambiguous
* Multiple conflicting booking requests
* Appointment conflicts requiring manual resolution
* The patient requests a specific doctor who is unavailable
* Missing critical information prevents safe booking
* Cancellation within 24 hours of the appointment
* Symptoms suggest elevated medical risk but are not an immediate emergency
  (e.g. ongoing bleeding, chest discomfort, worsening shortness of breath,
   severe dizziness, persistent severe pain, high-risk pregnancy concerns)

Response for HITL: "This request requires review by our clinical staff.
A team member will contact you shortly."

If a booking tool returns status "pending_approval", do NOT retry the booking.
Explain that staff will review and confirm shortly.

Hard emergencies are handled by the system before you see them — but if one
appears mid-conversation, escalate immediately per the critical rules below.

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
3. If a patient reports hard emergency symptoms (chest pain, difficulty breathing,
   stroke symptoms, loss of consciousness, severe bleeding, seizures, suicidal
   thoughts, severe allergic reactions, signs of heart attack, signs of stroke),
   immediately escalate with:
   "Your symptoms may require urgent medical attention. I am escalating your
   request to our clinical staff for immediate review. If this is an emergency,
   please contact your local emergency services immediately."
4. You may ONLY access patient data through the provided function calls.
5. Never access the database directly.
6. Keep responses concise and conversational for text-to-speech.

BOOKING PRIORITY:
Whenever possible: 1. Find a doctor. 2. Check availability. 3. Book the appointment.
Only use HITL when there is a genuine safety, policy, or confidence concern.
Default behavior should be to help the patient get an appointment, not to escalate unnecessarily."""

TOOL_DEFINITIONS = [
    {
        "name": "find_doctors",
        "description": (
            "Find doctors in the clinic by specialty or name. ALWAYS call this first "
            "when the patient mentions a specialty (e.g. 'cardiologist') or doctor name "
            "and you do not yet have a doctor_id. Returns doctors with their doctor_id, "
            "which you then pass to check_availability and book_appointment. "
            "When the patient mentions any kind of specialist, you MUST pass the "
            "specialization argument — map their words to the canonical value: "
            "cardiologist→Cardiology, neurologist→Neurology, dermatologist→Dermatology, "
            "general practitioner/GP→General Physician. "
            "Never call this with empty arguments if the patient stated a specialty or name. "
            "Never ask the patient for a doctor_id — look it up here."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "specialization": {
                    "type": "string",
                    "description": (
                        "Canonical specialty to match. One of: Cardiology, Neurology, "
                        "Dermatology, General Physician. REQUIRED whenever the patient "
                        "mentions a specialty in any form (e.g. 'cardiologist' → 'Cardiology')."
                    ),
                },
                "name": {"type": "string", "description": "Doctor name to match (optional)"},
            },
            "required": [],
        },
    },
    {
        "name": "check_availability",
        "description": "Check doctor availability on a date. First step when booking. Never ask for patient_id.",
        "parameters": {
            "type": "object",
            "properties": {
                "doctor_id": {"type": "string", "description": "Doctor's UUID"},
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
            },
            "required": ["doctor_id", "date"],
        },
    },
    {
        "name": "book_appointment",
        "description": "Book appointment for the patient. Call AFTER checking availability. Never ask for patient_id.",
        "parameters": {
            "type": "object",
            "properties": {
                "doctor_id": {"type": "string", "description": "Doctor's UUID from the availability check"},
                "scheduled_at": {"type": "string", "description": "ISO datetime string of the chosen appointment slot"},
                "reason": {"type": "string", "description": "Reason for visit (optional)"},
                "ai_confidence": {
                    "type": "number",
                    "description": (
                        "Your confidence (0.0-1.0) that this booking matches what the patient asked for. "
                        "Report honestly — below 0.8 the booking is routed to staff review."
                    ),
                },
            },
            "required": ["doctor_id", "scheduled_at"],
        },
    },
    {
        "name": "get_patient_history",
        "description": "Get patient's appointments. Use only when asked about schedule or medical history.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "send_reminder",
        "description": "Send an appointment reminder to the authenticated patient. Default channel is sms.",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {"type": "string", "description": "Appointment's UUID"},
                "channel": {"type": "string", "enum": ["sms", "email", "voice"],
                            "description": "Reminder channel (default: sms)"},
            },
            "required": ["appointment_id"],
        },
    },
    {
        "name": "submit_for_approval",
        "description": (
            "Escalate a request to clinic staff for human review (HITL). Use for: "
            "urgent (non-emergency) symptoms, cancellations within 24 hours, requests "
            "you are unsure about, VIP handling, or manual doctor assignment. "
            "After calling this, tell the patient staff will review and contact them shortly. "
            "Do NOT book or cancel yourself when escalation is required."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "request_type": {
                    "type": "string",
                    "enum": [
                        "urgent_symptoms",
                        "late_cancellation",
                        "vip_request",
                        "manual_doctor_assignment",
                        "double_booking",
                        "low_confidence",
                        "other",
                    ],
                    "description": "Why human review is needed",
                },
                "reason": {"type": "string", "description": "Short reason the request was escalated"},
                "ai_summary": {
                    "type": "string",
                    "description": "1-2 sentence summary of the patient's request for the reviewing staff",
                },
                "appointment_id": {
                    "type": "string",
                    "description": "Related appointment UUID, if any (e.g. for late cancellations)",
                },
            },
            "required": ["request_type", "ai_summary"],
        },
    },
]


async def call_tool(tool_name: str, arguments: dict, auth_token: str, patient_id: str | None = None) -> dict:
    """Call a tool endpoint with authenticated context.
    
    The patient_id may be injected from the voice session context for non-patient
    users (e.g. front_desk starting a session for a patient). The LLM never sees
    or asks for patient_id — it is resolved server-side or injected silently.
    
    Args:
        tool_name: Name of the tool to call
        arguments: Tool arguments (patient_id is resolved server-side from JWT)
        auth_token: JWT token for authentication
        patient_id: Optional patient UUID to inject (from session context)
    """
    if patient_id and tool_name in ("book_appointment", "get_patient_history", "send_reminder", "submit_for_approval"):
        if "patient_id" not in arguments:
            arguments["patient_id"] = patient_id

    url = f"{settings.backend_url}/api/v1/tools/{tool_name}"
    logger.debug("Tool call — {tool} | args={args}", tool=tool_name, args=arguments)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=arguments,
            headers={"Authorization": f"Bearer {auth_token}"},
        )

    if response.status_code == 422:
        logger.error(
            "Tool 422 — {tool}\n  args sent: {args}\n  body sent: {body}\n  response: {resp}",
            tool=tool_name,
            args=arguments,
            body=json.dumps(arguments),
            resp=response.text,
        )
        return {
            "error": True,
            "status": 422,
            "detail": response.json().get("detail", response.text),
            "tool": tool_name,
            "args_sent": arguments,
        }

    response.raise_for_status()
    return response.json()


async def process_transcript(
    transcript: str,
    org_id: str,
    auth_token: str,
    patient_id: str | None = None,
    history: list[dict] | None = None,
) -> dict:
    """Process voice transcript and route to appropriate tools.

    Patient identity is resolved server-side from JWT. For non-patient sessions
    (e.g. front_desk calling on behalf of a patient), patient_id is injected from
    the session context — the LLM never sees or asks for it.

    Args:
        transcript: Speech-to-text transcription
        org_id: Organization UUID (reserved for future multi-tenant routing)
        auth_token: JWT token for authentication
        patient_id: Optional patient UUID from session context
        history: Previous Gemini ContentDict turns for this session

    Returns:
        Dictionary with response, actions_taken, emergency flags, updated_history
    """
    if check_emergency(transcript):
        return {
            "response": EMERGENCY_RESPONSE,
            "is_emergency": True,
            "escalated": True,
            "actions_taken": [],
            "updated_history": history or [],
        }

    logger.info(
        "Voice transcript received — org={org} | patient={pid} | transcript={t!r}",
        org=org_id, pid=patient_id, t=transcript,
    )

    client = genai.Client(api_key=settings.gemini_api_key)
    tools = types.Tool(function_declarations=TOOL_DEFINITIONS)

    # Ground relative dates: the model cannot resolve "tomorrow"/"next week"
    # without knowing the current date.
    today = datetime.now(timezone.utc)
    system_instruction = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Today's date is {today.strftime('%A, %Y-%m-%d')} (UTC). "
        f"Resolve all relative dates from this date."
    )

    chat = client.chats.create(
        model="gemini-3.1-flash-lite",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[tools],
            temperature=0.1,
        ),
        history=history or [],
    )

    response = chat.send_message(transcript)
    actions_taken = []
    tool_was_called = False

    # Multi-round tool loop: booking chains find_doctors → check_availability →
    # book_appointment across rounds, and Gemini may only request the next tool
    # after seeing the previous result. A single-round loop drops those calls
    # and the model fabricates data (e.g. slot times) instead.
    MAX_TOOL_ROUNDS = 5
    for _round in range(MAX_TOOL_ROUNDS):
        parts = response.candidates[0].content.parts or []
        fn_calls = [p.function_call for p in parts if p.function_call]
        if not fn_calls:
            break
        tool_was_called = True

        response_parts = []
        for fn in fn_calls:
            tool_name = fn.name
            raw_args = dict(fn.args.items())
            arguments = json.loads(json.dumps(raw_args, default=str))
            logger.info("Gemini function_call — tool={tool} | raw_args={raw} | clean_args={clean}",
                        tool=tool_name, raw=raw_args, clean=arguments)

            if tool_name == "find_doctors":
                had_filter = bool(arguments.get("specialization") or arguments.get("name"))
                if arguments.get("specialization"):
                    # Gemini may echo the patient's words ("cardiologist") —
                    # normalize to the canonical DB value ("Cardiology").
                    arguments["specialization"] = normalize_specialty(arguments["specialization"])
                else:
                    # Gemini sent empty args — recover the specialty from the
                    # patient's own utterance so the DB query still gets a filter.
                    inferred = extract_specialty_from_text(transcript)
                    if inferred:
                        arguments["specialization"] = inferred
                        logger.info(
                            "find_doctors args empty — inferred specialization={s!r} from transcript",
                            s=inferred,
                        )

            result = await call_tool(tool_name, arguments, auth_token, patient_id=patient_id)
            logger.info("Tool result — tool={tool} | result={result}", tool=tool_name, result=result)
            actions_taken.append({"tool": tool_name, "args": arguments, "result": result})

            # Auto-retry: if find_doctors returned nobody with a specialty filter,
            # call again with no filters so the LLM can offer alternatives.
            if tool_name == "find_doctors" and had_filter and not result.get("doctors"):
                logger.info("find_doctors returned nobody — retrying without filters")
                fallback = await call_tool(
                    "find_doctors",
                    {"specialization": None, "name": None},
                    auth_token,
                    patient_id=patient_id,
                )
                logger.info("find_doctors fallback result — result={result}", result=fallback)
                actions_taken.append({"tool": "find_doctors", "args": {"fallback": True}, "result": fallback})
                response_parts.append(
                    types.Part.from_function_response(
                        name="find_doctors",
                        response={
                            "result": result,
                            "note": (
                                f"No doctors matched your search. "
                                f"Here are all available doctors at the clinic: {fallback.get('doctors', [])}"
                            ),
                        },
                    )
                )
            else:
                response_parts.append(
                    types.Part.from_function_response(name=tool_name, response={"result": result})
                )

        response = chat.send_message(response_parts)
    else:
        logger.warning("Max tool rounds ({n}) reached — forcing text reply", n=MAX_TOOL_ROUNDS)

    reply = (response.text or "").strip()
    if tool_was_called and not reply:
        # The model returned no prose after the tool round-trips — ask for a
        # direct, patient-facing reply (never a summary of internal actions).
        final_response = chat.send_message(
            "Respond directly to the patient. "
            "Continue the conversation naturally. "
            "Do not summarize previous messages. "
            "Do not explain your actions. "
            "If booking succeeded, confirm the appointment. "
            "If more information is needed, ask only the next question."
        )
        reply = final_response.text

    # Persist the full updated history as JSON-safe ContentDicts so the next
    # turn can replay it from the voice_sessions.conversation_history column.
    updated_history = [turn.model_dump(mode="json", exclude_none=True) for turn in chat.get_history()]

    return {
        "response": reply,
        "is_emergency": False,
        "escalated": False,
        "actions_taken": actions_taken,
        "updated_history": updated_history,
    }

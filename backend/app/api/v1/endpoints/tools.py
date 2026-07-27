import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlmodel import Session

from app.agent.specialties import normalize_specialty
from app.core.dependencies import get_current_user, get_session
from app.models.approval_request import ApprovalRequestType
from app.models.reminder import Reminder, ReminderChannel, ReminderType
from app.repositories.appointment_repo import AppointmentRepository
from app.repositories.doctor_repo import DoctorRepository
from app.repositories.patient_repo import PatientRepository
from app.repositories.reminder_repo import ReminderRepository
from app.schemas.approval import ApprovalRequestCreate
from app.schemas.tools import (
    BookAppointmentRequest,
    BookAppointmentResponse,
    CheckAvailabilityRequest,
    CheckAvailabilityResponse,
    DoctorSummary,
    FindDoctorsRequest,
    FindDoctorsResponse,
    GetPatientHistoryRequest,
    GetPatientHistoryResponse,
    SendReminderRequest,
    SendReminderResponse,
    SubmitForApprovalRequest,
    SubmitForApprovalResponse,
)
from app.services.appointment_service import AppointmentService
from app.services.approval_service import ApprovalService
from app.services.doctor_service import DoctorService
from app.services.email_service import send_appointment_confirmation
from app.services.reminder_service import ReminderService
from app.services.risk_engine import assess_booking

router = APIRouter(prefix="/tools", tags=["tools"])


def _as_utc(dt: datetime) -> datetime:
    """DB backends differ: Postgres returns aware datetimes, SQLite naive ones.
    Naive values are stored as UTC, so coerce before any aware comparison."""
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def _resolve_patient_id(session: Session, payload: dict, patient_id: UUID | None = None) -> UUID:
    """Resolve patient UUID — from request if provided, otherwise from JWT user context."""
    if patient_id:
        return patient_id
    patient_repo = PatientRepository(session)
    patient = patient_repo.get_by_user_id(payload["sub"], payload["org_id"])
    if not patient:
        raise HTTPException(status_code=404, detail="Patient record not found")
    return patient.id


@router.post("/find_doctors", response_model=FindDoctorsResponse)
def find_doctors(
    data: FindDoctorsRequest,
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user),
):
    """Resolve a specialty or name into concrete doctors (with IDs) within the org.

    The voice agent calls this first so it can pass a real doctor_id to
    check_availability / book_appointment instead of guessing one."""
    org_id = payload["org_id"]
    service = DoctorService(session)
    doctors = service.list_doctors(org_id)

    # Normalize synonyms ("cardiologist" → "Cardiology") so patient phrasing
    # matches the canonical values stored in doctors.specialization.
    spec = (normalize_specialty(data.specialization) or "").lower()
    name = (data.name or "").strip().lower()
    logger.info(
        "find_doctors query — org={org} | specialization_raw={raw!r} | normalized={norm!r} | name={name!r}",
        org=org_id, raw=data.specialization, norm=spec or None, name=name or None,
    )

    def spec_matches(db_value: str | None) -> bool:
        if not spec:
            return True
        db = (db_value or "").strip().lower()
        # Bidirectional substring: "cardiology" matches "Cardiology" and an
        # unnormalized "cardiology department" still matches "Cardiology".
        return bool(db) and (spec in db or db in spec)

    matched = [
        d for d in doctors
        if spec_matches(d.specialization)
        and (not name or name in (d.full_name or "").lower())
    ]
    logger.info(
        "find_doctors result — org={org} | matched={n}/{total} | doctors={docs}",
        org=org_id, n=len(matched), total=len(doctors),
        docs=[(str(d.id), d.full_name, d.specialization) for d in matched],
    )

    return FindDoctorsResponse(
        doctors=[
            DoctorSummary(
                doctor_id=d.id,
                name=d.full_name,
                specialization=d.specialization,
                is_available=d.is_available,
            )
            for d in matched
        ]
    )


@router.post("/check_availability", response_model=CheckAvailabilityResponse)
def check_availability(
    data: CheckAvailabilityRequest,
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user),
):
    org_id = payload["org_id"]
    logger.debug(
        "check_availability called — doctor_id={doc} (type={t}), date={date}, org_id={org}",
        doc=data.doctor_id,
        t=type(data.doctor_id).__name__,
        date=data.date,
        org=org_id,
    )
    service = AppointmentService(session)
    slots = service.get_doctor_availability(data.doctor_id, org_id, data.date)
    available = slots[0]["slots"] if slots else []
    return CheckAvailabilityResponse(available_slots=available)


_SCHEDULE_CSV = Path(__file__).resolve().parents[4] / "data" / "doctor_schedule.csv"


def _load_doctor_schedule() -> list[dict]:
    if not _SCHEDULE_CSV.exists():
        logger.warning("Doctor schedule CSV not found at {path}", path=_SCHEDULE_CSV)
        return []
    with _SCHEDULE_CSV.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


@router.post("/get_doctor_schedule")
def get_doctor_schedule(data: GetDoctorScheduleRequest) -> GetDoctorScheduleResponse:
    """Return the weekly schedule for a doctor by name or specialty from the CSV."""
    schedule = _load_doctor_schedule()
    if data.doctor_name:
        schedule = [r for r in schedule if data.doctor_name.lower() in r["doctor_name"].lower()]
    if data.specialty:
        schedule = [r for r in schedule if data.specialty.lower() in r["specialty"].lower()]
    return GetDoctorScheduleResponse(schedule=schedule)


@router.post("/book_appointment", response_model=BookAppointmentResponse)
def book_appointment(
    data: BookAppointmentRequest,
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user),
):
    org_id = payload["org_id"]
    patient_id = _resolve_patient_id(session, payload, data.patient_id)
    service = AppointmentService(session)

    # Validate that doctor_id refers to a real doctor in this org.
    doctor = DoctorRepository(session).get_by_id(data.doctor_id, org_id)
    if not doctor:
        raise HTTPException(
            status_code=400,
            detail=f"Doctor {data.doctor_id} not found in this organization. "
                   "Use find_doctors to get a valid doctor_id before booking.",
        )

    # Coerce scheduled_at to timezone-aware UTC — the DB column is
    # DateTime(timezone=True) and psycopg3 rejects naive datetimes.
    scheduled_at = _as_utc(data.scheduled_at)

    # --- HITL decision engine: auto-execute vs human approval ---------------
    patient = PatientRepository(session).get_by_id(patient_id, org_id)
    slot_taken = any(
        _as_utc(a.scheduled_at) == scheduled_at
        for a in service.repo.get_doctor_slots(
            data.doctor_id, org_id, scheduled_at, scheduled_at
        )
    )
    decision = assess_booking(
        is_vip=bool(patient and patient.is_vip),
        slot_taken=slot_taken,
        ai_confidence=data.ai_confidence,
    )
    if decision.requires_approval:
        approval_service = ApprovalService(session)
        request = approval_service.submit(
            org_id,
            payload["sub"],
            ApprovalRequestCreate(
                patient_id=patient_id,
                request_type=decision.request_type,
                reason=decision.reason,
                ai_summary=data.reason or "Appointment booking request",
                ai_confidence=data.ai_confidence,
                requested_action={
                    "action": "book_appointment",
                    "patient_id": str(patient_id),
                    "doctor_id": str(data.doctor_id),
                    "scheduled_at": scheduled_at.isoformat(),
                    "reason": data.reason,
                },
            ),
        )
        logger.info(
            "Booking routed to HITL queue — approval={id} | type={t} | patient={p}",
            id=request.id, t=decision.request_type.value, p=patient_id,
        )
        return BookAppointmentResponse(
            appointment_id=None,
            status="pending_approval",
            message=(
                "This request requires staff review before it can be completed. "
                f"Reason: {decision.reason}. "
                "Our team has been notified and will confirm shortly."
            ),
            approval_request_id=request.id,
        )
    # -------------------------------------------------------------------------

    from app.schemas.appointment import AppointmentCreate
    payload_data = AppointmentCreate(
        **data.model_dump(exclude={"patient_id", "ai_confidence", "scheduled_at"}),
        patient_id=patient_id,
        scheduled_at=scheduled_at,
    )
    created = service.create_appointment(org_id, payload_data)

    logger.info(
        "Appointment booked — id={id} | patient={p} | doctor={d}",
        id=created.id, p=patient_id, d=created.doctor_id,
    )

    send_appointment_confirmation(session, created, org_id)

    # Schedule reminders: 24 hours and 1 hour before the appointment
    now = datetime.now(timezone.utc)
    reminder_service = ReminderService(session)
    reminder_repo = ReminderRepository(session)
    existing = reminder_repo.list_by_appointment(created.id, org_id)

    for hours_before, label in [(24, "24h"), (1, "1h")]:
        reminder_at = _as_utc(created.scheduled_at) - timedelta(hours=hours_before)
        if reminder_at > now and not any(
            r.channel == ReminderChannel.email
            and r.type == ReminderType.appointment
            and abs((r.scheduled_at - reminder_at).total_seconds()) < 3600
            for r in existing
        ):
            reminder = Reminder(
                org_id=org_id,
                appointment_id=created.id,
                patient_id=patient_id,
                type=ReminderType.appointment,
                channel=ReminderChannel.email,
                scheduled_at=reminder_at,
                message=f"Appointment reminder ({label} before)",
            )
            reminder_service.create_reminder(reminder)
            logger.info("Reminder scheduled — appt={id} | at={at} | label={label}",
                        id=created.id, at=reminder_at.isoformat(), label=label)

    return BookAppointmentResponse(
        appointment_id=created.id,
        status=created.status.value,
        message="Appointment booked successfully",
    )


@router.post("/get_patient_history", response_model=GetPatientHistoryResponse)
def get_patient_history(
    data: GetPatientHistoryRequest,
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user),
):
    org_id = payload["org_id"]
    patient_id = _resolve_patient_id(session, payload, data.patient_id)
    patient_repo = PatientRepository(session)
    appt_repo = AppointmentRepository(session)

    patient = patient_repo.get_by_id(patient_id, org_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    appointments = appt_repo.list_by_patient(patient_id, org_id)
    upcoming = []
    past = []
    now = datetime.now(timezone.utc)
    for a in appointments:
        d = {"id": str(a.id), "scheduled_at": a.scheduled_at.isoformat(), "status": a.status.value}
        if a.scheduled_at > now:
            upcoming.append(d)
        else:
            past.append(d)

    return GetPatientHistoryResponse(
        patient_name=f"{patient.first_name} {patient.last_name}",
        upcoming_appointments=upcoming,
        past_appointments=past,
    )


@router.post("/send_reminder", response_model=SendReminderResponse)
def send_reminder(
    data: SendReminderRequest,
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user),
):
    org_id = payload["org_id"]
    patient_id = _resolve_patient_id(session, payload, data.patient_id)
    service = ReminderService(session)
    reminder = Reminder(
        org_id=org_id,
        appointment_id=data.appointment_id,
        patient_id=patient_id,
        type=ReminderType.appointment,
        channel=ReminderChannel(data.channel),
        scheduled_at=datetime.now(timezone.utc),
        message="Appointment reminder",
    )
    created = service.create_reminder(reminder)
    return SendReminderResponse(
        reminder_id=created.id,
        status="pending",
        message="Reminder queued for delivery",
    )


@router.post("/submit_for_approval", response_model=SubmitForApprovalResponse)
def submit_for_approval(
    data: SubmitForApprovalRequest,
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user),
):
    """HITL entry point for the AI agent: queue a request for human review.

    The agent calls this when the decision engine (or its own judgment) flags a
    request as high-risk — urgent symptoms, late cancellation, VIP handling,
    manual doctor assignment, or low confidence."""
    org_id = payload["org_id"]
    try:
        patient_id = _resolve_patient_id(session, payload, data.patient_id)
    except HTTPException:
        patient_id = None  # staff-submitted requests may have no patient record

    try:
        request_type = ApprovalRequestType(data.request_type)
    except ValueError:
        request_type = ApprovalRequestType.other

    approval_service = ApprovalService(session)
    request = approval_service.submit(
        org_id,
        payload["sub"],
        ApprovalRequestCreate(
            patient_id=patient_id,
            appointment_id=data.appointment_id,
            request_type=request_type,
            reason=data.reason,
            ai_summary=data.ai_summary,
            ai_confidence=data.ai_confidence,
            requested_action=data.requested_action,
        ),
    )
    return SubmitForApprovalResponse(
        approval_request_id=request.id,
        status="pending",
        message=(
            "Your request has been escalated to our clinical staff for review. "
            "A team member will contact you shortly."
        ),
    )

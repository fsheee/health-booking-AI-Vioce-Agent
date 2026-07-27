"""Email service for appointment notifications.

Sends transactional emails via SMTP with ICS calendar invites
for confirmation and reschedule notifications.
Email failures are logged but never bubble up — the appointment
lifecycle continues regardless of delivery status.
"""

import smtplib
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING
from uuid import UUID

from loguru import logger
from sqlmodel import Session

from app.core.config import settings
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.organization import Organization
from app.models.patient import Patient
from app.models.reminder import Reminder
from app.models.user import User
from app.services.calendar_service import appointment_ics, org_location
from app.services.email_templates import (
    approval_granted_email,
    approval_rejected_email,
    approval_requested_email,
    cancellation_email,
    confirmation_email,
    emergency_escalation_email,
    hitl_approved_email,
    hitl_rejected_email,
    hitl_under_review_email,
    reminder_1h_email,
    reminder_24h_email,
    reschedule_email,
)

if TYPE_CHECKING:
    from app.models.approval_request import ApprovalRequest


def _smtp_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_user and settings.smtp_password)


def _org_details(session: Session, org_id: UUID) -> dict:
    org = session.get(Organization, org_id)
    if not org:
        return {
            "clinic_name": "Healthcare Clinic",
            "clinic_phone": "",
            "clinic_address": "",
            "clinic_email": "",
        }
    return {
        "clinic_name": org.name or "Healthcare Clinic",
        "clinic_phone": org.phone or "",
        "clinic_address": org.address or "",
        "clinic_email": org.email or "",
    }


def _send_email(to_email: str, subject: str, html_body: str,
                ics_content: str | None = None) -> bool:
    if not _smtp_configured():
        logger.warning("SMTP not configured — email not sent to {to}", to=to_email)
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        if ics_content:
            ics_part = MIMEApplication(ics_content, _subtype="calendar; method=REQUEST")
            ics_part.add_header("Content-Disposition", "attachment; filename=appointment.ics")
            msg.attach(ics_part)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            if settings.smtp_use_tls:
                server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)

        logger.info("Email sent — to={to} | subject={subj}", to=to_email, subj=subject)
        return True
    except Exception as e:
        logger.error(
            "Email delivery failed — to={to} | subject={subj} | error={err}",
            to=to_email, subj=subject, err=str(e),
        )
        return False


def _lookup_appointment_details(
    session: Session, appointment: Appointment, org_id: UUID,
) -> dict | None:
    patient = session.get(Patient, appointment.patient_id)
    if not patient or not patient.email:
        logger.warning("Patient or email missing — appt={id}", id=appointment.id)
        return None

    doctor = session.get(Doctor, appointment.doctor_id)
    if not doctor:
        logger.warning("Doctor missing — appt={id}", id=appointment.id)
        return None

    doctor_user = session.get(User, doctor.user_id)
    doctor_name = doctor_user.full_name if doctor_user else "Unknown Doctor"

    org_info = _org_details(session, org_id)
    scheduled = appointment.scheduled_at
    return {
        "patient_name": f"{patient.first_name} {patient.last_name}".strip(),
        "patient_email": patient.email,
        "doctor_name": doctor_name,
        "specialization": doctor.specialization or "General",
        "appointment_date": scheduled.strftime("%A, %B %d, %Y"),
        "appointment_time": scheduled.strftime("%I:%M %p").lstrip("0"),
        "appointment_id": str(appointment.id),
        "scheduled_at": scheduled,
        "duration_minutes": appointment.duration_minutes or 30,
        "clinic_name": org_info["clinic_name"],
        "clinic_phone": org_info["clinic_phone"],
        "clinic_address": org_info["clinic_address"],
        "clinic_email": org_info["clinic_email"],
    }


# ---------------------------------------------------------------------------
# Public send functions
# ---------------------------------------------------------------------------


def send_appointment_confirmation(session: Session, appointment: Appointment, org_id: UUID) -> None:
    details = _lookup_appointment_details(session, appointment, org_id)
    if not details:
        return

    org = session.get(Organization, org_id)
    ics_content = appointment_ics(
        appointment_id=details["appointment_id"],
        doctor_name=details["doctor_name"],
        patient_name=details["patient_name"],
        patient_email=details["patient_email"],
        scheduled_at=details["scheduled_at"],
        duration_minutes=details["duration_minutes"],
        location=org_location(org),
        clinic_name=details["clinic_name"],
        clinic_email=details["clinic_email"] or settings.smtp_from_email,
    )

    subject, html = confirmation_email(**details)
    _send_email(details["patient_email"], subject, html, ics_content=ics_content)
    logger.info("Confirmation email sent — appt={id} | patient={p}",
                id=appointment.id, p=details["patient_name"])


def send_appointment_cancellation(
    session: Session, appointment: Appointment, org_id: UUID, reason: str = "",
) -> None:
    details = _lookup_appointment_details(session, appointment, org_id)
    if not details:
        return

    subject, html = cancellation_email(
        patient_name=details["patient_name"],
        doctor_name=details["doctor_name"],
        appointment_date=details["appointment_date"],
        appointment_time=details["appointment_time"],
        reason=reason,
        clinic_name=details["clinic_name"],
        clinic_phone=details["clinic_phone"],
        clinic_address=details["clinic_address"],
        clinic_email=details["clinic_email"],
    )
    _send_email(details["patient_email"], subject, html)
    logger.info("Cancellation email sent — appt={id} | patient={p}",
                id=appointment.id, p=details["patient_name"])


def send_appointment_rescheduled(
    session: Session,
    appointment: Appointment,
    org_id: UUID,
    old_scheduled_at: datetime | None = None,
    reason: str = "",
) -> None:
    details = _lookup_appointment_details(session, appointment, org_id)
    if not details:
        return

    old_date = old_scheduled_at.strftime("%A, %B %d, %Y") if old_scheduled_at else "—"
    old_time = old_scheduled_at.strftime("%I:%M %p").lstrip("0") if old_scheduled_at else "—"

    org = session.get(Organization, org_id)
    ics_content = appointment_ics(
        appointment_id=details["appointment_id"],
        doctor_name=details["doctor_name"],
        patient_name=details["patient_name"],
        patient_email=details["patient_email"],
        scheduled_at=details["scheduled_at"],
        duration_minutes=details["duration_minutes"],
        location=org_location(org),
        clinic_name=details["clinic_name"],
        clinic_email=details["clinic_email"] or settings.smtp_from_email,
    )

    subject, html = reschedule_email(
        patient_name=details["patient_name"],
        doctor_name=details["doctor_name"],
        specialization=details["specialization"],
        old_date=old_date,
        old_time=old_time,
        new_date=details["appointment_date"],
        new_time=details["appointment_time"],
        appointment_id=details["appointment_id"],
        reason=reason,
        clinic_name=details["clinic_name"],
        clinic_phone=details["clinic_phone"],
        clinic_address=details["clinic_address"],
        clinic_email=details["clinic_email"],
    )
    _send_email(details["patient_email"], subject, html, ics_content=ics_content)
    logger.info("Reschedule email sent — appt={id} | patient={p}",
                id=appointment.id, p=details["patient_name"])


def send_appointment_reminder(session: Session, appointment: Appointment, org_id: UUID,
                              reminder: Reminder | None = None) -> None:
    """Send a reminder email.

    Supports two tiers based on the reminder's message label:
    - '24h' → full reminder with location and instructions
    - '1h'  → short "upcoming soon" reminder
    Falls back to the 24h template when the label is unknown.
    """
    details = _lookup_appointment_details(session, appointment, org_id)
    if not details:
        return

    label = (reminder.message or "") if reminder else ""
    is_one_hour = "1h" in label

    if is_one_hour:
        subject, html = reminder_1h_email(
            patient_name=details["patient_name"],
            doctor_name=details["doctor_name"],
            appointment_time=details["appointment_time"],
            clinic_name=details["clinic_name"],
            clinic_phone=details["clinic_phone"],
            clinic_address=details["clinic_address"],
            clinic_email=details["clinic_email"],
        )
    else:
        subject, html = reminder_24h_email(
            patient_name=details["patient_name"],
            doctor_name=details["doctor_name"],
            specialization=details["specialization"],
            appointment_date=details["appointment_date"],
            appointment_time=details["appointment_time"],
            clinic_name=details["clinic_name"],
            clinic_phone=details["clinic_phone"],
            clinic_address=details["clinic_address"],
            clinic_email=details["clinic_email"],
        )

    _send_email(details["patient_email"], subject, html)
    logger.info("Reminder email sent — appt={id} | patient={p} | label={label}",
                id=appointment.id, p=details["patient_name"], label=label or "24h")


# ---------------------------------------------------------------------------
# HITL / Approval emails
# ---------------------------------------------------------------------------


def _clinic_name(session: Session, org_id: UUID) -> str:
    org = session.get(Organization, org_id)
    return org.name if org else "Healthcare Clinic"


def _clinic_details(session: Session, org_id: UUID) -> dict:
    return _org_details(session, org_id)


def _patient_display(session: Session, patient_id: UUID | None) -> tuple[str, str | None]:
    if not patient_id:
        return "Unknown Patient", None
    patient = session.get(Patient, patient_id)
    if not patient:
        return "Unknown Patient", None
    return f"{patient.first_name} {patient.last_name}".strip(), patient.email


def send_approval_requested(session: Session, request: "ApprovalRequest") -> None:
    from sqlmodel import select

    from app.models.user import UserRole

    clinic = _clinic_details(session, request.org_id)
    patient_name, _ = _patient_display(session, request.patient_id)
    staff = session.exec(
        select(User).where(
            User.org_id == request.org_id,
            User.role.in_([UserRole.admin, UserRole.front_desk]),
        )
    ).all()
    if not staff:
        logger.warning("No staff to notify for approval request {id}", id=request.id)
        return
    for member in staff:
        if not member.email:
            continue
        subject, html = approval_requested_email(
            staff_name=member.full_name or "Team Member",
            patient_name=patient_name,
            request_type=request.request_type.value.replace("_", " ").title(),
            reason=request.reason or "—",
            ai_summary=request.ai_summary or "—",
            ai_confidence=request.ai_confidence,
            clinic_name=clinic["clinic_name"],
            clinic_phone=clinic["clinic_phone"],
            clinic_address=clinic["clinic_address"],
            clinic_email=clinic["clinic_email"],
        )
        _send_email(member.email, subject, html)
    logger.info("Approval-requested emails sent — request={id} | staff_notified={n}",
                id=request.id, n=len(staff))


def send_hitl_under_review(session: Session, request: "ApprovalRequest") -> None:
    from app.models.doctor import Doctor
    from app.models.user import User

    clinic = _clinic_details(session, request.org_id)
    patient_name, patient_email = _patient_display(session, request.patient_id)
    if not patient_email:
        logger.warning("Patient email missing — HITL under-review not sent | request={id}", id=request.id)
        return

    action = request.requested_action or {}
    doctor_name = None
    if action.get("doctor_id"):
        doctor = session.get(Doctor, UUID(action["doctor_id"]))
        if doctor:
            doctor_user = session.get(User, doctor.user_id)
            doctor_name = doctor_user.full_name if doctor_user else None

    reason_parts = [request.reason or "Routine review"]
    if request.request_type.value:
        type_label = request.request_type.value.replace("_", " ").title()
        reason_parts.insert(0, f"[{type_label}]")
    if doctor_name:
        reason_parts.append(f" — Doctor: {doctor_name}")
    full_reason = " ".join(reason_parts)

    subject, html = hitl_under_review_email(
        patient_name=patient_name,
        reason=full_reason,
        clinic_name=clinic["clinic_name"],
        clinic_phone=clinic["clinic_phone"],
        clinic_address=clinic["clinic_address"],
        clinic_email=clinic["clinic_email"],
    )
    _send_email(patient_email, subject, html)
    logger.info("HITL under-review email sent — request={id} | patient={p}",
                id=request.id, p=patient_name)


def send_hitl_approved(session: Session, request: "ApprovalRequest") -> None:
    from app.models.appointment import Appointment
    from app.models.doctor import Doctor
    from app.models.user import User

    clinic = _clinic_details(session, request.org_id)
    patient_name, patient_email = _patient_display(session, request.patient_id)
    if not patient_email:
        return

    # Prefer the actual appointment (already created by _execute_action)
    # over the deferred-action metadata for accurate details.
    doctor_name = None
    appointment_date = "—"
    appointment_time = "—"

    if request.appointment_id:
        apt = session.get(Appointment, request.appointment_id)
        if apt:
            doctor = session.get(Doctor, apt.doctor_id)
            if doctor:
                doctor_user = session.get(User, doctor.user_id)
                doctor_name = doctor_user.full_name if doctor_user else None
            if apt.scheduled_at:
                appointment_date = apt.scheduled_at.strftime("%A, %B %d, %Y")
                appointment_time = apt.scheduled_at.strftime("%I:%M %p").lstrip("0")

    if not doctor_name:
        # Fallback to deferred-action metadata (approvals not linked to an appointment).
        action = request.requested_action or {}
        if action.get("doctor_id"):
            doctor = session.get(Doctor, UUID(action["doctor_id"]))
            if doctor:
                doctor_user = session.get(User, doctor.user_id)
                doctor_name = doctor_user.full_name if doctor_user else None
        if not appointment_date or appointment_date == "—":
            if action.get("scheduled_at"):
                try:
                    scheduled_at = datetime.fromisoformat(action["scheduled_at"])
                    appointment_date = scheduled_at.strftime("%A, %B %d, %Y") if scheduled_at else "—"
                    appointment_time = scheduled_at.strftime("%I:%M %p").lstrip("0") if scheduled_at else "—"
                except (ValueError, TypeError):
                    pass

    doctor_name = doctor_name or "Assigned Doctor"

    subject, html = hitl_approved_email(
        patient_name=patient_name,
        doctor_name=doctor_name,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        clinic_name=clinic["clinic_name"],
        clinic_phone=clinic["clinic_phone"],
        clinic_address=clinic["clinic_address"],
        clinic_email=clinic["clinic_email"],
    )
    _send_email(patient_email, subject, html)
    logger.info("HITL approved email sent — request={id} | patient={p}",
                id=request.id, p=patient_name)


def send_hitl_rejected(session: Session, request: "ApprovalRequest") -> None:
    clinic = _clinic_details(session, request.org_id)
    patient_name, patient_email = _patient_display(session, request.patient_id)
    if not patient_email:
        return

    subject, html = hitl_rejected_email(
        patient_name=patient_name,
        reason=request.reason,
        reviewer_comment=request.reviewer_comment,
        clinic_name=clinic["clinic_name"],
        clinic_phone=clinic["clinic_phone"],
        clinic_address=clinic["clinic_address"],
        clinic_email=clinic["clinic_email"],
    )
    _send_email(patient_email, subject, html)
    logger.info("HITL rejected email sent — request={id} | patient={p}",
                id=request.id, p=patient_name)


def send_approval_decision(session: Session, request: "ApprovalRequest", approved: bool) -> None:
    clinic = _clinic_details(session, request.org_id)
    patient_name, patient_email = _patient_display(session, request.patient_id)
    if not patient_email:
        logger.warning("Patient email missing — approval decision not emailed | request={id}", id=request.id)
        return
    template = approval_granted_email if approved else approval_rejected_email
    subject, html = template(
        patient_name=patient_name,
        request_type=request.request_type.value.replace("_", " ").title(),
        comment=request.reviewer_comment,
        clinic_name=clinic["clinic_name"],
        clinic_phone=clinic["clinic_phone"],
        clinic_address=clinic["clinic_address"],
        clinic_email=clinic["clinic_email"],
    )
    _send_email(patient_email, subject, html)
    logger.info("Approval decision email sent — request={id} | approved={a} | patient={p}",
                id=request.id, a=approved, p=patient_name)


def send_emergency_escalation(session: Session, request: "ApprovalRequest") -> None:
    clinic = _clinic_details(session, request.org_id)
    patient_name, patient_email = _patient_display(session, request.patient_id)
    if not patient_email:
        logger.warning("Patient email missing — emergency escalation not sent | request={id}", id=request.id)
        return

    transcript = (request.ai_summary or "")
    transcript = transcript.replace("Patient said: ", "").replace(
        ". Emergency response was given; human follow-up required.", ""
    )
    subject, html = emergency_escalation_email(
        patient_name=patient_name,
        transcript=transcript,
        clinic_name=clinic["clinic_name"],
        clinic_phone=clinic["clinic_phone"],
        clinic_address=clinic["clinic_address"],
        clinic_email=clinic["clinic_email"],
    )
    _send_email(patient_email, subject, html)
    logger.info("Emergency escalation email sent — request={id} | patient={p}",
                id=request.id, p=patient_name)
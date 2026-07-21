"""Email service for appointment notifications.

Sends transactional emails via SMTP.  Email failures are logged but never
bubble up — the appointment lifecycle continues regardless of delivery status.
"""

import smtplib
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
from app.models.user import User
from app.services.email_templates import (
    approval_granted_email,
    approval_rejected_email,
    approval_requested_email,
    cancellation_email,
    confirmation_email,
    reminder_email,
)

if TYPE_CHECKING:
    from app.models.approval_request import ApprovalRequest


def _smtp_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_user and settings.smtp_password)


def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    if not _smtp_configured():
        logger.warning("SMTP not configured — email not sent to {to}", to=to_email)
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

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
    session: Session, appointment: Appointment, org_id: UUID
) -> dict | None:
    """Fetch patient, doctor, user, and org details for an appointment.

    Returns a dict of resolved display values or None if critical data is
    missing (in which case the caller should skip emailing).
    """
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

    org = session.get(Organization, org_id)
    clinic_name = org.name if org else "Healthcare Clinic"

    scheduled = appointment.scheduled_at
    return {
        "patient_name": f"{patient.first_name} {patient.last_name}".strip(),
        "patient_email": patient.email,
        "doctor_name": doctor_name,
        "specialization": doctor.specialization or "General",
        "appointment_date": scheduled.strftime("%A, %B %d, %Y"),
        "appointment_time": scheduled.strftime("%I:%M %p").lstrip("0"),
        "appointment_id": str(appointment.id),
        "clinic_name": clinic_name,
    }


def send_appointment_confirmation(session: Session, appointment: Appointment, org_id: UUID) -> None:
    """Send a confirmation email after a successful booking."""
    details = _lookup_appointment_details(session, appointment, org_id)
    if not details:
        return
    subject, html = confirmation_email(
        patient_name=details["patient_name"],
        doctor_name=details["doctor_name"],
        specialization=details["specialization"],
        appointment_date=details["appointment_date"],
        appointment_time=details["appointment_time"],
        appointment_id=details["appointment_id"],
        clinic_name=details["clinic_name"],
    )
    _send_email(details["patient_email"], subject, html)
    logger.info("Confirmation email sent — appt={id} | patient={p}", id=appointment.id, p=details["patient_name"])


def send_appointment_reminder(session: Session, appointment: Appointment, org_id: UUID) -> None:
    """Send a reminder email 24h before the appointment."""
    details = _lookup_appointment_details(session, appointment, org_id)
    if not details:
        return
    subject, html = reminder_email(
        patient_name=details["patient_name"],
        doctor_name=details["doctor_name"],
        specialization=details["specialization"],
        appointment_date=details["appointment_date"],
        appointment_time=details["appointment_time"],
        appointment_id=details["appointment_id"],
        clinic_name=details["clinic_name"],
    )
    _send_email(details["patient_email"], subject, html)
    logger.info("Reminder email sent — appt={id} | patient={p}", id=appointment.id, p=details["patient_name"])


def send_appointment_cancellation(session: Session, appointment: Appointment, org_id: UUID) -> None:
    """Send a cancellation notice after an appointment is cancelled."""
    details = _lookup_appointment_details(session, appointment, org_id)
    if not details:
        return
    subject, html = cancellation_email(
        patient_name=details["patient_name"],
        doctor_name=details["doctor_name"],
        specialization=details["specialization"],
        appointment_date=details["appointment_date"],
        appointment_time=details["appointment_time"],
        clinic_name=details["clinic_name"],
    )
    _send_email(details["patient_email"], subject, html)
    logger.info("Cancellation email sent — appt={id} | patient={p}", id=appointment.id, p=details["patient_name"])


def _clinic_name(session: Session, org_id: UUID) -> str:
    org = session.get(Organization, org_id)
    return org.name if org else "Healthcare Clinic"


def _patient_display(session: Session, patient_id: UUID | None) -> tuple[str, str | None]:
    """Return (display name, email) for a patient, tolerating missing records."""
    if not patient_id:
        return "Unknown Patient", None
    patient = session.get(Patient, patient_id)
    if not patient:
        return "Unknown Patient", None
    return f"{patient.first_name} {patient.last_name}".strip(), patient.email


def send_approval_requested(session: Session, request: "ApprovalRequest") -> None:
    """Notify org staff (admin + front_desk) that a request awaits review."""
    from sqlmodel import select

    from app.models.user import UserRole

    clinic_name = _clinic_name(session, request.org_id)
    patient_name, _ = _patient_display(session, request.patient_id)
    staff = session.exec(
        select(User).where(
            User.org_id == request.org_id,
            User.role.in_([UserRole.admin, UserRole.front_desk]),  # type: ignore[attr-defined]
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
            clinic_name=clinic_name,
        )
        _send_email(member.email, subject, html)
    logger.info("Approval-requested emails sent — request={id} | staff_notified={n}",
                id=request.id, n=len(staff))


def send_approval_decision(session: Session, request: "ApprovalRequest", approved: bool) -> None:
    """Notify the patient that their request was approved or rejected."""
    clinic_name = _clinic_name(session, request.org_id)
    patient_name, patient_email = _patient_display(session, request.patient_id)
    if not patient_email:
        logger.warning("Patient email missing — approval decision not emailed | request={id}", id=request.id)
        return
    template = approval_granted_email if approved else approval_rejected_email
    subject, html = template(
        patient_name=patient_name,
        request_type=request.request_type.value.replace("_", " ").title(),
        comment=request.reviewer_comment,
        clinic_name=clinic_name,
    )
    _send_email(patient_email, subject, html)
    logger.info("Approval decision email sent — request={id} | approved={a} | patient={p}",
                id=request.id, a=approved, p=patient_name)

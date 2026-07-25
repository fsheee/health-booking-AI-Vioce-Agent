"""ICS calendar invite (iCalendar / .ics) generation.

Generates standard .ics strings so patients can add appointments
directly to Google Calendar, Outlook, or Apple Calendar.
Uses raw iCalendar formatting — no external dependency needed.
"""

from datetime import datetime, timedelta, timezone

from app.models.organization import Organization

PRODID = "-//Healthcare Clinic//Appointment Calendar//EN"
DT_FMT = "%Y%m%dT%H%M%S"


def _format_dt(dt: datetime) -> str:
    """Format a datetime for iCalendar (UTC)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime(DT_FMT) + "Z"


def _fold(line: str) -> str:
    """Fold long lines per RFC 5545 (max 75 octets)."""
    if len(line) <= 75:
        return line + "\r\n"
    return line[:75] + "\r\n " + _fold(line[75:])[2:]


def appointment_ics(
    appointment_id: str,
    doctor_name: str,
    patient_name: str,
    patient_email: str,
    scheduled_at: datetime,
    duration_minutes: int,
    location: str,
    clinic_name: str,
    clinic_email: str,
) -> str:
    """Return a complete .ics string for an appointment event."""
    dtstart = scheduled_at
    dtend = scheduled_at + timedelta(minutes=duration_minutes or 30)

    uid = f"{appointment_id}@healthcare-clinic"
    now_stamp = _format_dt(datetime.now(timezone.utc))
    start = _format_dt(dtstart)
    end = _format_dt(dtend)

    summary = f"Appointment with {doctor_name}"
    desc = (
        f"Appointment ID: {appointment_id}\\n"
        f"Doctor: {doctor_name}\\n"
        f"Clinic: {clinic_name}\\n"
        f"Please arrive 10 minutes before your scheduled time."
    )
    loc = location.replace(",", "\\,")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "METHOD:REQUEST",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{now_stamp}",
        f"DTSTART:{start}",
        f"DTEND:{end}",
        f"SUMMARY:{summary}",
        _fold(f"DESCRIPTION:{desc}").strip(),
        _fold(f"LOCATION:{loc}").strip(),
        f"ORGANIZER;CN={clinic_name}:mailto:{clinic_email}",
        f"ATTENDEE;CN={patient_name};ROLE=REQ-PARTICIPANT;RSVP=TRUE:mailto:{patient_email}",
        "STATUS:CONFIRMED",
        "CLASS:PUBLIC",
        "TRANSP:OPAQUE",
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        "DESCRIPTION:Reminder: Upcoming appointment",
        "TRIGGER:-PT10M",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(lines) + "\r\n"


def _org_location(org: Organization | None) -> str:
    if not org:
        return "Healthcare Clinic"
    parts = [org.name or "Healthcare Clinic"]
    if org.address:
        parts.append(org.address)
    return ", ".join(parts)


def org_location(org: Organization | None) -> str:
    return _org_location(org)
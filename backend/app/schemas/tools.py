from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator


def coerce_uuid(v: object) -> UUID | None:
    if v is None:
        return None
    if isinstance(v, UUID):
        return v
    if isinstance(v, str):
        return UUID(v)
    raise ValueError(f"Expected UUID or string, got {type(v).__name__}: {v!r}")


class FindDoctorsRequest(BaseModel):
    specialization: str | None = None
    name: str | None = None


class DoctorSummary(BaseModel):
    doctor_id: UUID
    name: str | None = None
    specialization: str | None = None
    is_available: bool


class FindDoctorsResponse(BaseModel):
    doctors: list[DoctorSummary]


class CheckAvailabilityRequest(BaseModel):
    doctor_id: Annotated[UUID, BeforeValidator(coerce_uuid)]
    date: str


class CheckAvailabilityResponse(BaseModel):
    available_slots: list[str]


class BookAppointmentRequest(BaseModel):
    doctor_id: Annotated[UUID, BeforeValidator(coerce_uuid)]
    scheduled_at: datetime
    reason: str | None = None
    patient_id: Annotated[UUID | None, BeforeValidator(coerce_uuid)] = None
    # Self-reported model confidence (0.0–1.0); below threshold the booking is
    # routed to the HITL approval queue instead of auto-executing.
    ai_confidence: float | None = None


class BookAppointmentResponse(BaseModel):
    appointment_id: UUID | None = None
    status: str
    message: str
    approval_request_id: UUID | None = None


class GetPatientHistoryRequest(BaseModel):
    patient_id: Annotated[UUID | None, BeforeValidator(coerce_uuid)] = None


class GetPatientHistoryResponse(BaseModel):
    patient_name: str
    upcoming_appointments: list[dict]
    past_appointments: list[dict]


class SendReminderRequest(BaseModel):
    appointment_id: Annotated[UUID, BeforeValidator(coerce_uuid)]
    channel: str = "sms"
    patient_id: Annotated[UUID | None, BeforeValidator(coerce_uuid)] = None


class SendReminderResponse(BaseModel):
    reminder_id: UUID
    status: str
    message: str


class SubmitForApprovalRequest(BaseModel):
    request_type: str = "other"
    reason: str | None = None
    ai_summary: str | None = None
    ai_confidence: float | None = None
    requested_action: dict | None = None
    appointment_id: Annotated[UUID | None, BeforeValidator(coerce_uuid)] = None
    patient_id: Annotated[UUID | None, BeforeValidator(coerce_uuid)] = None


class SubmitForApprovalResponse(BaseModel):
    approval_request_id: UUID
    status: str
    message: str

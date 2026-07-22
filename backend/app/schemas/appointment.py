from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.appointment import AppointmentStatus


class AppointmentCreate(BaseModel):
    patient_id: UUID
    doctor_id: UUID
    scheduled_at: datetime
    duration_minutes: int = 30
    reason: str | None = None


class AppointmentUpdate(BaseModel):
    scheduled_at: datetime | None = None
    duration_minutes: int | None = None
    status: AppointmentStatus | None = None
    reason: str | None = None
    notes: str | None = None


class AppointmentResponse(BaseModel):
    id: UUID
    org_id: UUID
    patient_id: UUID
    doctor_id: UUID
    scheduled_at: datetime
    duration_minutes: int
    status: AppointmentStatus
    reason: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class AppointmentDetailResponse(AppointmentResponse):
    doctor_name: str | None = None
    specialization: str | None = None
    patient_name: str | None = None


class AppointmentReschedule(BaseModel):
    scheduled_at: datetime
    reason: str | None = None

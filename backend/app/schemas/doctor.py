from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DoctorCreate(BaseModel):
    user_id: UUID
    specialization: str | None = None
    license_number: str | None = None
    is_available: bool = True


class DoctorUpdate(BaseModel):
    specialization: str | None = None
    license_number: str | None = None
    is_available: bool | None = None


class DoctorResponse(BaseModel):
    id: UUID
    user_id: UUID
    org_id: UUID
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    specialization: str | None = None
    license_number: str | None = None
    is_available: bool
    created_at: datetime
    updated_at: datetime


class AvailabilitySlot(BaseModel):
    doctor_id: UUID
    date: str
    slots: list[str]

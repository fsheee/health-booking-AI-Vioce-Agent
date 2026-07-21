from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    medical_history: str | None = None
    emergency_contact: str | None = None


class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    medical_history: str | None = None
    emergency_contact: str | None = None


class PatientResponse(BaseModel):
    id: UUID
    org_id: UUID
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    medical_history: str | None = None
    emergency_contact: str | None = None
    created_at: datetime
    updated_at: datetime

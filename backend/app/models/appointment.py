import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Integer, Text, func
from sqlmodel import Column, Field, SQLModel


class AppointmentStatus(str, PyEnum):
    scheduled = "scheduled"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"
    no_show = "no_show"


class Appointment(SQLModel, table=True):
    __tablename__ = "appointments"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    org_id: uuid.UUID = Field(
        foreign_key="organizations.id", nullable=False, index=True,
    )
    patient_id: uuid.UUID = Field(
        foreign_key="patients.id", nullable=False, index=True,
    )
    doctor_id: uuid.UUID = Field(
        foreign_key="doctors.id", nullable=False, index=True,
    )
    scheduled_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    duration_minutes: int = Field(default=30, sa_column=Column(Integer, default=30, nullable=False))
    status: AppointmentStatus = Field(
        default=AppointmentStatus.scheduled,
        sa_column=Column(Enum(AppointmentStatus), nullable=False, default=AppointmentStatus.scheduled),
    )
    reason: str | None = Field(sa_column=Column(Text, nullable=True))
    notes: str | None = Field(sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )

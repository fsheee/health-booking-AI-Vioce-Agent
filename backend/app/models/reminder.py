import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Text, func
from sqlmodel import Column, Field, SQLModel


class ReminderType(str, PyEnum):
    appointment = "appointment"
    follow_up = "follow_up"
    medication = "medication"


class ReminderChannel(str, PyEnum):
    sms = "sms"
    email = "email"
    voice = "voice"


class ReminderStatus(str, PyEnum):
    pending = "pending"
    sent = "sent"
    failed = "failed"
    cancelled = "cancelled"


class Reminder(SQLModel, table=True):
    __tablename__ = "reminders"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    org_id: uuid.UUID = Field(
        foreign_key="organizations.id", nullable=False, index=True,
    )
    appointment_id: uuid.UUID | None = Field(
        foreign_key="appointments.id", nullable=True,
    )
    patient_id: uuid.UUID = Field(
        foreign_key="patients.id", nullable=False, index=True,
    )
    type: ReminderType = Field(sa_column=Column(Enum(ReminderType), nullable=False))
    channel: ReminderChannel = Field(sa_column=Column(Enum(ReminderChannel), nullable=False))
    scheduled_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    sent_at: datetime | None = Field(sa_column=Column(DateTime(timezone=True), nullable=True))
    status: ReminderStatus = Field(
        default=ReminderStatus.pending,
        sa_column=Column(Enum(ReminderStatus), nullable=False, default=ReminderStatus.pending),
    )
    message: str | None = Field(sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )

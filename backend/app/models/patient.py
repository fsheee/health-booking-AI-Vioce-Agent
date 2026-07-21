import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, String, Text, func
from sqlmodel import Column, Field, SQLModel


class Patient(SQLModel, table=True):
    __tablename__ = "patients"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    user_id: uuid.UUID | None = Field(
        foreign_key="users.id", nullable=True,
    )
    org_id: uuid.UUID = Field(
        foreign_key="organizations.id", nullable=False, index=True,
    )
    first_name: str = Field(sa_column=Column(String(100), nullable=False))
    last_name: str = Field(sa_column=Column(String(100), nullable=False))
    date_of_birth: date | None = Field(sa_column=Column(Date, nullable=True))
    phone: str = Field(sa_column=Column(String(50), nullable=True))
    email: str = Field(sa_column=Column(String(255), nullable=True))
    address: str | None = Field(sa_column=Column(Text, nullable=True))
    medical_history: str | None = Field(sa_column=Column(Text, nullable=True))
    emergency_contact: str | None = Field(sa_column=Column(Text, nullable=True))
    # VIP patients' AI-initiated bookings are routed to the HITL approval queue.
    is_vip: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, default=False, server_default="false"),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )

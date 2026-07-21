import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import JSON, DateTime, Enum, Float, Text, func
from sqlmodel import Column, Field, SQLModel


class ApprovalRequestType(str, PyEnum):
    emergency_escalation = "emergency_escalation"
    urgent_symptoms = "urgent_symptoms"
    late_cancellation = "late_cancellation"
    vip_request = "vip_request"
    manual_doctor_assignment = "manual_doctor_assignment"
    double_booking = "double_booking"
    low_confidence = "low_confidence"
    appointment_booking = "appointment_booking"
    other = "other"


class ApprovalStatus(str, PyEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class ApprovalRequest(SQLModel, table=True):
    __tablename__ = "approval_requests"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    org_id: uuid.UUID = Field(
        foreign_key="organizations.id", nullable=False, index=True,
    )
    patient_id: uuid.UUID | None = Field(
        foreign_key="patients.id", nullable=True, index=True,
    )
    appointment_id: uuid.UUID | None = Field(
        foreign_key="appointments.id", nullable=True,
    )
    request_type: ApprovalRequestType = Field(
        sa_column=Column(Enum(ApprovalRequestType), nullable=False)
    )
    reason: str | None = Field(sa_column=Column(Text, nullable=True))
    ai_summary: str | None = Field(sa_column=Column(Text, nullable=True))
    # Confidence the AI reported for its own decision (0.0–1.0); below the
    # threshold the decision engine routes to human review.
    ai_confidence: float | None = Field(sa_column=Column(Float, nullable=True))
    # Deferred action to execute when a reviewer approves, e.g. the
    # book_appointment payload {doctor_id, scheduled_at, reason, patient_id}.
    requested_action: dict | None = Field(sa_column=Column(JSON, nullable=True))
    status: ApprovalStatus = Field(
        default=ApprovalStatus.pending,
        sa_column=Column(Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.pending, index=True),
    )
    approved_by: uuid.UUID | None = Field(
        foreign_key="users.id", nullable=True,
    )
    approved_at: datetime | None = Field(sa_column=Column(DateTime(timezone=True), nullable=True))
    reviewer_comment: str | None = Field(sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )

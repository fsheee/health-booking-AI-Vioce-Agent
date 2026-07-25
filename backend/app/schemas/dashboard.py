from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.appointment import AppointmentStatus


class AppointmentItem(BaseModel):
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    patient_name: str | None = None
    doctor_name: str | None = None
    scheduled_at: datetime
    duration_minutes: int
    status: AppointmentStatus
    reason: str | None = None
    created_at: datetime


class PatientItem(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    phone: str | None = None
    email: str | None = None
    created_at: datetime


class VoiceSessionSummary(BaseModel):
    id: UUID
    patient_id: UUID
    started_at: datetime | None
    is_emergency: bool
    escalated_to_human: bool


class PendingHITLRequest(BaseModel):
    id: UUID
    patient_id: UUID | None
    request_type: str
    reason: str | None
    created_at: datetime


class AuditLogEntry(BaseModel):
    id: UUID
    action: str
    resource_type: str
    details: dict | None
    created_at: datetime


class EmailNotificationStats(BaseModel):
    total_sent: int
    total_failed: int
    total_pending: int


class SystemStatistics(BaseModel):
    total_voice_sessions: int
    total_approval_requests: int
    total_audit_logs: int
    total_reminders: int
    total_appointments_today: int
    total_appointments_this_week: int


class OrganizationDetails(BaseModel):
    id: UUID
    name: str
    slug: str
    phone: str | None
    email: str | None
    address: str | None


class DashboardResponse(BaseModel):
    total_patients: int
    total_doctors: int
    total_appointments: int
    appointments: list[AppointmentItem]
    patients: list[PatientItem]
    voice_sessions: list[VoiceSessionSummary]
    pending_hitl_requests: list[PendingHITLRequest]
    total_users: int | None = None
    audit_logs: list[AuditLogEntry] | None = None
    system_statistics: SystemStatistics | None = None
    organization_details: OrganizationDetails | None = None
    email_notification_statistics: EmailNotificationStats | None = None

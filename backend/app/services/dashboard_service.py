from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import Session, func, select

from app.models.appointment import Appointment
from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.audit_log import AuditLog
from app.models.doctor import Doctor
from app.models.organization import Organization
from app.models.patient import Patient
from app.models.reminder import Reminder, ReminderStatus
from app.models.user import User
from app.models.voice_session import VoiceSession
from app.repositories.approval_request_repo import ApprovalRequestRepository
from app.repositories.audit_log_repo import AuditLogRepository
from app.schemas.dashboard import (
    AppointmentItem,
    AuditLogEntry,
    DashboardResponse,
    EmailNotificationStats,
    OrganizationDetails,
    PatientItem,
    PendingHITLRequest,
    SystemStatistics,
    VoiceSessionSummary,
)


class DashboardService:
    def __init__(self, session: Session):
        self.session = session
        self.approval_repo = ApprovalRequestRepository(session)
        self.audit_log_repo = AuditLogRepository(session)

    def _count(self, model, org_id: UUID) -> int:
        return self.session.exec(
            select(func.count()).select_from(model).where(model.org_id == org_id)
        ).one()

    def _get_appointments(self, org_id: UUID, skip: int = 0, limit: int = 100) -> list[AppointmentItem]:
        rows = self.session.exec(
            select(Appointment)
            .where(Appointment.org_id == org_id)
            .order_by(Appointment.scheduled_at.desc())
            .offset(skip).limit(limit)
        ).all()
        result = []
        for a in rows:
            doctor_name = None
            if a.doctor_id:
                doctor = self.session.get(Doctor, a.doctor_id)
                if doctor:
                    user = self.session.get(User, doctor.user_id)
                    doctor_name = user.full_name if user else None
            patient = self.session.get(Patient, a.patient_id)
            patient_name = f"{patient.first_name} {patient.last_name}" if patient else None
            result.append(AppointmentItem(
                id=a.id,
                patient_id=a.patient_id,
                doctor_id=a.doctor_id,
                patient_name=patient_name,
                doctor_name=doctor_name,
                scheduled_at=a.scheduled_at,
                duration_minutes=a.duration_minutes,
                status=a.status,
                reason=a.reason,
                created_at=a.created_at,
            ))
        return result

    def _get_patients(self, org_id: UUID, skip: int = 0, limit: int = 100) -> list[PatientItem]:
        rows = self.session.exec(
            select(Patient)
            .where(Patient.org_id == org_id)
            .order_by(Patient.created_at.desc())
            .offset(skip).limit(limit)
        ).all()
        return [
            PatientItem(
                id=p.id,
                first_name=p.first_name,
                last_name=p.last_name,
                phone=p.phone,
                email=p.email,
                created_at=p.created_at,
            )
            for p in rows
        ]

    def _get_voice_sessions(self, org_id: UUID, limit: int = 10) -> list[VoiceSessionSummary]:
        sessions = self.session.exec(
            select(VoiceSession)
            .where(VoiceSession.org_id == org_id)
            .order_by(VoiceSession.created_at.desc())
            .limit(limit)
        ).all()
        return [
            VoiceSessionSummary(
                id=s.id,
                patient_id=s.patient_id,
                started_at=s.started_at,
                is_emergency=s.is_emergency,
                escalated_to_human=s.escalated_to_human,
            )
            for s in sessions
        ]

    def _get_pending_hitl(self, org_id: UUID, limit: int = 10) -> list[PendingHITLRequest]:
        requests = self.approval_repo.list_by_org(org_id, status=ApprovalStatus.pending, limit=limit)
        return [
            PendingHITLRequest(
                id=r.id,
                patient_id=r.patient_id,
                request_type=r.request_type.value,
                reason=r.reason,
                created_at=r.created_at,
            )
            for r in requests
        ]

    def _get_audit_logs(self, org_id: UUID, limit: int = 20) -> list[AuditLogEntry]:
        logs = self.audit_log_repo.list_by_org(org_id, limit=limit)
        return [
            AuditLogEntry(
                id=log.id,
                action=log.action,
                resource_type=log.resource_type,
                details=log.details,
                created_at=log.created_at,
            )
            for log in logs
        ]

    def _get_email_stats(self, org_id: UUID) -> EmailNotificationStats:
        sent = self.session.exec(
            select(func.count()).select_from(Reminder)
            .where(Reminder.org_id == org_id, Reminder.status == ReminderStatus.sent)
        ).one()
        failed = self.session.exec(
            select(func.count()).select_from(Reminder)
            .where(Reminder.org_id == org_id, Reminder.status == ReminderStatus.failed)
        ).one()
        pending = self.session.exec(
            select(func.count()).select_from(Reminder)
            .where(Reminder.org_id == org_id, Reminder.status == ReminderStatus.pending)
        ).one()
        return EmailNotificationStats(
            total_sent=sent,
            total_failed=failed,
            total_pending=pending,
        )

    def _get_system_stats(self, org_id: UUID) -> SystemStatistics:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        return SystemStatistics(
            total_voice_sessions=self._count(VoiceSession, org_id),
            total_approval_requests=self._count(ApprovalRequest, org_id),
            total_audit_logs=self._count(AuditLog, org_id),
            total_reminders=self._count(Reminder, org_id),
            total_appointments_today=self.session.exec(
                select(func.count()).select_from(Appointment)
                .where(Appointment.org_id == org_id, Appointment.scheduled_at >= today_start)
            ).one(),
            total_appointments_this_week=self.session.exec(
                select(func.count()).select_from(Appointment)
                .where(Appointment.org_id == org_id, Appointment.scheduled_at >= week_start)
            ).one(),
        )

    def get_dashboard(self, org_id: UUID, role: str) -> DashboardResponse:
        is_admin = role == "admin"

        response = DashboardResponse(
            total_patients=self._count(Patient, org_id),
            total_doctors=self._count(Doctor, org_id),
            total_appointments=self._count(Appointment, org_id),
            appointments=self._get_appointments(org_id),
            patients=self._get_patients(org_id),
            voice_sessions=self._get_voice_sessions(org_id),
            pending_hitl_requests=self._get_pending_hitl(org_id),
        )

        if is_admin:
            org = self.session.get(Organization, org_id)
            response.total_users = self._count(User, org_id)
            response.audit_logs = self._get_audit_logs(org_id)
            response.system_statistics = self._get_system_stats(org_id)
            response.organization_details = OrganizationDetails(
                id=org.id,
                name=org.name,
                slug=org.slug,
                phone=org.phone,
                email=org.email,
                address=org.address,
            ) if org else None
            response.email_notification_statistics = self._get_email_stats(org_id)

        return response

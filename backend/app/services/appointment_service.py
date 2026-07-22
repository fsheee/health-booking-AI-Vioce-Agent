from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import Session

from app.models.appointment import Appointment, AppointmentStatus
from app.models.audit_log import AuditLog
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User
from app.repositories.appointment_repo import AppointmentRepository
from app.repositories.doctor_repo import DoctorRepository
from app.schemas.appointment import AppointmentCreate, AppointmentDetailResponse, AppointmentUpdate

SLOT_DURATION = 30
BUSINESS_HOURS = range(9, 17)  # 9 AM to 5 PM


class AppointmentService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = AppointmentRepository(session)
        self.doctor_repo = DoctorRepository(session)

    def create_appointment(self, org_id: UUID, data: AppointmentCreate) -> Appointment:
        appointment = Appointment(org_id=org_id, **data.model_dump())
        result = self.repo.create(appointment)

        self.session.add(AuditLog(
            org_id=org_id,
            action="appointment_created",
            resource_type="appointment",
            resource_id=result.id,
            details={
                "patient_id": str(result.patient_id),
                "doctor_id": str(result.doctor_id),
                "scheduled_at": result.scheduled_at.isoformat(),
            },
        ))
        self.session.commit()

        return result

    def get_appointment(self, appointment_id: UUID, org_id: UUID) -> Appointment | None:
        return self.repo.get_by_id(appointment_id, org_id)

    def list_appointments(self, org_id: UUID, skip: int = 0, limit: int = 100) -> list[Appointment]:
        return self.repo.list_by_org(org_id, skip, limit)

    def list_by_patient(self, patient_id: UUID, org_id: UUID) -> list[Appointment]:
        return self.repo.list_by_patient(patient_id, org_id)

    def list_by_patient_with_details(self, patient_id: UUID, org_id: UUID) -> list[AppointmentDetailResponse]:
        appointments = self.repo.list_by_patient(patient_id, org_id)
        return [self._enrich_appointment(a, org_id) for a in appointments]

    def list_all_with_details(self, org_id: UUID, skip: int = 0, limit: int = 100) -> list[AppointmentDetailResponse]:
        appointments = self.repo.list_by_org(org_id, skip, limit)
        return [self._enrich_appointment(a, org_id) for a in appointments]

    def _enrich_appointment(self, appointment: Appointment, org_id: UUID) -> AppointmentDetailResponse:
        doctor = self.session.get(Doctor, appointment.doctor_id)
        doctor_name = None
        specialization = None
        if doctor:
            doctor_user = self.session.get(User, doctor.user_id)
            doctor_name = doctor_user.full_name if doctor_user else None
            specialization = doctor.specialization

        patient = self.session.get(Patient, appointment.patient_id)
        patient_name = f"{patient.first_name} {patient.last_name}" if patient else None

        return AppointmentDetailResponse(
            id=appointment.id,
            org_id=appointment.org_id,
            patient_id=appointment.patient_id,
            doctor_id=appointment.doctor_id,
            scheduled_at=appointment.scheduled_at,
            duration_minutes=appointment.duration_minutes,
            status=appointment.status,
            reason=appointment.reason,
            notes=appointment.notes,
            created_at=appointment.created_at,
            updated_at=appointment.updated_at,
            doctor_name=doctor_name,
            specialization=specialization,
            patient_name=patient_name,
        )

    def list_by_doctor(self, doctor_id: UUID, org_id: UUID) -> list[Appointment]:
        return self.repo.list_by_doctor(doctor_id, org_id)

    def update_appointment(self, appointment_id: UUID, org_id: UUID, data: AppointmentUpdate) -> Appointment | None:
        appointment = self.repo.get_by_id(appointment_id, org_id)
        if not appointment:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(appointment, key, value)
        return self.repo.update(appointment)

    def reschedule_appointment(
        self, appointment_id: UUID, org_id: UUID, new_scheduled_at: datetime, reason: str | None = None
    ) -> Appointment | None:
        appointment = self.repo.get_by_id(appointment_id, org_id)
        if not appointment:
            return None
        old_scheduled_at = appointment.scheduled_at
        appointment.scheduled_at = new_scheduled_at
        if reason:
            appointment.reason = reason
        result = self.repo.update(appointment)

        self.session.add(AuditLog(
            org_id=org_id,
            action="appointment_rescheduled",
            resource_type="appointment",
            resource_id=appointment_id,
            details={
                "old_scheduled_at": old_scheduled_at.isoformat(),
                "new_scheduled_at": new_scheduled_at.isoformat(),
            },
        ))
        self.session.commit()

        return result

    def cancel_appointment(self, appointment_id: UUID, org_id: UUID) -> Appointment | None:
        appointment = self.repo.get_by_id(appointment_id, org_id)
        if not appointment:
            return None
        appointment.status = AppointmentStatus.cancelled
        result = self.repo.update(appointment)

        self.session.add(AuditLog(
            org_id=org_id,
            action="appointment_cancelled",
            resource_type="appointment",
            resource_id=appointment_id,
            details={"status": AppointmentStatus.cancelled.value},
        ))
        self.session.commit()

        return result

    def get_doctor_availability(self, doctor_id: UUID, org_id: UUID, date_str: str | None = None) -> list[dict]:
        doctor = self.doctor_repo.get_by_id(doctor_id, org_id)
        if not doctor:
            return []

        if date_str:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            date = datetime.now(timezone.utc).date()

        day_start = datetime(date.year, date.month, date.day, tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        booked = self.repo.get_doctor_slots(doctor_id, org_id, day_start, day_end)
        booked_times = {
            a.scheduled_at.strftime("%H:%M")
            for a in booked
            if a.status not in (AppointmentStatus.cancelled,)
        }

        slots = []
        for hour in BUSINESS_HOURS:
            for minute in (0, 30):
                t = f"{hour:02d}:{minute:02d}"
                if t not in booked_times:
                    slots.append(t)

        return [{"date": date_str or date.isoformat(), "slots": slots}]

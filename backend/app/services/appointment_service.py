from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import Session

from app.models.appointment import Appointment, AppointmentStatus
from app.repositories.appointment_repo import AppointmentRepository
from app.repositories.doctor_repo import DoctorRepository
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate

SLOT_DURATION = 30
BUSINESS_HOURS = range(9, 17)  # 9 AM to 5 PM


class AppointmentService:
    def __init__(self, session: Session):
        self.repo = AppointmentRepository(session)
        self.doctor_repo = DoctorRepository(session)

    def create_appointment(self, org_id: UUID, data: AppointmentCreate) -> Appointment:
        appointment = Appointment(org_id=org_id, **data.model_dump())
        return self.repo.create(appointment)

    def get_appointment(self, appointment_id: UUID, org_id: UUID) -> Appointment | None:
        return self.repo.get_by_id(appointment_id, org_id)

    def list_appointments(self, org_id: UUID, skip: int = 0, limit: int = 100) -> list[Appointment]:
        return self.repo.list_by_org(org_id, skip, limit)

    def list_by_patient(self, patient_id: UUID, org_id: UUID) -> list[Appointment]:
        return self.repo.list_by_patient(patient_id, org_id)

    def list_by_doctor(self, doctor_id: UUID, org_id: UUID) -> list[Appointment]:
        return self.repo.list_by_doctor(doctor_id, org_id)

    def update_appointment(self, appointment_id: UUID, org_id: UUID, data: AppointmentUpdate) -> Appointment | None:
        appointment = self.repo.get_by_id(appointment_id, org_id)
        if not appointment:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(appointment, key, value)
        return self.repo.update(appointment)

    def cancel_appointment(self, appointment_id: UUID, org_id: UUID) -> Appointment | None:
        appointment = self.repo.get_by_id(appointment_id, org_id)
        if not appointment:
            return None
        appointment.status = AppointmentStatus.cancelled
        return self.repo.update(appointment)

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

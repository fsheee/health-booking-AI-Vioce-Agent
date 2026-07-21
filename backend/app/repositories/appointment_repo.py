from datetime import datetime
from uuid import UUID

from sqlmodel import Session, not_, select

from app.models.appointment import Appointment, AppointmentStatus


class AppointmentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, appointment: Appointment) -> Appointment:
        self.session.add(appointment)
        self.session.commit()
        self.session.refresh(appointment)
        return appointment

    def get_by_id(self, appointment_id: UUID, org_id: UUID) -> Appointment | None:
        return self.session.exec(
            select(Appointment).where(Appointment.id == appointment_id, Appointment.org_id == org_id)
        ).first()

    def list_by_org(self, org_id: UUID, skip: int = 0, limit: int = 100) -> list[Appointment]:
        return self.session.exec(
            select(Appointment).where(Appointment.org_id == org_id).offset(skip).limit(limit)
        ).all()

    def list_by_patient(self, patient_id: UUID, org_id: UUID) -> list[Appointment]:
        return self.session.exec(
            select(Appointment).where(Appointment.patient_id == patient_id, Appointment.org_id == org_id)
        ).all()

    def list_by_doctor(self, doctor_id: UUID, org_id: UUID) -> list[Appointment]:
        return self.session.exec(
            select(Appointment).where(Appointment.doctor_id == doctor_id, Appointment.org_id == org_id)
        ).all()

    def get_doctor_slots(
        self, doctor_id: UUID, org_id: UUID, date_from: datetime, date_to: datetime
    ) -> list[Appointment]:
        return self.session.exec(
            select(Appointment).where(
                Appointment.doctor_id == doctor_id,
                Appointment.org_id == org_id,
                Appointment.scheduled_at >= date_from,
                Appointment.scheduled_at <= date_to,
                not_(Appointment.status.in_([AppointmentStatus.cancelled])),
            )
        ).all()

    def update(self, appointment: Appointment) -> Appointment:
        self.session.add(appointment)
        self.session.commit()
        self.session.refresh(appointment)
        return appointment

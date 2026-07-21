from uuid import UUID

from sqlmodel import Session, select

from app.models.doctor import Doctor
from app.models.user import User


class DoctorRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, doctor: Doctor) -> Doctor:
        self.session.add(doctor)
        self.session.commit()
        self.session.refresh(doctor)
        return doctor

    def get_by_id(self, doctor_id: UUID, org_id: UUID) -> Doctor | None:
        return self.session.exec(
            select(Doctor).where(Doctor.id == doctor_id, Doctor.org_id == org_id)
        ).first()

    def list_by_org(self, org_id: UUID) -> list[Doctor]:
        return self.session.exec(
            select(Doctor).where(Doctor.org_id == org_id)
        ).all()

    def get_available(self, org_id: UUID) -> list[Doctor]:
        return self.session.exec(
            select(Doctor).where(Doctor.org_id == org_id, Doctor.is_available)
        ).all()

    def get_by_id_with_user(self, doctor_id: UUID, org_id: UUID) -> tuple[Doctor, User | None] | None:
        return self.session.exec(
            select(Doctor, User)
            .outerjoin(User, Doctor.user_id == User.id)
            .where(Doctor.id == doctor_id, Doctor.org_id == org_id)
        ).first()

    def list_by_org_with_user(self, org_id: UUID) -> list[tuple[Doctor, User | None]]:
        return self.session.exec(
            select(Doctor, User)
            .outerjoin(User, Doctor.user_id == User.id)
            .where(Doctor.org_id == org_id)
        ).all()

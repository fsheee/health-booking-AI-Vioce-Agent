from uuid import UUID

from sqlmodel import Session

from app.models.doctor import Doctor
from app.models.user import User
from app.repositories.doctor_repo import DoctorRepository
from app.schemas.doctor import DoctorCreate, DoctorResponse, DoctorUpdate


def _to_response(doctor: Doctor, user: User | None) -> DoctorResponse:
    return DoctorResponse(
        id=doctor.id,
        user_id=doctor.user_id,
        org_id=doctor.org_id,
        full_name=user.full_name if user else None,
        email=user.email if user else None,
        phone=user.phone if user else None,
        specialization=doctor.specialization,
        license_number=doctor.license_number,
        is_available=doctor.is_available,
        created_at=doctor.created_at,
        updated_at=doctor.updated_at,
    )


class DoctorService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = DoctorRepository(session)

    def create_doctor(self, org_id: UUID, data: DoctorCreate) -> DoctorResponse:
        doctor = Doctor(org_id=org_id, **data.model_dump())
        doctor = self.repo.create(doctor)
        user = self.session.get(User, doctor.user_id)
        return _to_response(doctor, user)

    def get_doctor(self, doctor_id: UUID, org_id: UUID) -> DoctorResponse | None:
        row = self.repo.get_by_id_with_user(doctor_id, org_id)
        if not row:
            return None
        return _to_response(*row)

    def list_doctors(self, org_id: UUID) -> list[DoctorResponse]:
        return [_to_response(doctor, user) for doctor, user in self.repo.list_by_org_with_user(org_id)]

    def update_doctor(self, doctor_id: UUID, org_id: UUID, data: DoctorUpdate) -> DoctorResponse | None:
        doctor = self.repo.get_by_id(doctor_id, org_id)
        if not doctor:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(doctor, field, value)
        self.session.add(doctor)
        self.session.commit()
        self.session.refresh(doctor)
        user = self.session.get(User, doctor.user_id)
        return _to_response(doctor, user)

    def get_available_doctors(self, org_id: UUID) -> list[Doctor]:
        return self.repo.get_available(org_id)

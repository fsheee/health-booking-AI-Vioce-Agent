from uuid import UUID

from sqlmodel import Session, select

from app.models.patient import Patient


class PatientRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, patient: Patient) -> Patient:
        self.session.add(patient)
        self.session.commit()
        self.session.refresh(patient)
        return patient

    def get_by_id(self, patient_id: UUID, org_id: UUID) -> Patient | None:
        return self.session.exec(
            select(Patient).where(Patient.id == patient_id, Patient.org_id == org_id)
        ).first()

    def get_by_user_id(self, user_id: UUID | str, org_id: UUID) -> Patient | None:
        return self.session.exec(
            select(Patient).where(Patient.user_id == user_id, Patient.org_id == org_id)
        ).first()

    def list_by_org(self, org_id: UUID, skip: int = 0, limit: int = 100) -> list[Patient]:
        return self.session.exec(
            select(Patient).where(Patient.org_id == org_id).offset(skip).limit(limit)
        ).all()

    def search(self, org_id: UUID, query: str) -> list[Patient]:
        like = f"%{query}%"
        return self.session.exec(
            select(Patient).where(
                Patient.org_id == org_id,
                Patient.first_name.ilike(like) | Patient.last_name.ilike(like)
                | Patient.phone.ilike(like) | Patient.email.ilike(like),
            )
        ).all()

    def update(self, patient: Patient) -> Patient:
        self.session.add(patient)
        self.session.commit()
        self.session.refresh(patient)
        return patient

    def delete(self, patient: Patient) -> None:
        self.session.delete(patient)
        self.session.commit()

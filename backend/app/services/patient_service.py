from uuid import UUID

from sqlmodel import Session

from app.models.patient import Patient
from app.repositories.patient_repo import PatientRepository
from app.schemas.patient import PatientCreate, PatientUpdate


class PatientService:
    def __init__(self, session: Session):
        self.repo = PatientRepository(session)

    def create_patient(self, org_id: UUID, data: PatientCreate) -> Patient:
        patient = Patient(org_id=org_id, **data.model_dump())
        return self.repo.create(patient)

    def get_patient(self, patient_id: UUID, org_id: UUID) -> Patient | None:
        return self.repo.get_by_id(patient_id, org_id)

    def get_patient_by_user_id(self, user_id: UUID | str, org_id: UUID) -> Patient | None:
        return self.repo.get_by_user_id(user_id, org_id)

    def list_patients(self, org_id: UUID, skip: int = 0, limit: int = 100) -> list[Patient]:
        return self.repo.list_by_org(org_id, skip, limit)

    def search_patients(self, org_id: UUID, query: str) -> list[Patient]:
        return self.repo.search(org_id, query)

    def update_patient(self, patient_id: UUID, org_id: UUID, data: PatientUpdate) -> Patient | None:
        patient = self.repo.get_by_id(patient_id, org_id)
        if not patient:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(patient, key, value)
        return self.repo.update(patient)

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.dependencies import get_current_user, get_session, require_any_role
from app.models.user import UserRole
from app.repositories.patient_repo import PatientRepository
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate
from app.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=list[PatientResponse])
def list_patients(
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    session: Session = Depends(get_session),
    payload: dict = Depends(require_any_role(UserRole.admin, UserRole.doctor, UserRole.front_desk)),
):
    service = PatientService(session)
    org_id = payload.get("org_id")
    if search:
        patients = service.search_patients(org_id, search)
    else:
        patients = service.list_patients(org_id, skip, limit)
    return patients


@router.post("", response_model=PatientResponse, status_code=201)
def create_patient(
    data: PatientCreate,
    session: Session = Depends(get_session),
    payload: dict = Depends(require_any_role(UserRole.admin, UserRole.front_desk)),
):
    service = PatientService(session)
    return service.create_patient(payload.get("org_id"), data)


@router.get("/me", response_model=PatientResponse)
def get_my_patient_profile(
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user),
):
    org_id = payload["org_id"]
    repo = PatientRepository(session)
    patient = repo.get_by_user_id(payload["sub"], org_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found. Please contact front desk.")
    return patient


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: UUID,
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user),
):
    service = PatientService(session)
    patient = service.get_patient(patient_id, payload.get("org_id"))
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: UUID,
    data: PatientUpdate,
    session: Session = Depends(get_session),
    payload: dict = Depends(require_any_role(UserRole.admin, UserRole.front_desk)),
):
    service = PatientService(session)
    patient = service.update_patient(patient_id, payload.get("org_id"), data)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

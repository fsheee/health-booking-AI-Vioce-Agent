from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.dependencies import get_current_user, get_session, require_any_role
from app.models.user import UserRole
from app.schemas.doctor import DoctorCreate, DoctorResponse, DoctorUpdate
from app.services.appointment_service import AppointmentService
from app.services.doctor_service import DoctorService

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.get("", response_model=list[DoctorResponse])
def list_doctors(
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user),
):
    service = DoctorService(session)
    return service.list_doctors(payload.get("org_id"))


@router.post("", response_model=DoctorResponse, status_code=201)
def create_doctor(
    data: DoctorCreate,
    session: Session = Depends(get_session),
    payload: dict = Depends(require_any_role(UserRole.admin, UserRole.front_desk)),
):
    service = DoctorService(session)
    return service.create_doctor(payload.get("org_id"), data)


@router.get("/{doctor_id}", response_model=DoctorResponse)
def get_doctor(
    doctor_id: UUID,
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user),
):
    service = DoctorService(session)
    doctor = service.get_doctor(doctor_id, payload.get("org_id"))
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@router.patch("/{doctor_id}", response_model=DoctorResponse)
def update_doctor(
    doctor_id: UUID,
    data: DoctorUpdate,
    session: Session = Depends(get_session),
    payload: dict = Depends(require_any_role(UserRole.admin, UserRole.front_desk)),
):
    service = DoctorService(session)
    doctor = service.update_doctor(doctor_id, payload.get("org_id"), data)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@router.get("/{doctor_id}/availability")
def get_doctor_availability(
    doctor_id: UUID,
    date: str | None = None,
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user),
):
    service = AppointmentService(session)
    return service.get_doctor_availability(doctor_id, payload.get("org_id"), date)

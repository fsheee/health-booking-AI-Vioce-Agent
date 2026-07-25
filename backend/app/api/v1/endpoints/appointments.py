from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlmodel import Session

from app.core.dependencies import get_current_user, get_session, require_any_role
from app.models.user import UserRole
from app.repositories.patient_repo import PatientRepository
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentDetailResponse,
    AppointmentReschedule,
    AppointmentResponse,
    AppointmentUpdate,
)
from app.schemas.approval import ApprovalRequestCreate
from app.services.appointment_service import AppointmentService
from app.services.approval_service import ApprovalService
from app.services.email_service import (
    send_appointment_cancellation,
    send_appointment_rescheduled,
)
from app.services.risk_engine import assess_cancellation

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get("", response_model=list[AppointmentDetailResponse])
def list_appointments(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    payload: dict = Depends(require_any_role(UserRole.admin, UserRole.doctor, UserRole.front_desk)),
):
    service = AppointmentService(session)
    return service.list_all_with_details(payload.get("org_id"), skip, limit)


@router.get("/my", response_model=list[AppointmentDetailResponse])
def list_my_appointments(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user),
):
    org_id = payload["org_id"]
    service = AppointmentService(session)
    patient_repo = PatientRepository(session)
    patient = patient_repo.get_by_user_id(payload["sub"], org_id)
    if not patient:
        return []
    return service.list_by_patient_with_details(patient.id, org_id)


@router.post("", response_model=AppointmentResponse, status_code=201)
def create_appointment(
    data: AppointmentCreate,
    session: Session = Depends(get_session),
    payload: dict = Depends(require_any_role(UserRole.admin, UserRole.front_desk)),
):
    service = AppointmentService(session)
    return service.create_appointment(payload.get("org_id"), data)


@router.get("/{appointment_id}", response_model=AppointmentDetailResponse)
def get_appointment(
    appointment_id: UUID,
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user),
):
    service = AppointmentService(session)
    appointment = service.get_appointment(appointment_id, payload.get("org_id"))
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return service._enrich_appointment(appointment, payload.get("org_id"))


@router.put("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: UUID,
    data: AppointmentUpdate,
    session: Session = Depends(get_session),
    payload: dict = Depends(require_any_role(UserRole.admin, UserRole.front_desk)),
):
    service = AppointmentService(session)
    appointment = service.update_appointment(appointment_id, payload.get("org_id"), data)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.put("/{appointment_id}/reschedule", response_model=AppointmentDetailResponse)
def reschedule_appointment(
    appointment_id: UUID,
    data: AppointmentReschedule,
    session: Session = Depends(get_session),
    payload: dict = Depends(require_any_role(UserRole.admin, UserRole.front_desk, UserRole.patient)),
):
    service = AppointmentService(session)
    org_id = payload.get("org_id")
    appointment = service.get_appointment(appointment_id, org_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if payload.get("role") == UserRole.patient.value:
        patient_repo = PatientRepository(session)
        patient = patient_repo.get_by_user_id(payload["sub"], org_id)
        if not patient or appointment.patient_id != patient.id:
            raise HTTPException(status_code=403, detail="You can only reschedule your own appointments")

    old_scheduled_at = appointment.scheduled_at
    result = service.reschedule_appointment(appointment_id, org_id, data.scheduled_at, data.reason)
    if not result:
        raise HTTPException(status_code=404, detail="Appointment not found")

    send_appointment_rescheduled(session, result, org_id, old_scheduled_at=old_scheduled_at,
                                reason=data.reason or "")
    logger.info("Appointment rescheduled — id={id} | old={old} | new={new}",
                id=appointment_id, old=old_scheduled_at.isoformat(), new=data.scheduled_at.isoformat())

    return service._enrich_appointment(result, org_id)


@router.delete("/{appointment_id}")
def cancel_appointment(
    appointment_id: UUID,
    session: Session = Depends(get_session),
    payload: dict = Depends(require_any_role(UserRole.admin, UserRole.front_desk, UserRole.patient)),
):
    service = AppointmentService(session)
    org_id = payload.get("org_id")
    appointment = service.get_appointment(appointment_id, org_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # HITL: cancellations within 24h go to the approval queue instead of
    # executing — except when staff (admin/front_desk) cancels directly,
    # which IS the human decision.
    if payload.get("role") == UserRole.patient.value:
        patient_repo = PatientRepository(session)
        patient = patient_repo.get_by_user_id(payload["sub"], org_id)
        if not patient or appointment.patient_id != patient.id:
            raise HTTPException(status_code=403, detail="You can only cancel your own appointments")
        decision = assess_cancellation(appointment.scheduled_at)
        if decision.requires_approval:
            approval_service = ApprovalService(session)
            request = approval_service.submit(
                org_id,
                payload["sub"],
                ApprovalRequestCreate(
                    patient_id=patient.id,
                    appointment_id=appointment_id,
                    request_type=decision.request_type,
                    reason=decision.reason,
                    ai_summary="Patient asked to cancel an appointment starting within 24 hours",
                    requested_action={
                        "action": "cancel_appointment",
                        "appointment_id": str(appointment_id),
                    },
                ),
            )
            logger.info(
                "Late cancellation routed to HITL queue — appt={id} | approval={aid}",
                id=appointment_id, aid=request.id,
            )
            return {
                "message": (
                    "This appointment starts within 24 hours, so the cancellation "
                    "needs staff review. Our team has been notified."
                ),
                "status": "pending_approval",
                "approval_request_id": str(request.id),
            }

    appointment = service.cancel_appointment(appointment_id, org_id)

    logger.info("Appointment cancelled — id={id}", id=appointment_id)
    send_appointment_cancellation(session, appointment, org_id, reason=appointment.reason or "")

    return {"message": "Appointment cancelled"}

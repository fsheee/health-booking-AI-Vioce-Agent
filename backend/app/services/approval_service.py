"""HITL approval workflow service.

Owns the approval queue lifecycle: submit → pending → approved/rejected.
On approval, executes the deferred action stored on the request (currently
appointment booking); every transition is audit-logged and emailed.
"""

from datetime import datetime, timezone
from uuid import UUID

from loguru import logger
from sqlmodel import Session

from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.audit_log import AuditLog
from app.repositories.approval_request_repo import ApprovalRequestRepository
from app.schemas.approval import ApprovalRequestCreate
from app.services.email_service import (
    send_approval_decision,
    send_approval_requested,
)


class ApprovalService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = ApprovalRequestRepository(session)

    def _audit(
        self,
        org_id: UUID,
        user_id: UUID | None,
        action: str,
        request: ApprovalRequest,
        details: dict | None = None,
    ) -> None:
        log = AuditLog(
            org_id=org_id,
            user_id=user_id,
            action=action,
            resource_type="approval_request",
            resource_id=request.id,
            details={
                "request_type": request.request_type.value,
                "status": request.status.value,
                "reason": request.reason,
                **(details or {}),
            },
        )
        self.session.add(log)
        self.session.commit()

    def submit(
        self, org_id: UUID, submitted_by: UUID | None, data: ApprovalRequestCreate
    ) -> ApprovalRequest:
        request = ApprovalRequest(org_id=org_id, **data.model_dump())
        request = self.repo.create(request)
        logger.info(
            "Approval requested — id={id} | type={t} | reason={r}",
            id=request.id, t=request.request_type.value, r=request.reason,
        )
        self._audit(org_id, submitted_by, "approval_requested", request,
                    {"ai_summary": request.ai_summary, "ai_confidence": request.ai_confidence})
        send_approval_requested(self.session, request)
        return request

    def get(self, request_id: UUID, org_id: UUID) -> ApprovalRequest | None:
        return self.repo.get_by_id(request_id, org_id)

    def list(
        self, org_id: UUID, status: ApprovalStatus | None = None, skip: int = 0, limit: int = 100
    ) -> list[ApprovalRequest]:
        return self.repo.list_by_org(org_id, status=status, skip=skip, limit=limit)

    def approve(
        self, request_id: UUID, org_id: UUID, reviewer_id: UUID, comment: str | None = None
    ) -> ApprovalRequest | None:
        request = self.repo.get_by_id(request_id, org_id)
        if not request:
            return None
        if request.status != ApprovalStatus.pending:
            return request  # idempotent: decisions are final

        outcome = self._execute_action(request)

        request.status = ApprovalStatus.approved
        request.approved_by = reviewer_id
        request.approved_at = datetime.now(timezone.utc)
        request.reviewer_comment = comment
        request = self.repo.update(request)

        logger.info("Approval granted — id={id} | by={u} | outcome={o}",
                    id=request.id, u=reviewer_id, o=outcome)
        self._audit(org_id, reviewer_id, "approval_granted", request,
                    {"comment": comment, "outcome": outcome})
        send_approval_decision(self.session, request, approved=True)
        return request

    def reject(
        self, request_id: UUID, org_id: UUID, reviewer_id: UUID, comment: str | None = None
    ) -> ApprovalRequest | None:
        request = self.repo.get_by_id(request_id, org_id)
        if not request:
            return None
        if request.status != ApprovalStatus.pending:
            return request

        request.status = ApprovalStatus.rejected
        request.approved_by = reviewer_id
        request.approved_at = datetime.now(timezone.utc)
        request.reviewer_comment = comment
        request = self.repo.update(request)

        logger.info("Approval rejected — id={id} | by={u}", id=request.id, u=reviewer_id)
        self._audit(org_id, reviewer_id, "approval_rejected", request, {"comment": comment})
        send_approval_decision(self.session, request, approved=False)
        return request

    def _execute_action(self, request: ApprovalRequest) -> dict:
        """Execute the deferred action stored on an approved request.

        Best-effort: a failed action is reported in the outcome (and audit log)
        but does not block the approval decision itself.
        """
        action = request.requested_action or {}
        action_name = action.get("action")
        if not action_name:
            return {"executed": False, "note": "no deferred action attached"}

        try:
            if action_name == "book_appointment":
                from app.schemas.appointment import AppointmentCreate
                from app.services.appointment_service import AppointmentService

                service = AppointmentService(self.session)
                created = service.create_appointment(
                    request.org_id,
                    AppointmentCreate(
                        patient_id=action["patient_id"],
                        doctor_id=action["doctor_id"],
                        scheduled_at=action["scheduled_at"],
                        duration_minutes=action.get("duration_minutes", 30),
                        reason=action.get("reason"),
                    ),
                )
                request.appointment_id = created.id
                from app.services.email_service import send_appointment_confirmation
                send_appointment_confirmation(self.session, created, request.org_id)
                return {"executed": True, "appointment_id": str(created.id)}

            if action_name == "cancel_appointment":
                from app.services.appointment_service import AppointmentService
                from app.services.email_service import send_appointment_cancellation

                service = AppointmentService(self.session)
                appointment = service.cancel_appointment(UUID(action["appointment_id"]), request.org_id)
                if not appointment:
                    return {"executed": False, "note": "appointment not found"}
                send_appointment_cancellation(self.session, appointment, request.org_id)
                return {"executed": True, "appointment_id": str(appointment.id)}

            return {"executed": False, "note": f"unknown action '{action_name}'"}
        except Exception as e:
            logger.error("Deferred action failed — request={id} | action={a} | error={e}",
                         id=request.id, a=action_name, e=str(e))
            return {"executed": False, "error": str(e)}

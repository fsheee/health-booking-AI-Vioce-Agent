from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.core.dependencies import get_session, require_any_role
from app.models.approval_request import ApprovalStatus
from app.models.user import UserRole
from app.schemas.approval import ApprovalDecision, ApprovalRequestResponse
from app.services.approval_service import ApprovalService

router = APIRouter(prefix="/approvals", tags=["approvals"])

# Staff who can review the HITL queue. Admin passes require_any_role implicitly.
_reviewer_dep = require_any_role(UserRole.front_desk, UserRole.doctor)


@router.get("", response_model=list[ApprovalRequestResponse])
def list_approvals(
    status: ApprovalStatus | None = Query(default=None),
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    payload: dict = Depends(_reviewer_dep),
):
    service = ApprovalService(session)
    return service.list(payload["org_id"], status=status, skip=skip, limit=limit)


@router.get("/pending", response_model=list[ApprovalRequestResponse])
def get_pending_approvals(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    payload: dict = Depends(_reviewer_dep),
):
    service = ApprovalService(session)
    return service.list(payload["org_id"], status=ApprovalStatus.pending, skip=skip, limit=limit)


@router.get("/{request_id}", response_model=ApprovalRequestResponse)
def get_approval(
    request_id: UUID,
    session: Session = Depends(get_session),
    payload: dict = Depends(_reviewer_dep),
):
    service = ApprovalService(session)
    request = service.get(request_id, payload["org_id"])
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return request


@router.post("/{request_id}/approve", response_model=ApprovalRequestResponse)
def approve_request(
    request_id: UUID,
    data: ApprovalDecision,
    session: Session = Depends(get_session),
    payload: dict = Depends(_reviewer_dep),
):
    service = ApprovalService(session)
    request = service.approve(request_id, payload["org_id"], payload["sub"], comment=data.comment)
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return request


@router.post("/{request_id}/reject", response_model=ApprovalRequestResponse)
def reject_request(
    request_id: UUID,
    data: ApprovalDecision,
    session: Session = Depends(get_session),
    payload: dict = Depends(_reviewer_dep),
):
    service = ApprovalService(session)
    request = service.reject(request_id, payload["org_id"], payload["sub"], comment=data.comment)
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return request

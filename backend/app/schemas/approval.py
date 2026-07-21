from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator

from app.models.approval_request import ApprovalRequestType, ApprovalStatus
from app.schemas.tools import coerce_uuid


class ApprovalRequestCreate(BaseModel):
    patient_id: Annotated[UUID | None, BeforeValidator(coerce_uuid)] = None
    appointment_id: Annotated[UUID | None, BeforeValidator(coerce_uuid)] = None
    request_type: ApprovalRequestType = ApprovalRequestType.other
    reason: str | None = None
    ai_summary: str | None = None
    ai_confidence: float | None = None
    requested_action: dict | None = None


class ApprovalDecision(BaseModel):
    comment: str | None = None


class ApprovalRequestResponse(BaseModel):
    id: UUID
    org_id: UUID
    patient_id: UUID | None = None
    appointment_id: UUID | None = None
    request_type: ApprovalRequestType
    reason: str | None = None
    ai_summary: str | None = None
    ai_confidence: float | None = None
    requested_action: dict | None = None
    status: ApprovalStatus
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    reviewer_comment: str | None = None
    created_at: datetime
    updated_at: datetime

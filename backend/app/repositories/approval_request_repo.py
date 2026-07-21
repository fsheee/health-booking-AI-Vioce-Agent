from uuid import UUID

from sqlmodel import Session, col, select

from app.models.approval_request import ApprovalRequest, ApprovalStatus


class ApprovalRequestRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, request: ApprovalRequest) -> ApprovalRequest:
        self.session.add(request)
        self.session.commit()
        self.session.refresh(request)
        return request

    def get_by_id(self, request_id: UUID, org_id: UUID) -> ApprovalRequest | None:
        return self.session.exec(
            select(ApprovalRequest).where(
                ApprovalRequest.id == request_id, ApprovalRequest.org_id == org_id
            )
        ).first()

    def list_by_org(
        self,
        org_id: UUID,
        status: ApprovalStatus | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ApprovalRequest]:
        query = select(ApprovalRequest).where(ApprovalRequest.org_id == org_id)
        if status:
            query = query.where(ApprovalRequest.status == status)
        query = query.order_by(col(ApprovalRequest.created_at).desc()).offset(skip).limit(limit)
        return self.session.exec(query).all()

    def list_pending(self, org_id: UUID, skip: int = 0, limit: int = 100) -> list[ApprovalRequest]:
        return self.list_by_org(org_id, status=ApprovalStatus.pending, skip=skip, limit=limit)

    def update(self, request: ApprovalRequest) -> ApprovalRequest:
        self.session.add(request)
        self.session.commit()
        self.session.refresh(request)
        return request

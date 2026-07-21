from uuid import UUID

from sqlmodel import Session, select

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, log: AuditLog) -> AuditLog:
        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log

    def list_by_org(self, org_id: UUID, skip: int = 0, limit: int = 100) -> list[AuditLog]:
        return self.session.exec(
            select(AuditLog).where(AuditLog.org_id == org_id)
            .order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        ).all()

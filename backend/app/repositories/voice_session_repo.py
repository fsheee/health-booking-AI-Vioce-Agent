from uuid import UUID

from sqlmodel import Session, select

from app.models.voice_session import VoiceSession


class VoiceSessionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, session_obj: VoiceSession) -> VoiceSession:
        self.session.add(session_obj)
        self.session.commit()
        self.session.refresh(session_obj)
        return session_obj

    def get_by_id(self, session_id: UUID, org_id: UUID) -> VoiceSession | None:
        return self.session.exec(
            select(VoiceSession).where(VoiceSession.id == session_id, VoiceSession.org_id == org_id)
        ).first()

    def list_by_org(self, org_id: UUID, skip: int = 0, limit: int = 100) -> list[VoiceSession]:
        return self.session.exec(
            select(VoiceSession).where(VoiceSession.org_id == org_id).offset(skip).limit(limit)
        ).all()

    def update(self, session_obj: VoiceSession) -> VoiceSession:
        self.session.add(session_obj)
        self.session.commit()
        self.session.refresh(session_obj)
        return session_obj

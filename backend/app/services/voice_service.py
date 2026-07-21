from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session

from app.models.voice_session import VoiceSession
from app.repositories.voice_session_repo import VoiceSessionRepository


class VoiceService:
    def __init__(self, session: Session):
        self.repo = VoiceSessionRepository(session)

    def start_session(self, org_id: UUID, patient_id: UUID, user_id: UUID | None = None) -> VoiceSession:
        session_obj = VoiceSession(
            org_id=org_id,
            patient_id=patient_id,
            user_id=user_id,
            started_at=datetime.now(timezone.utc),
        )
        return self.repo.create(session_obj)

    def get_session(self, session_id: UUID, org_id: UUID) -> VoiceSession | None:
        return self.repo.get_by_id(session_id, org_id)

    def list_sessions(self, org_id: UUID, skip: int = 0, limit: int = 100) -> list[VoiceSession]:
        return self.repo.list_by_org(org_id, skip, limit)

    def update_session(self, session_obj: VoiceSession) -> VoiceSession:
        return self.repo.update(session_obj)

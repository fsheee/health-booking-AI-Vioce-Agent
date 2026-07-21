from uuid import UUID

from sqlmodel import Session

from app.models.reminder import Reminder
from app.repositories.reminder_repo import ReminderRepository


class ReminderService:
    def __init__(self, session: Session):
        self.repo = ReminderRepository(session)

    def create_reminder(self, reminder: Reminder) -> Reminder:
        return self.repo.create(reminder)

    def get_reminder(self, reminder_id: UUID, org_id: UUID) -> Reminder | None:
        return self.repo.get_by_id(reminder_id, org_id)

    def list_reminders(self, org_id: UUID, skip: int = 0, limit: int = 100) -> list[Reminder]:
        return self.repo.list_by_org(org_id, skip, limit)

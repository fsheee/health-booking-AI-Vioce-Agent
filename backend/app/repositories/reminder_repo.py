from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session, select

from app.models.reminder import Reminder, ReminderStatus


class ReminderRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, reminder: Reminder) -> Reminder:
        self.session.add(reminder)
        self.session.commit()
        self.session.refresh(reminder)
        return reminder

    def get_by_id(self, reminder_id: UUID, org_id: UUID) -> Reminder | None:
        return self.session.exec(
            select(Reminder).where(Reminder.id == reminder_id, Reminder.org_id == org_id)
        ).first()

    def list_by_org(self, org_id: UUID, skip: int = 0, limit: int = 100) -> list[Reminder]:
        return self.session.exec(
            select(Reminder).where(Reminder.org_id == org_id).offset(skip).limit(limit)
        ).all()

    def list_by_appointment(self, appointment_id: UUID, org_id: UUID) -> list[Reminder]:
        return self.session.exec(
            select(Reminder).where(
                Reminder.appointment_id == appointment_id,
                Reminder.org_id == org_id,
            )
        ).all()

    def list_pending(self, org_id: UUID) -> list[Reminder]:
        now = datetime.now(timezone.utc)
        return self.session.exec(
            select(Reminder).where(
                Reminder.org_id == org_id,
                Reminder.status == ReminderStatus.pending,
                Reminder.scheduled_at <= now,
            )
        ).all()

    def update(self, reminder: Reminder) -> Reminder:
        self.session.add(reminder)
        self.session.commit()
        self.session.refresh(reminder)
        return reminder

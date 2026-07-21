import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session

from app.models.organization import Organization
from app.models.reminder import Reminder, ReminderChannel, ReminderStatus, ReminderType
from app.services.reminder_worker import process_pending_reminders
from tests.conftest import engine


@pytest.fixture
def org_id() -> uuid.UUID:
    from sqlmodel import select
    with Session(engine) as session:
        org = session.exec(select(Organization)).first()
        if org:
            return org.id
    o = Organization(name="Test", slug="test")
    with Session(engine) as session:
        session.add(o)
        session.commit()
        session.refresh(o)
        return o.id


def _create_reminder(org_id, status=ReminderStatus.pending, channel=ReminderChannel.email, minutes_ago=5):
    reminder = Reminder(
        org_id=org_id,
        patient_id=uuid.uuid4(),
        type=ReminderType.appointment,
        channel=channel,
        scheduled_at=datetime.now(timezone.utc) - timedelta(minutes=minutes_ago),
        status=status,
        message="Test reminder",
    )
    with Session(engine) as session:
        session.add(reminder)
        session.commit()
        return reminder.id


def test_process_pending_reminders(org_id):
    rid = _create_reminder(org_id)
    process_pending_reminders(engine)

    with Session(engine) as session:
        from sqlmodel import select
        reminder = session.exec(select(Reminder).where(Reminder.id == rid)).first()
        assert reminder is not None
        assert reminder.status == ReminderStatus.sent
        assert reminder.sent_at is not None


def test_pending_only_processed(org_id):
    sent_id = _create_reminder(org_id, status=ReminderStatus.sent)
    pending_id = _create_reminder(org_id, status=ReminderStatus.pending)

    process_pending_reminders(engine)

    with Session(engine) as session:
        from sqlmodel import select
        sent = session.exec(select(Reminder).where(Reminder.id == sent_id)).first()
        assert sent.status == ReminderStatus.sent

        pending = session.exec(select(Reminder).where(Reminder.id == pending_id)).first()
        assert pending.status == ReminderStatus.sent


def test_future_reminders_not_sent(org_id):
    future = Reminder(
        org_id=org_id,
        patient_id=uuid.uuid4(),
        type=ReminderType.appointment,
        channel=ReminderChannel.email,
        scheduled_at=datetime.now(timezone.utc) + timedelta(hours=1),
        status=ReminderStatus.pending,
        message="Future reminder",
    )
    with Session(engine) as session:
        session.add(future)
        session.commit()
        fid = future.id

    process_pending_reminders(engine)

    with Session(engine) as session:
        from sqlmodel import select
        result = session.exec(select(Reminder).where(Reminder.id == fid)).first()
        assert result.status == ReminderStatus.pending


def test_all_channels(org_id):
    channels = [ReminderChannel.email, ReminderChannel.sms, ReminderChannel.voice]
    ids = []
    for ch in channels:
        ids.append(_create_reminder(org_id, channel=ch))

    process_pending_reminders(engine)

    with Session(engine) as session:
        from sqlmodel import select
        for rid in ids:
            r = session.exec(select(Reminder).where(Reminder.id == rid)).first()
            assert r.status == ReminderStatus.sent, f"Channel {r.channel} failed: {r.status}"

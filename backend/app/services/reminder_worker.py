from datetime import datetime, timezone
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from sqlmodel import Session, create_engine, select

from app.core.config import settings
from app.models.appointment import Appointment
from app.models.audit_log import AuditLog
from app.models.reminder import Reminder, ReminderChannel, ReminderStatus
from app.services.email_service import send_appointment_reminder as _send_email_reminder

scheduler = AsyncIOScheduler()


def send_email(reminder: Reminder) -> bool:
    try:
        engine = create_engine(str(settings.database_url))
        with Session(engine) as session:
            appointment = session.get(Appointment, reminder.appointment_id)
            if appointment:
                _send_email_reminder(session, appointment, reminder.org_id, reminder=reminder)
                logger.info("Reminder email sent — reminder={id}", id=reminder.id)
            else:
                logger.warning("Appointment not found for reminder {id}", id=reminder.id)
                return False
        engine.dispose()
        return True
    except Exception as e:
        logger.error("Failed to send reminder email — reminder={id} | error={err}", id=reminder.id, err=str(e))
        return False


def send_sms(reminder: Reminder) -> bool:
    logger.info(f"[SMS] To: patient={reminder.patient_id}, msg={reminder.message}")
    return True


def send_voice(reminder: Reminder) -> bool:
    logger.info(f"[VOICE] To: patient={reminder.patient_id}, msg={reminder.message}")
    return True


CHANNEL_DISPATCH: dict[ReminderChannel, Callable[[Reminder], bool]] = {
    ReminderChannel.email: send_email,
    ReminderChannel.sms: send_sms,
    ReminderChannel.voice: send_voice,
}


def process_pending_reminders(engine=None):
    owns_engine = engine is None
    if owns_engine:
        engine = create_engine(str(settings.database_url))
    with Session(engine) as session:
        now = datetime.now(timezone.utc)
        reminders = session.exec(
            select(Reminder).where(
                Reminder.status == ReminderStatus.pending,
                Reminder.scheduled_at <= now,
            )
        ).all()

        for reminder in reminders:
            dispatch = CHANNEL_DISPATCH.get(reminder.channel)
            if not dispatch:
                logger.warning(f"Unknown channel {reminder.channel} for reminder {reminder.id}")
                reminder.status = ReminderStatus.failed
            else:
                try:
                    success = dispatch(reminder)
                    reminder.status = ReminderStatus.sent if success else ReminderStatus.failed
                    reminder.sent_at = datetime.now(timezone.utc)
                except Exception as e:
                    logger.error(f"Failed to send reminder {reminder.id}: {e}")
                    reminder.status = ReminderStatus.failed

            session.add(reminder)

            if reminder.status == ReminderStatus.sent:
                session.add(AuditLog(
                    org_id=reminder.org_id,
                    action="reminder_sent",
                    resource_type="reminder",
                    resource_id=reminder.id,
                    details={
                        "channel": reminder.channel.value,
                        "type": reminder.type.value,
                        "appointment_id": str(reminder.appointment_id) if reminder.appointment_id else None,
                    },
                ))

            session.commit()

    if owns_engine:
        engine.dispose()


async def start_scheduler():
    scheduler.add_job(
        process_pending_reminders,
        "interval",
        minutes=1,
        id="reminder_worker",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Reminder worker started (polling every 60s)")


async def stop_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("Reminder worker stopped")

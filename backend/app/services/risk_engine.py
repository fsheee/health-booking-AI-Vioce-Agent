"""HITL decision engine — classifies requested actions as auto-execute or
human-approval-required.

Routine scheduling stays fully automated; anything clinically sensitive,
disruptive (late cancellation, double-booking), VIP-flagged, or below the AI
confidence threshold is routed to the approval queue for staff review.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.agent.emergency import check_emergency
from app.models.approval_request import ApprovalRequestType

CONFIDENCE_THRESHOLD = 0.80

# Symptoms that suggest elevated medical risk but are not an immediate hard
# emergency (those are caught by check_emergency() above). These are subtle
# enough that a human should review before booking around them.
# NOTE: Do NOT add trigger words like "emergency", "urgent", "ASAP" here —
# those are handled by the LLM's HITL policy, not keyword-matched.
ELEVATED_RISK_PHRASES = [
    "persistent severe pain",
    "severe dizziness",
    "fainted",
    "numbness",
    "high-risk pregnancy",
    "ongoing bleeding",
]

LATE_CANCELLATION_WINDOW = timedelta(hours=24)


@dataclass
class RiskDecision:
    requires_approval: bool
    request_type: ApprovalRequestType = ApprovalRequestType.other
    reason: str = ""


def assess_transcript(transcript: str) -> RiskDecision:
    """Risk-screen the patient's utterance before any tool runs."""
    if check_emergency(transcript):
        return RiskDecision(
            requires_approval=True,
            request_type=ApprovalRequestType.emergency_escalation,
            reason="Emergency phrase detected in patient message",
        )
    lowered = transcript.lower()
    for phrase in ELEVATED_RISK_PHRASES:
        if phrase in lowered:
            return RiskDecision(
                requires_approval=True,
                request_type=ApprovalRequestType.urgent_symptoms,
                reason=f"Elevated risk mentioned: '{phrase}'",
            )
    return RiskDecision(requires_approval=False)


def assess_booking(
    is_vip: bool = False,
    slot_taken: bool = False,
    manual_doctor_assignment: bool = False,
    ai_confidence: float | None = None,
) -> RiskDecision:
    """Risk-screen a booking/reschedule action right before execution."""
    if slot_taken:
        return RiskDecision(
            requires_approval=True,
            request_type=ApprovalRequestType.double_booking,
            reason="Requested slot conflicts with an existing appointment",
        )
    if is_vip:
        return RiskDecision(
            requires_approval=True,
            request_type=ApprovalRequestType.vip_request,
            reason="VIP patient — bookings require staff confirmation",
        )
    if manual_doctor_assignment:
        return RiskDecision(
            requires_approval=True,
            request_type=ApprovalRequestType.manual_doctor_assignment,
            reason="Manual doctor assignment requested",
        )
    if ai_confidence is not None and ai_confidence < CONFIDENCE_THRESHOLD:
        return RiskDecision(
            requires_approval=True,
            request_type=ApprovalRequestType.low_confidence,
            reason=f"AI confidence {ai_confidence:.0%} below {CONFIDENCE_THRESHOLD:.0%} threshold",
        )
    return RiskDecision(requires_approval=False)


def assess_cancellation(scheduled_at: datetime) -> RiskDecision:
    """Cancellations within 24h of the appointment need staff sign-off."""
    now = datetime.now(timezone.utc)
    if scheduled_at.tzinfo is None:
        scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
    if now <= scheduled_at <= now + LATE_CANCELLATION_WINDOW:
        return RiskDecision(
            requires_approval=True,
            request_type=ApprovalRequestType.late_cancellation,
            reason="Cancellation within 24 hours of the appointment",
        )
    return RiskDecision(requires_approval=False)

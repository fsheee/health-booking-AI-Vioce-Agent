"""Unit tests for the HITL decision engine (app/services/risk_engine.py).

Pure functions — no DB, no fixtures. These pin down the routing rules:
what auto-executes vs. what goes to the staff approval queue.
"""

from datetime import datetime, timedelta, timezone

from app.models.approval_request import ApprovalRequestType
from app.services.risk_engine import (
    CONFIDENCE_THRESHOLD,
    assess_booking,
    assess_cancellation,
    assess_transcript,
)

# ---------------------------------------------------------------------------
# assess_transcript
# ---------------------------------------------------------------------------


class TestAssessTranscript:
    def test_hard_emergency_phrase_escalates_as_emergency(self):
        decision = assess_transcript("I have chest pain right now")
        assert decision.requires_approval is True
        assert decision.request_type == ApprovalRequestType.emergency_escalation

    def test_emergency_word_escalates_as_urgent(self):
        # Regression: "I need an emergency appointment" produced no HITL entry
        # because "emergency" was in no trigger list.
        decision = assess_transcript("I need an emergency appointment")
        assert decision.requires_approval is True
        assert decision.request_type == ApprovalRequestType.urgent_symptoms
        assert "emergency" in decision.reason.lower()

    def test_urgent_symptom_phrase_escalates(self):
        # "chest tightness" is urgent but not in EMERGENCY_PHRASES — it must
        # route to urgent_symptoms, not the hard-emergency short-circuit.
        decision = assess_transcript("I've been having chest tightness at night")
        assert decision.requires_approval is True
        assert decision.request_type == ApprovalRequestType.urgent_symptoms

    def test_matching_is_case_insensitive(self):
        decision = assess_transcript("THIS IS AN EMERGENCY")
        assert decision.requires_approval is True

    def test_routine_booking_request_is_not_flagged(self):
        decision = assess_transcript("book me a dermatologist appointment next week")
        assert decision.requires_approval is False

    def test_empty_transcript_is_not_flagged(self):
        assert assess_transcript("").requires_approval is False


# ---------------------------------------------------------------------------
# assess_booking
# ---------------------------------------------------------------------------


class TestAssessBooking:
    def test_routine_booking_auto_executes(self):
        assert assess_booking().requires_approval is False

    def test_slot_conflict_flags_double_booking(self):
        decision = assess_booking(slot_taken=True)
        assert decision.requires_approval is True
        assert decision.request_type == ApprovalRequestType.double_booking

    def test_vip_patient_requires_approval(self):
        decision = assess_booking(is_vip=True)
        assert decision.requires_approval is True
        assert decision.request_type == ApprovalRequestType.vip_request

    def test_manual_doctor_assignment_requires_approval(self):
        decision = assess_booking(manual_doctor_assignment=True)
        assert decision.requires_approval is True
        assert decision.request_type == ApprovalRequestType.manual_doctor_assignment

    def test_low_confidence_requires_approval(self):
        decision = assess_booking(ai_confidence=0.5)
        assert decision.requires_approval is True
        assert decision.request_type == ApprovalRequestType.low_confidence

    def test_confidence_at_threshold_auto_executes(self):
        assert assess_booking(ai_confidence=CONFIDENCE_THRESHOLD).requires_approval is False

    def test_confidence_just_below_threshold_flags(self):
        assert assess_booking(ai_confidence=CONFIDENCE_THRESHOLD - 0.01).requires_approval is True

    def test_missing_confidence_auto_executes(self):
        # The agent may omit ai_confidence; absence alone must not block booking.
        assert assess_booking(ai_confidence=None).requires_approval is False

    def test_priority_double_booking_beats_vip(self):
        decision = assess_booking(is_vip=True, slot_taken=True, ai_confidence=0.1)
        assert decision.request_type == ApprovalRequestType.double_booking

    def test_priority_vip_beats_manual_and_confidence(self):
        decision = assess_booking(is_vip=True, manual_doctor_assignment=True, ai_confidence=0.1)
        assert decision.request_type == ApprovalRequestType.vip_request

    def test_priority_manual_beats_confidence(self):
        decision = assess_booking(manual_doctor_assignment=True, ai_confidence=0.1)
        assert decision.request_type == ApprovalRequestType.manual_doctor_assignment


# ---------------------------------------------------------------------------
# assess_cancellation
# ---------------------------------------------------------------------------


class TestAssessCancellation:
    def test_cancellation_within_24h_requires_approval(self):
        scheduled = datetime.now(timezone.utc) + timedelta(hours=2)
        decision = assess_cancellation(scheduled)
        assert decision.requires_approval is True
        assert decision.request_type == ApprovalRequestType.late_cancellation

    def test_cancellation_beyond_24h_auto_executes(self):
        scheduled = datetime.now(timezone.utc) + timedelta(hours=25)
        assert assess_cancellation(scheduled).requires_approval is False

    def test_cancelling_past_appointment_auto_executes(self):
        # Nothing to protect — the appointment already started/happened.
        scheduled = datetime.now(timezone.utc) - timedelta(hours=1)
        assert assess_cancellation(scheduled).requires_approval is False

    def test_naive_datetime_treated_as_utc(self):
        # SQLite (tests) returns naive datetimes; Postgres returns aware ones.
        scheduled = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=2)
        assert assess_cancellation(scheduled).requires_approval is True

import base64
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlmodel import Session

from app.agent.agent import process_transcript
from app.agent.emergency import EMERGENCY_RESPONSE, check_emergency
from app.agent.stt import transcribe_audio
from app.agent.tts import text_to_speech
from app.core.dependencies import get_current_user, get_session
from app.models.approval_request import ApprovalRequestType
from app.models.audit_log import AuditLog
from app.repositories.patient_repo import PatientRepository
from app.schemas.approval import ApprovalRequestCreate
from app.schemas.voice import VoiceProcessRequest, VoiceSessionResponse, VoiceSessionStart
from app.services.approval_service import ApprovalService
from app.services.risk_engine import assess_transcript
from app.services.voice_service import VoiceService

router = APIRouter(prefix="/voice", tags=["voice"])


def _tts_base64_or_none(text: str) -> str | None:
    """TTS is best-effort: a missing provider key or provider outage should not
    fail the whole voice interaction — the client still gets the text response."""
    try:
        return base64.b64encode(text_to_speech(text)).decode()
    except Exception as e:
        logger.warning("TTS unavailable, returning text-only response: {err}", err=str(e))
        return None


@router.post("/sessions", response_model=VoiceSessionResponse, status_code=201)
def start_session(
    data: VoiceSessionStart,
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user),
):
    patient_id = data.patient_id
    if not patient_id:
        patient_repo = PatientRepository(session)
        patient = patient_repo.get_by_user_id(payload["sub"], payload["org_id"])
        if not patient:
            raise HTTPException(
                status_code=400,
                detail="Patient record not found for current user",
            )
        patient_id = patient.id

    service = VoiceService(session)
    voice_session = service.start_session(
        org_id=payload.get("org_id"),
        patient_id=patient_id,
        user_id=payload.get("sub"),
    )
    return voice_session


@router.get("/sessions", response_model=list[VoiceSessionResponse])
def list_sessions(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user),
):
    service = VoiceService(session)
    return service.list_sessions(payload.get("org_id"), skip, limit)


@router.get("/sessions/{session_id}", response_model=VoiceSessionResponse)
def get_voice_session(
    session_id: UUID,
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user),
):
    service = VoiceService(session)
    voice_session = service.get_session(session_id, payload.get("org_id"))
    if not voice_session:
        raise HTTPException(status_code=404, detail="Voice session not found")
    return voice_session


@router.post("/process")
async def process_voice(
    data: VoiceProcessRequest,
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user),
):
    org_id = payload["org_id"]
    user_id = payload["sub"]

    voice_service = VoiceService(session)
    vs = voice_service.get_session(data.session_id, org_id)
    if not vs:
        raise HTTPException(status_code=404, detail="Voice session not found")

    try:
        audio_bytes = base64.b64decode(data.audio_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 audio payload")

    try:
        transcript = await transcribe_audio(audio_bytes)
    except Exception as e:
        logger.error("STT failed for session {sid}: {err}", sid=data.session_id, err=str(e))
        raise HTTPException(status_code=502, detail=f"Speech-to-text failed: {e}")

    if check_emergency(transcript):
        log = AuditLog(
            org_id=org_id,
            user_id=user_id,
            action="emergency_detected",
            resource_type="voice_session",
            resource_id=data.session_id,
            details={"transcript": transcript},
        )
        session.add(log)
        session.commit()

        vs.transcription = transcript
        vs.is_emergency = True
        vs.escalated_to_human = True
        voice_service.update_session(vs)

        # HITL: emergencies also land in the staff approval queue so a human
        # sees and acts on the escalation, not just the audit log.
        approval_service = ApprovalService(session)
        request = approval_service.submit(
            org_id,
            user_id,
            ApprovalRequestCreate(
                patient_id=vs.patient_id,
                request_type=ApprovalRequestType.emergency_escalation,
                reason="Emergency phrase detected in patient voice message",
                ai_summary=f"Patient said: {transcript!r}. Emergency response was given; human follow-up required.",
            ),
        )

        from app.services.email_service import send_emergency_escalation
        send_emergency_escalation(session, request)

        return {
            "transcript": transcript,
            "response": EMERGENCY_RESPONSE,
            "audio": _tts_base64_or_none(EMERGENCY_RESPONSE),
            "is_emergency": True,
            "escalated": True,
        }

    # HITL: elevated-risk symptoms that are not hard emergencies (persistent
    # severe pain, severe dizziness, fainted, numbness, etc.) are escalated
    # deterministically — queued for staff review.
    urgent = assess_transcript(transcript)
    if urgent.requires_approval:
        vs.transcription = transcript
        vs.escalated_to_human = True
        voice_service.update_session(vs)

        approval_service = ApprovalService(session)
        approval_service.submit(
            org_id,
            user_id,
            ApprovalRequestCreate(
                patient_id=vs.patient_id,
                request_type=urgent.request_type,
                reason=urgent.reason,
                ai_summary=f"Patient said: {transcript!r}. Needs staff review before any action.",
            ),
        )
        logger.info(
            "Urgent request routed to HITL queue — session={sid} | reason={r}",
            sid=data.session_id, r=urgent.reason,
        )

        urgent_response = (
            "Your request may require urgent medical attention. "
            "I am escalating it to our clinical staff for review. "
            "A team member will contact you shortly."
        )
        return {
            "transcript": transcript,
            "response": urgent_response,
            "audio": _tts_base64_or_none(urgent_response),
            "is_emergency": False,
            "escalated": True,
        }

    try:
        result = await process_transcript(
            transcript,
            str(org_id),
            payload['token'],
            patient_id=str(vs.patient_id),
            history=vs.conversation_history or [],
        )
    except Exception as e:
        logger.error("AI agent failed for session {sid}: {err}", sid=data.session_id, err=str(e))
        raise HTTPException(status_code=502, detail=f"AI agent failed: {e}")

    vs.transcription = transcript
    vs.summary = result.get("response")
    vs.actions_taken = result.get("actions_taken")
    vs.conversation_history = result.get("updated_history")
    voice_service.update_session(vs)

    return {
        "transcript": transcript,
        "response": result.get("response"),
        "audio": _tts_base64_or_none(result.get("response", "")),
        "is_emergency": False,
        "actions_taken": result.get("actions_taken", []),
    }

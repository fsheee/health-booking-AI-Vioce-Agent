import base64
import uuid
from unittest.mock import patch

import pytest
from sqlmodel import Session, select

from app.core.security import create_access_token
from app.models.user import User
from tests.conftest import client, engine


def _admin_token():
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "admin@test.com")).first()
    if not user:
        return ""
    return create_access_token(sub=str(user.id), email=user.email, role=user.role.value, org_id=str(user.org_id))


def _auth_headers():
    return {"Authorization": f"Bearer {_admin_token()}"}


def test_list_voice_sessions_no_auth():
    resp = client.get("/api/v1/voice/sessions")
    assert resp.status_code == 401


def test_start_voice_session():
    headers = _auth_headers()
    if not headers["Authorization"]:
        pytest.skip("No admin user")

    patient = client.post("/api/v1/patients", json={"first_name": "Voice", "last_name": "Test"}, headers=headers).json()

    resp = client.post(
        "/api/v1/voice/sessions",
        json={"patient_id": str(patient["id"])},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["is_emergency"] is False

    # list sessions
    resp = client.get("/api/v1/voice/sessions", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # get session
    resp = client.get(f"/api/v1/voice/sessions/{data['id']}", headers=headers)
    assert resp.status_code == 200


def test_get_voice_session_not_found():
    headers = _auth_headers()
    resp = client.get(f"/api/v1/voice/sessions/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404


@patch("app.api.v1.endpoints.voice.transcribe_audio")
@patch("app.api.v1.endpoints.voice.process_transcript")
@patch("app.api.v1.endpoints.voice.text_to_speech")
def test_voice_process(mock_tts, mock_process, mock_stt):
    mock_stt.return_value = "I want to book an appointment"
    mock_process.return_value = {"response": "I can help with that.", "actions_taken": []}
    mock_tts.return_value = b"fake_audio_data"

    headers = _auth_headers()
    if not headers["Authorization"]:
        pytest.skip("No admin user")

    patient = client.post("/api/v1/patients", json={"first_name": "Proc", "last_name": "Test"}, headers=headers).json()
    session = client.post("/api/v1/voice/sessions", json={"patient_id": str(patient["id"])}, headers=headers).json()

    audio_b64 = base64.b64encode(b"fake_audio_bytes").decode()
    resp = client.post(
        "/api/v1/voice/process",
        json={"session_id": str(session["id"]), "audio_base64": audio_b64},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert data["is_emergency"] is False


@patch("app.api.v1.endpoints.voice.transcribe_audio")
@patch("app.api.v1.endpoints.voice.text_to_speech")
def test_voice_process_emergency(mock_tts, mock_stt):
    mock_stt.return_value = "I have chest pain"
    mock_tts.return_value = b"emergency_audio"

    headers = _auth_headers()
    if not headers["Authorization"]:
        pytest.skip("No admin user")

    patient = client.post("/api/v1/patients", json={"first_name": "Emerg", "last_name": "Test"}, headers=headers).json()
    session = client.post("/api/v1/voice/sessions", json={"patient_id": str(patient["id"])}, headers=headers).json()

    audio_b64 = base64.b64encode(b"fake_audio").decode()
    resp = client.post(
        "/api/v1/voice/process",
        json={"session_id": str(session["id"]), "audio_base64": audio_b64},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_emergency"] is True
    assert data["escalated"] is True


def _approval_requests():
    from app.models.approval_request import ApprovalRequest

    with Session(engine) as session:
        return session.exec(select(ApprovalRequest)).all()


@patch("app.api.v1.endpoints.voice.transcribe_audio")
@patch("app.api.v1.endpoints.voice.text_to_speech")
def test_voice_emergency_creates_hitl_queue_entry(mock_tts, mock_stt):
    # A hard emergency must not stop at the audit log — staff must see it in
    # the approval queue too.
    mock_stt.return_value = "I have chest pain"
    mock_tts.return_value = b"audio"

    headers = _auth_headers()
    patient = client.post("/api/v1/patients", json={"first_name": "Queue", "last_name": "Emerg"}, headers=headers).json()
    session = client.post("/api/v1/voice/sessions", json={"patient_id": str(patient["id"])}, headers=headers).json()

    resp = client.post(
        "/api/v1/voice/process",
        json={"session_id": str(session["id"]), "audio_base64": base64.b64encode(b"a").decode()},
        headers=headers,
    )
    assert resp.status_code == 200

    from app.models.approval_request import ApprovalRequestType

    requests = _approval_requests()
    assert any(r.request_type == ApprovalRequestType.emergency_escalation for r in requests)


@patch("app.api.v1.endpoints.voice.transcribe_audio")
@patch("app.api.v1.endpoints.voice.process_transcript")
@patch("app.api.v1.endpoints.voice.text_to_speech")
def test_voice_urgent_request_escalates_without_calling_agent(mock_tts, mock_agent, mock_stt):
    # Regression: "I need an emergency appointment" must be escalated
    # deterministically by the risk engine — before Gemini is ever invoked.
    mock_stt.return_value = "I need an emergency appointment"
    mock_tts.return_value = b"audio"

    headers = _auth_headers()
    patient = client.post("/api/v1/patients", json={"first_name": "Urgent", "last_name": "Test"}, headers=headers).json()
    session = client.post("/api/v1/voice/sessions", json={"patient_id": str(patient["id"])}, headers=headers).json()

    resp = client.post(
        "/api/v1/voice/process",
        json={"session_id": str(session["id"]), "audio_base64": base64.b64encode(b"a").decode()},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["escalated"] is True
    assert data["is_emergency"] is False
    assert "escalating" in data["response"].lower()

    # the agent must never have been consulted
    mock_agent.assert_not_called()

    # the request landed in the staff approval queue
    from app.models.approval_request import ApprovalRequestType

    requests = _approval_requests()
    urgent = [r for r in requests if r.request_type == ApprovalRequestType.urgent_symptoms]
    assert len(urgent) == 1
    assert urgent[0].status.value == "pending"
    assert "emergency" in (urgent[0].reason or "").lower()

    # the voice session itself is marked escalated
    vs = client.get(f"/api/v1/voice/sessions/{session['id']}", headers=headers).json()
    assert vs["escalated_to_human"] is True


@patch("app.api.v1.endpoints.voice.transcribe_audio")
@patch("app.api.v1.endpoints.voice.process_transcript")
@patch("app.api.v1.endpoints.voice.text_to_speech")
def test_voice_routine_request_is_not_escalated(mock_tts, mock_agent, mock_stt):
    mock_stt.return_value = "book me a dermatologist appointment next week"
    mock_agent.return_value = {"response": "Sure, let me check.", "actions_taken": []}
    mock_tts.return_value = b"audio"

    headers = _auth_headers()
    patient = client.post("/api/v1/patients", json={"first_name": "Routine", "last_name": "Test"}, headers=headers).json()
    session = client.post("/api/v1/voice/sessions", json={"patient_id": str(patient["id"])}, headers=headers).json()

    resp = client.post(
        "/api/v1/voice/process",
        json={"session_id": str(session["id"]), "audio_base64": base64.b64encode(b"a").decode()},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["is_emergency"] is False
    mock_agent.assert_called_once()
    assert _approval_requests() == []

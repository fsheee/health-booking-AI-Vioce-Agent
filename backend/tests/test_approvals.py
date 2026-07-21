"""HITL approval workflow tests.

Covers the full lifecycle: risk-flagged actions land in the approval queue,
approving executes the deferred action, rejecting leaves no side effects,
decisions are idempotent, and the queue is staff-only (RBAC).
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.core.security import create_access_token
from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.patient import Patient
from app.models.user import User, UserRole
from tests.conftest import client, engine

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _token(user: User) -> str:
    return create_access_token(
        sub=str(user.id), email=user.email, role=user.role.value, org_id=str(user.org_id)
    )


def _headers(user: User) -> dict:
    return {"Authorization": f"Bearer {_token(user)}"}


def _get_admin() -> User:
    with Session(engine) as session:
        return session.exec(select(User).where(User.email == "admin@test.com")).first()


def _make_user(org_id, role: UserRole, email: str | None = None) -> User:
    with Session(engine) as session:
        user = User(
            org_id=org_id,
            email=email or f"{role.value}.{uuid.uuid4().hex[:8]}@test.com",
            full_name=f"Test {role.value}",
            hashed_password="x",
            role=role,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def _make_patient(org_id, user_id=None, is_vip: bool = False) -> Patient:
    with Session(engine) as session:
        patient = Patient(
            org_id=org_id,
            user_id=user_id,
            first_name="Pat",
            last_name=uuid.uuid4().hex[:8],
            is_vip=is_vip,
        )
        session.add(patient)
        session.commit()
        session.refresh(patient)
        return patient


def _make_doctor(admin: User) -> dict:
    doc_user = _make_user(admin.org_id, UserRole.doctor)
    resp = client.post(
        "/api/v1/doctors", json={"user_id": str(doc_user.id)}, headers=_headers(admin)
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


def _future(hours: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _book(admin: User, patient: Patient, doctor: dict, scheduled_at: str, **extra) -> dict:
    resp = client.post(
        "/api/v1/tools/book_appointment",
        json={
            "patient_id": str(patient.id),
            "doctor_id": str(doctor["id"]),
            "scheduled_at": scheduled_at,
            **extra,
        },
        headers=_headers(admin),
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# RBAC
# ---------------------------------------------------------------------------


def test_approvals_require_auth():
    assert client.get("/api/v1/approvals/pending").status_code == 401


def test_patient_cannot_view_approval_queue():
    admin = _get_admin()
    patient_user = _make_user(admin.org_id, UserRole.patient)
    resp = client.get("/api/v1/approvals/pending", headers=_headers(patient_user))
    assert resp.status_code == 403


def test_front_desk_can_view_approval_queue():
    admin = _get_admin()
    front_desk = _make_user(admin.org_id, UserRole.front_desk)
    resp = client.get("/api/v1/approvals/pending", headers=_headers(front_desk))
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# booking → queue → approve/reject
# ---------------------------------------------------------------------------


def test_vip_booking_is_queued_then_approval_executes_it():
    admin = _get_admin()
    patient = _make_patient(admin.org_id, is_vip=True)
    doctor = _make_doctor(admin)

    result = _book(admin, patient, doctor, _future(48))
    assert result["status"] == "pending_approval"
    assert result["appointment_id"] is None
    assert result["approval_request_id"]

    # visible in the pending queue
    pending = client.get("/api/v1/approvals/pending", headers=_headers(admin)).json()
    assert any(r["id"] == result["approval_request_id"] for r in pending)

    # approve → the deferred booking executes
    resp = client.post(
        f"/api/v1/approvals/{result['approval_request_id']}/approve",
        json={"comment": "confirmed by staff"},
        headers=_headers(admin),
    )
    assert resp.status_code == 200
    decided = resp.json()
    assert decided["status"] == "approved"
    assert decided["appointment_id"] is not None
    assert decided["reviewer_comment"] == "confirmed by staff"

    appt = client.get(
        f"/api/v1/appointments/{decided['appointment_id']}", headers=_headers(admin)
    )
    assert appt.status_code == 200
    assert appt.json()["status"] == "scheduled"


def test_low_confidence_booking_is_queued_and_reject_leaves_no_side_effects():
    admin = _get_admin()
    patient = _make_patient(admin.org_id)
    doctor = _make_doctor(admin)

    result = _book(admin, patient, doctor, _future(72), ai_confidence=0.4)
    assert result["status"] == "pending_approval"

    resp = client.post(
        f"/api/v1/approvals/{result['approval_request_id']}/reject",
        json={"comment": "not enough information"},
        headers=_headers(admin),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
    assert resp.json()["appointment_id"] is None

    # no appointment was created for this patient
    history = client.post(
        "/api/v1/tools/get_patient_history",
        json={"patient_id": str(patient.id)},
        headers=_headers(admin),
    ).json()
    assert history["upcoming_appointments"] == []


def test_confident_routine_booking_auto_executes():
    admin = _get_admin()
    patient = _make_patient(admin.org_id)
    doctor = _make_doctor(admin)

    result = _book(admin, patient, doctor, _future(96), ai_confidence=0.95)
    assert result["status"] == "scheduled"
    assert result["appointment_id"] is not None


def test_double_booking_same_slot_is_queued():
    admin = _get_admin()
    doctor = _make_doctor(admin)
    slot = _future(120)

    first = _book(admin, _make_patient(admin.org_id), doctor, slot)
    assert first["status"] == "scheduled"

    second = _book(admin, _make_patient(admin.org_id), doctor, slot)
    assert second["status"] == "pending_approval"
    detail = client.get(
        f"/api/v1/approvals/{second['approval_request_id']}", headers=_headers(admin)
    ).json()
    assert detail["request_type"] == "double_booking"


def test_decisions_are_idempotent():
    admin = _get_admin()
    patient = _make_patient(admin.org_id, is_vip=True)
    doctor = _make_doctor(admin)

    result = _book(admin, patient, doctor, _future(48))
    request_id = result["approval_request_id"]

    approved = client.post(
        f"/api/v1/approvals/{request_id}/approve", json={}, headers=_headers(admin)
    ).json()
    assert approved["status"] == "approved"
    first_appt = approved["appointment_id"]

    # a second approve or a late reject must not change anything
    again = client.post(
        f"/api/v1/approvals/{request_id}/approve", json={}, headers=_headers(admin)
    ).json()
    assert again["status"] == "approved"
    assert again["appointment_id"] == first_appt

    rejected = client.post(
        f"/api/v1/approvals/{request_id}/reject", json={}, headers=_headers(admin)
    ).json()
    assert rejected["status"] == "approved"  # decision is final


def test_decide_unknown_request_404():
    admin = _get_admin()
    resp = client.post(
        f"/api/v1/approvals/{uuid.uuid4()}/approve", json={}, headers=_headers(admin)
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# patient cancellations
# ---------------------------------------------------------------------------


def test_patient_late_cancellation_is_queued_then_approval_cancels():
    admin = _get_admin()
    patient_user = _make_user(admin.org_id, UserRole.patient)
    patient = _make_patient(admin.org_id, user_id=patient_user.id)
    doctor = _make_doctor(admin)

    appt = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": str(patient.id),
            "doctor_id": str(doctor["id"]),
            "scheduled_at": _future(2),  # starts within 24h
        },
        headers=_headers(admin),
    ).json()

    resp = client.delete(
        f"/api/v1/appointments/{appt['id']}", headers=_headers(patient_user)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending_approval"

    # appointment is still scheduled until staff approves
    still = client.get(f"/api/v1/appointments/{appt['id']}", headers=_headers(admin)).json()
    assert still["status"] == "scheduled"

    approved = client.post(
        f"/api/v1/approvals/{body['approval_request_id']}/approve",
        json={},
        headers=_headers(admin),
    ).json()
    assert approved["status"] == "approved"

    cancelled = client.get(
        f"/api/v1/appointments/{appt['id']}", headers=_headers(admin)
    ).json()
    assert cancelled["status"] == "cancelled"


def test_patient_far_future_cancellation_executes_directly():
    admin = _get_admin()
    patient_user = _make_user(admin.org_id, UserRole.patient)
    patient = _make_patient(admin.org_id, user_id=patient_user.id)
    doctor = _make_doctor(admin)

    appt = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": str(patient.id),
            "doctor_id": str(doctor["id"]),
            "scheduled_at": _future(72),  # well outside the 24h window
        },
        headers=_headers(admin),
    ).json()

    resp = client.delete(
        f"/api/v1/appointments/{appt['id']}", headers=_headers(patient_user)
    )
    assert resp.status_code == 200
    assert "pending" not in resp.json().get("status", "")

    cancelled = client.get(
        f"/api/v1/appointments/{appt['id']}", headers=_headers(admin)
    ).json()
    assert cancelled["status"] == "cancelled"


def test_patient_cannot_cancel_someone_elses_appointment():
    admin = _get_admin()
    owner = _make_patient(admin.org_id)
    doctor = _make_doctor(admin)
    appt = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": str(owner.id),
            "doctor_id": str(doctor["id"]),
            "scheduled_at": _future(2),
        },
        headers=_headers(admin),
    ).json()

    intruder_user = _make_user(admin.org_id, UserRole.patient)
    _make_patient(admin.org_id, user_id=intruder_user.id)

    resp = client.delete(
        f"/api/v1/appointments/{appt['id']}", headers=_headers(intruder_user)
    )
    assert resp.status_code == 403


def test_staff_late_cancellation_executes_directly():
    # A front-desk/admin cancellation IS the human decision — no queue.
    admin = _get_admin()
    patient = _make_patient(admin.org_id)
    doctor = _make_doctor(admin)
    appt = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": str(patient.id),
            "doctor_id": str(doctor["id"]),
            "scheduled_at": _future(2),
        },
        headers=_headers(admin),
    ).json()

    resp = client.delete(f"/api/v1/appointments/{appt['id']}", headers=_headers(admin))
    assert resp.status_code == 200
    assert "pending" not in resp.json().get("status", "")


# ---------------------------------------------------------------------------
# agent-facing submit_for_approval
# ---------------------------------------------------------------------------


def test_submit_for_approval_creates_pending_request():
    admin = _get_admin()
    patient = _make_patient(admin.org_id)

    resp = client.post(
        "/api/v1/tools/submit_for_approval",
        json={
            "patient_id": str(patient.id),
            "request_type": "urgent_symptoms",
            "reason": "Patient reported worsening symptoms",
            "ai_summary": "Patient asked for an urgent visit",
        },
        headers=_headers(admin),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending"

    with Session(engine) as session:
        request = session.get(ApprovalRequest, uuid.UUID(body["approval_request_id"]))
        assert request is not None
        assert request.status == ApprovalStatus.pending
        assert request.request_type.value == "urgent_symptoms"


def test_submit_for_approval_coerces_unknown_type_to_other():
    admin = _get_admin()
    patient = _make_patient(admin.org_id)

    resp = client.post(
        "/api/v1/tools/submit_for_approval",
        json={
            "patient_id": str(patient.id),
            "request_type": "made_up_type",
            "ai_summary": "…",
        },
        headers=_headers(admin),
    )
    assert resp.status_code == 200
    with Session(engine) as session:
        request = session.get(
            ApprovalRequest, uuid.UUID(resp.json()["approval_request_id"])
        )
        assert request.request_type.value == "other"

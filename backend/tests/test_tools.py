from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session, select

from app.core.security import create_access_token
from app.models.user import User, UserRole
from tests.conftest import client, engine


def _admin_token():
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "admin@test.com")).first()
    if not user:
        return ""
    return create_access_token(sub=str(user.id), email=user.email, role=user.role.value, org_id=str(user.org_id))


def _auth_headers():
    return {"Authorization": f"Bearer {_admin_token()}"}


def test_check_availability_no_auth():
    resp = client.post(
        "/api/v1/tools/check_availability",
        json={"doctor_id": "00000000-0000-0000-0000-000000000000", "date": "2030-01-01"},
    )
    assert resp.status_code == 401


def test_book_appointment_no_auth():
    resp = client.post(
        "/api/v1/tools/book_appointment",
        json={
            "patient_id": "00000000-0000-0000-0000-000000000000",
            "doctor_id": "00000000-0000-0000-0000-000000000000",
            "scheduled_at": "2030-01-01T10:00:00Z",
        },
    )
    assert resp.status_code == 401


def test_check_availability():
    headers = _auth_headers()
    if not headers["Authorization"]:
        pytest.skip("No admin user")

    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "admin@test.com")).first()
        org_id = user.org_id

    doc_user = User(

        org_id=org_id,

        email="dr.tool@test.com",

        full_name="Dr Tool",

        hashed_password="x",

        role=UserRole.doctor,

    )
    with Session(engine) as session:
        session.add(doc_user)
        session.commit()
        session.refresh(doc_user)

    doctor = client.post(
        "/api/v1/doctors", json={"user_id": str(doc_user.id)}, headers=headers,
    ).json()

    from datetime import date, timedelta
    future = (date.today() + timedelta(days=1)).isoformat()
    resp = client.post(
        "/api/v1/tools/check_availability",
        json={"doctor_id": str(doctor["id"]), "date": future},
        headers=headers,
    )
    assert resp.status_code == 200
    assert "available_slots" in resp.json()


def test_book_appointment():
    headers = _auth_headers()
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "admin@test.com")).first()
        org_id = user.org_id

    patient = client.post("/api/v1/patients", json={"first_name": "Tool", "last_name": "Test"}, headers=headers).json()

    doc_user = User(

        org_id=org_id,

        email="dr.book@test.com",

        full_name="Dr Book",

        hashed_password="x",

        role=UserRole.doctor,

    )
    with Session(engine) as session:
        session.add(doc_user)
        session.commit()
        session.refresh(doc_user)

    doctor = client.post("/api/v1/doctors", json={"user_id": str(doc_user.id)}, headers=headers).json()

    scheduled_at = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    resp = client.post(
        "/api/v1/tools/book_appointment",
        json={"patient_id": str(patient["id"]), "doctor_id": str(doctor["id"]), "scheduled_at": scheduled_at},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "scheduled"
    assert "appointment_id" in data


def test_get_patient_history():
    headers = _auth_headers()

    patient = client.post(
        "/api/v1/patients", json={"first_name": "History", "last_name": "Test"}, headers=headers,
    ).json()

    resp = client.post(
        "/api/v1/tools/get_patient_history",
        json={"patient_id": str(patient["id"])},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "patient_name" in data
    assert "upcoming_appointments" in data
    assert "past_appointments" in data


def test_send_reminder():
    headers = _auth_headers()
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "admin@test.com")).first()
        org_id = user.org_id

    patient = client.post("/api/v1/patients", json={"first_name": "Remind", "last_name": "Me"}, headers=headers).json()

    doc_user = User(

        org_id=org_id,

        email="dr.remind@test.com",

        full_name="Dr Remind",

        hashed_password="x",

        role=UserRole.doctor,

    )
    with Session(engine) as session:
        session.add(doc_user)
        session.commit()
        session.refresh(doc_user)

    doctor = client.post("/api/v1/doctors", json={"user_id": str(doc_user.id)}, headers=headers).json()

    appt = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": str(patient["id"]),
            "doctor_id": str(doctor["id"]),
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        },
        headers=headers,
    ).json()

    resp = client.post(
        "/api/v1/tools/send_reminder",
        json={"appointment_id": str(appt["id"]), "patient_id": str(patient["id"]), "channel": "email"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pending"
    assert "reminder_id" in data

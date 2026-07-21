import uuid

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


def test_list_doctors_no_auth():
    resp = client.get("/api/v1/doctors")
    assert resp.status_code == 401


def test_doctor_availability_no_auth():
    resp = client.get(f"/api/v1/doctors/{uuid.uuid4()}/availability")
    assert resp.status_code == 401


def test_create_and_list_doctors():
    headers = _auth_headers()
    if not headers["Authorization"]:
        pytest.skip("No admin user")

    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "admin@test.com")).first()
        org_id = user.org_id

    doc_user = User(

        org_id=org_id,

        email="dr.test@clinic.com",

        full_name="Dr. Test",

        hashed_password="x",

        role=UserRole.doctor,

    )
    with Session(engine) as session:
        session.add(doc_user)
        session.commit()
        session.refresh(doc_user)

    resp = client.post(
        "/api/v1/doctors",
        json={"user_id": str(doc_user.id), "specialization": "Cardiology", "license_number": "LIC-123"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["specialization"] == "Cardiology"
    assert data["is_available"] is True

    # list
    resp = client.get("/api/v1/doctors", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # get
    resp = client.get(f"/api/v1/doctors/{data['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["specialization"] == "Cardiology"


def test_get_doctor_not_found():
    headers = _auth_headers()
    resp = client.get(f"/api/v1/doctors/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404


def test_doctor_availability():
    headers = _auth_headers()
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "admin@test.com")).first()
        org_id = user.org_id

    doc_user = User(

        org_id=org_id,

        email="dr.avail@clinic.com",

        full_name="Dr. Avail",

        hashed_password="x",

        role=UserRole.doctor,

    )
    with Session(engine) as session:
        session.add(doc_user)
        session.commit()
        session.refresh(doc_user)

    doctor = client.post(
        "/api/v1/doctors", json={"user_id": str(doc_user.id), "specialization": "General"}, headers=headers,
    ).json()

    from datetime import date, timedelta
    future = (date.today() + timedelta(days=1)).isoformat()
    resp = client.get(f"/api/v1/doctors/{doctor['id']}/availability?date={future}", headers=headers)
    assert resp.status_code == 200
    slots = resp.json()
    assert isinstance(slots, list)
    if slots:
        assert "slots" in slots[0]

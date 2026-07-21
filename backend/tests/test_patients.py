import uuid

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
    token = _admin_token()
    return {"Authorization": f"Bearer {token}"}


def test_list_patients_empty():
    resp = client.get("/api/v1/patients")
    assert resp.status_code == 401


def test_create_patient():
    headers = _auth_headers()
    if not headers["Authorization"]:
        pytest.skip("No admin user")

    resp = client.post(
        "/api/v1/patients",
        json={"first_name": "John", "last_name": "Doe", "phone": "1234567890", "email": "john@test.com"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["phone"] == "1234567890"
    assert "id" in data


def test_list_patients():
    headers = _auth_headers()
    resp = client.get("/api/v1/patients", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_get_patient():
    headers = _auth_headers()
    create = client.post(
        "/api/v1/patients", json={"first_name": "Jane", "last_name": "Smith"}, headers=headers,
    )
    pid = create.json()["id"]

    resp = client.get(f"/api/v1/patients/{pid}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Jane"


def test_get_patient_not_found():
    headers = _auth_headers()
    resp = client.get(f"/api/v1/patients/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404


def test_update_patient():
    headers = _auth_headers()
    create = client.post(
        "/api/v1/patients", json={"first_name": "Bob", "last_name": "Brown"}, headers=headers,
    )
    pid = create.json()["id"]

    resp = client.put(
        f"/api/v1/patients/{pid}", json={"phone": "9999999999"}, headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["phone"] == "9999999999"


def test_search_patients():
    headers = _auth_headers()
    client.post("/api/v1/patients", json={"first_name": "Alice", "last_name": "Jones"}, headers=headers)

    resp = client.get("/api/v1/patients?search=Alice", headers=headers)
    assert resp.status_code == 200
    assert any(p["first_name"] == "Alice" for p in resp.json())


def test_get_my_patient_profile():
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "admin@test.com")).first()
    from app.models.patient import Patient
    with Session(engine) as session:
        patient = session.exec(select(Patient).where(Patient.user_id == user.id)).first()
    if not patient:
        patient = Patient(org_id=user.org_id, user_id=user.id, first_name="Admin", last_name="User", email=user.email)
        with Session(engine) as session:
            session.add(patient)
            session.commit()

    token = create_access_token(sub=str(user.id), email=user.email, role=user.role.value, org_id=str(user.org_id))
    resp = client.get("/api/v1/patients/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@test.com"

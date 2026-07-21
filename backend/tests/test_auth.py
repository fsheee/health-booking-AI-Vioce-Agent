from unittest.mock import patch

import pytest
from sqlmodel import Session, select

from app.models.user import User, UserRole
from tests.conftest import client, engine


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


@patch("app.api.v1.endpoints.auth.pwd_context.hash")
def test_signup(mock_hash):
    mock_hash.return_value = "$2b$12$hashedpass"

    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": "new@test.com", "password": "password123", "full_name": "New Patient", "org_slug": "new-org"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data

    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "new@test.com")).first()
        assert user is not None
        assert user.full_name == "New Patient"
        assert user.role == UserRole.patient
        from app.models.patient import Patient
        patient = session.exec(select(Patient).where(Patient.user_id == user.id)).first()
        assert patient is not None
        assert patient.first_name == "New"
        assert patient.last_name == "Patient"


def test_signup_duplicate_email():
    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": "admin@test.com", "password": "password123", "full_name": "Dup", "org_slug": "dup-org"},
    )
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


@patch("app.api.v1.endpoints.auth.pwd_context.verify")
def test_login(mock_verify):
    mock_verify.return_value = True

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "admin123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


@patch("app.api.v1.endpoints.auth.pwd_context.verify")
def test_login_invalid(mock_verify):
    mock_verify.return_value = False

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@test.com", "password": "wrong"},
    )
    assert resp.status_code == 401


def _get_token():
    from app.core.security import create_access_token
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "admin@test.com")).first()
    if not user:
        return ""
    return create_access_token(sub=str(user.id), email=user.email, role=user.role.value, org_id=str(user.org_id))


def test_me():
    token = _get_token()
    if not token:
        pytest.skip("No admin user found")
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "admin@test.com"
    assert "role" in data
    assert "org_id" in data


def test_me_no_auth():
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401

import uuid
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.core.dependencies import get_session
from app.main import app
from app.models.organization import Organization
from app.models.user import User, UserRole

TEST_DB_URL = "sqlite:///test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})


def override_get_session() -> Generator[Session, None, None]:
    with Session(engine, expire_on_commit=False) as session:
        yield session


app.dependency_overrides[get_session] = override_get_session
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield


@pytest.fixture(autouse=True)
def org(setup_db) -> Organization:
    with Session(engine) as session:
        o = Organization(id=uuid.uuid4(), name="Test Clinic", slug="test-clinic")
        session.add(o)
        session.commit()
        session.refresh(o)
        return o


@pytest.fixture(autouse=True)
def admin_user(org: Organization) -> User:
    with Session(engine) as session:
        u = User(
            id=uuid.uuid4(),
            org_id=org.id,
            hashed_password="$2b$12$placeholder",
            email="admin@test.com",
            full_name="Admin User",
            role=UserRole.admin,
        )
        session.add(u)
        session.commit()
        session.refresh(u)
        return u

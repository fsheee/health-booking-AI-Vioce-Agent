import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlmodel import Column, Field, SQLModel


class UserRole(str, PyEnum):
    admin = "admin"
    doctor = "doctor"
    front_desk = "front_desk"
    patient = "patient"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    org_id: uuid.UUID = Field(
        foreign_key="organizations.id", nullable=False, index=True
    )
    hashed_password: str = Field(sa_column=Column(String(255), nullable=False))
    email: str = Field(sa_column=Column(String(255), unique=True, nullable=False, index=True))
    full_name: str = Field(sa_column=Column(String(255), nullable=False))
    role: UserRole = Field(sa_column=Column(Enum(UserRole), nullable=False, default=UserRole.patient))
    phone: str | None = Field(sa_column=Column(String(50), nullable=True))
    is_active: bool = Field(default=True, sa_column=Column(Boolean, default=True, nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, func
from sqlmodel import Column, Field, SQLModel


class Doctor(SQLModel, table=True):
    __tablename__ = "doctors"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    user_id: uuid.UUID = Field(
        foreign_key="users.id", unique=True, nullable=False,
    )
    org_id: uuid.UUID = Field(
        foreign_key="organizations.id", nullable=False, index=True,
    )
    specialization: str = Field(sa_column=Column(String(255), nullable=True))
    license_number: str = Field(sa_column=Column(String(100), nullable=True))
    is_available: bool = Field(default=True, sa_column=Column(Boolean, default=True, nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )

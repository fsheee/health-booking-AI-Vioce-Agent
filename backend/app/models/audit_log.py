import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, String, func
from sqlmodel import Column, Field, SQLModel


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    org_id: uuid.UUID = Field(
        foreign_key="organizations.id", nullable=False, index=True,
    )
    user_id: uuid.UUID | None = Field(
        foreign_key="users.id", nullable=True,
    )
    action: str = Field(sa_column=Column(String(100), nullable=False))
    resource_type: str = Field(sa_column=Column(String(100), nullable=False))
    resource_id: uuid.UUID | None = Field(
        nullable=True,
    )
    details: dict | None = Field(sa_column=Column(JSON, nullable=True, default=dict))
    ip_address: str | None = Field(sa_column=Column(String(50), nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )

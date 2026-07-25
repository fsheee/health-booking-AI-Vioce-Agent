import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text, func
from sqlmodel import Column, Field, SQLModel


class Organization(SQLModel, table=True):
    __tablename__ = "organizations"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    name: str = Field(sa_column=Column(String(255), nullable=False))
    slug: str = Field(sa_column=Column(String(255), unique=True, nullable=False, index=True))
    phone: str | None = Field(sa_column=Column(String(50), nullable=True))
    address: str | None = Field(sa_column=Column(Text, nullable=True))
    email: str | None = Field(sa_column=Column(String(255), nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )
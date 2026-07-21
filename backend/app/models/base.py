import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlmodel import Column, Field, SQLModel, create_engine

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"connect_timeout": 30},
    pool_pre_ping=True,
)


def utcnow():
    return datetime.now(timezone.utc)


class Base(SQLModel):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    org_id: uuid.UUID = Field(
        foreign_key="organizations.id", nullable=False,
    )
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )

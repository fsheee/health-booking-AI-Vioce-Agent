import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Text, func
from sqlmodel import Column, Field, SQLModel


class VoiceSession(SQLModel, table=True):
    __tablename__ = "voice_sessions"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    org_id: uuid.UUID = Field(
        foreign_key="organizations.id", nullable=False, index=True,
    )
    patient_id: uuid.UUID = Field(
        foreign_key="patients.id", nullable=False, index=True,
    )
    user_id: uuid.UUID | None = Field(
        foreign_key="users.id", nullable=True,
    )
    transcription: str | None = Field(sa_column=Column(Text, nullable=True))
    summary: str | None = Field(sa_column=Column(Text, nullable=True))
    # List of tool-call dicts recorded by process_transcript(); older rows may
    # hold a bare dict from the previous column default.
    actions_taken: list | dict | None = Field(sa_column=Column(JSON, nullable=True, default=list))
    # Full Gemini conversation history stored as a list of ContentDict objects
    # so each turn can be replayed without starting a new chat session.
    conversation_history: list | None = Field(sa_column=Column(JSON, nullable=True, default=list))
    is_emergency: bool = Field(default=False, sa_column=Column(Boolean, default=False, nullable=False))
    escalated_to_human: bool = Field(default=False, sa_column=Column(Boolean, default=False, nullable=False))
    started_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=True))
    ended_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )

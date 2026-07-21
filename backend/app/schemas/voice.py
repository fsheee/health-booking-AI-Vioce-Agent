from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator


class VoiceSessionStart(BaseModel):
    patient_id: UUID | None = None


class VoiceProcessRequest(BaseModel):
    session_id: UUID
    audio_base64: str


def _coerce_actions(v: object) -> list | None:
    # process_transcript() stores actions_taken as a list of tool-call dicts,
    # but older sessions were saved as a dict (JSON column default) — accept both.
    if v is None or isinstance(v, list):
        return v
    if isinstance(v, dict):
        return [v] if v else []
    return v


class VoiceSessionResponse(BaseModel):
    id: UUID
    org_id: UUID
    patient_id: UUID
    transcription: str | None = None
    summary: str | None = None
    actions_taken: Annotated[list | None, BeforeValidator(_coerce_actions)] = None
    is_emergency: bool = False
    escalated_to_human: bool = False
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime

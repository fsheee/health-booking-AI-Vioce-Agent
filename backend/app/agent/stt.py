import asyncio

import assemblyai as aai

from app.core.config import settings

aai.settings.api_key = settings.assemblyai_api_key


async def transcribe_audio(audio_bytes: bytes, language_code: str = "en") -> str:
    def _sync_transcribe():
        transcript = aai.Transcriber().transcribe(audio_bytes)
        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(f"Transcription failed: {transcript.error}")
        return transcript.text

    return await asyncio.to_thread(_sync_transcribe)


async def transcribe_from_url(audio_url: str) -> str:
    def _sync_transcribe():
        transcript = aai.Transcriber().transcribe(audio_url)
        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(f"Transcription failed: {transcript.error}")
        return transcript.text

    return await asyncio.to_thread(_sync_transcribe)

from importlib import import_module

from app.core.config import settings

USE_ELEVENLABS = bool(settings.elevenlabs_api_key)
USE_DEEPGRAM = bool(settings.deepgram_api_key)

_ELEVENLABS_AVAILABLE = None
_DEEPGRAM_AVAILABLE = None


def _provider_available(name: str) -> bool:
    """Check if a provider package is installed (lazy, cached)."""
    global _ELEVENLABS_AVAILABLE, _DEEPGRAM_AVAILABLE
    if name == "elevenlabs":
        if _ELEVENLABS_AVAILABLE is None:
            try:
                import_module("elevenlabs")
                _ELEVENLABS_AVAILABLE = True
            except ImportError:
                _ELEVENLABS_AVAILABLE = False
        return _ELEVENLABS_AVAILABLE
    if name == "deepgram":
        if _DEEPGRAM_AVAILABLE is None:
            try:
                import_module("deepgram")
                _DEEPGRAM_AVAILABLE = True
            except ImportError:
                _DEEPGRAM_AVAILABLE = False
        return _DEEPGRAM_AVAILABLE
    return False


def text_to_speech(text: str, voice_id: str = "default") -> bytes:
    if USE_ELEVENLABS and _provider_available("elevenlabs"):
        from elevenlabs.client import ElevenLabs

        client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        audio = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id if voice_id != "default" else "JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_monolingual_v1",
            output_format="mp3_44100_128",
        )
        return b"".join(audio)

    if USE_DEEPGRAM and _provider_available("deepgram"):
        from deepgram import DeepgramClient, SpeakOptions

        client = DeepgramClient(api_key=settings.deepgram_api_key)
        options = SpeakOptions(model="aura-asteria-en", encoding="linear16", container="wav")
        response = client.speak.rest.v("1").save(text, text, options)
        if response and hasattr(response, 'data'):
            return response.data
        return b""

    raise ValueError(
        "No TTS provider available. Set ELEVENLABS_API_KEY / DEEPGRAM_API_KEY and install the provider package."
    )

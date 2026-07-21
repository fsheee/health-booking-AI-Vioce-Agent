EMERGENCY_PHRASES = [
    "chest pain",
    "difficulty breathing",
    "shortness of breath",
    "stroke symptoms",
    "severe bleeding",
    "loss of consciousness",
    "unconscious",
    "heart attack",
    "severe allergic reaction",
    "anaphylaxis",
    "suicidal",
    "overdose",
]


EMERGENCY_RESPONSE = (
    "EMERGENCY: I cannot provide medical advice. Please hang up and call 911 immediately. "
    "This is a medical emergency."
)


def check_emergency(text: str) -> bool:
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in EMERGENCY_PHRASES)

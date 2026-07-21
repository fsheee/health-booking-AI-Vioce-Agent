from app.agent.emergency import EMERGENCY_PHRASES, check_emergency


def test_emergency_phrases():
    for phrase in EMERGENCY_PHRASES:
        assert check_emergency(f"patient says {phrase}"), f"'{phrase}' not detected"


def test_non_emergency():
    assert not check_emergency("I have a mild headache")
    assert not check_emergency("I need to book an appointment")

"""End-to-end evaluation of doctor-specialty routing.

Seeds a fresh org (patient + 4 doctors with distinct specialties) in the DB,
then drives process_transcript against live Gemini + the running backend and
scores tool-call correctness and name grounding.

Run: uv run python eval_routing.py   (backend must be running on :8000)
"""

import asyncio
import re
import socket
import time

import httpx

# Same IPv4-first patch as app/main.py — this machine's IPv6 routing is broken
# and this script connects to NeonDB directly without importing app.main.
_orig_getaddrinfo = socket.getaddrinfo


def _ipv4_fallback_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    try:
        return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
    except socket.gaierror:
        return _orig_getaddrinfo(host, port, family, type, proto, flags)


socket.getaddrinfo = _ipv4_fallback_getaddrinfo
from sqlmodel import Session, select  # noqa: E402

from app.agent.agent import process_transcript  # noqa: E402
from app.models.base import engine  # noqa: E402
from app.models.doctor import Doctor  # noqa: E402
from app.models.patient import Patient  # noqa: E402
from app.models.user import User  # noqa: E402

BASE = "http://localhost:8000/api/v1"

DOCTORS = [
    ("Ahmed Raza", "Cardiology"),
    ("Sara Malik", "Neurology"),
    ("Bilal Chaudhry", "Dermatology"),
    ("Nadia Hussain", "General Physician"),
]


def seed() -> tuple[str, str, str, list[str]]:
    slug = f"evalorg{int(time.time())}"
    with httpx.Client(timeout=60) as client:
        r = client.post(f"{BASE}/auth/signup", json={
            "org_slug": slug, "email": f"patient@{slug}.com",
            "password": "Passw0rd!123", "full_name": "Eval Patient", "role": "patient",
        })
        r.raise_for_status()
        token = r.json()["access_token"]

        for name, _spec in DOCTORS:
            handle = name.lower().replace(" ", ".")
            client.post(f"{BASE}/auth/signup", json={
                "org_slug": slug, "email": f"{handle}@{slug}.com",
                "password": "Passw0rd!123", "full_name": name, "role": "doctor",
            }).raise_for_status()

    with Session(engine) as db:
        patient_user = db.exec(select(User).where(User.email == f"patient@{slug}.com")).one()
        org_id = str(patient_user.org_id)
        patient = db.exec(select(Patient).where(Patient.user_id == patient_user.id)).one()
        patient_id = str(patient.id)
        for name, spec in DOCTORS:
            u = db.exec(select(User).where(User.email == f"{name.lower().replace(' ', '.')}@{slug}.com")).one()
            doc = db.exec(select(Doctor).where(Doctor.user_id == u.id)).one()
            doc.specialization = spec
            db.add(doc)
        db.commit()

    return token, org_id, patient_id, [p for n, _ in DOCTORS for p in n.split()]


def invented_names(response: str, allowed_tokens: list[str]) -> list[str]:
    """Doctor names mentioned in the reply that were never seeded."""
    mentions = re.findall(r"Dr\.?\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)", response)
    bad = []
    for m in mentions:
        if not any(tok in allowed_tokens for tok in m.split()):
            bad.append(m)
    return bad


async def run_case(name, transcript, token, org_id, patient_id, history, checks):
    result = await process_transcript(transcript, org_id, token, patient_id=patient_id, history=history)
    tools = [(a["tool"], a["args"]) for a in result["actions_taken"]]
    print(f"\n=== {name}")
    print(f"  user     : {transcript!r}")
    print(f"  tools    : {tools}")
    print(f"  response : {result['response']!r}")
    verdicts = []
    for label, fn in checks:
        ok = fn(result, tools)
        verdicts.append((label, ok))
        print(f"  {'PASS' if ok else 'FAIL'} — {label}")
    return result, verdicts


async def main():
    token, org_id, patient_id, name_tokens = seed()
    print(f"Seeded org={org_id} patient={patient_id} doctors={DOCTORS}")
    all_verdicts = []

    def no_invented(result, _tools):
        bad = invented_names(result["response"], name_tokens)
        if bad:
            print(f"       invented names: {bad}")
        return not bad

    def fd_with(spec):
        def check(_result, tools):
            return any(t == "find_doctors" and a.get("specialization") == spec for t, a in tools)
        return check

    def times_grounded(result, _tools):
        """Any time quoted in the reply must exist in a check_availability result."""
        slots = set()
        for a in result["actions_taken"]:
            if a["tool"] == "check_availability":
                slots.update(a["result"].get("available_slots", []))
        quoted = []
        for h, m, ampm in re.findall(r"(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?", result["response"]):
            hour = int(h) % 12 + (12 if ampm and ampm.lower() == "pm" else 0)
            quoted.append(f"{hour:02d}:{m}")
        if quoted and not slots:
            print(f"       times quoted with no check_availability call: {quoted}")
            return False
        bad = [t for t in quoted if t not in slots]
        if bad:
            print(f"       fabricated times not in slots: {bad} (slots={sorted(slots)})")
        return not bad

    def booked_ok(result, _tools):
        return any(
            a["tool"] == "book_appointment" and a["result"].get("appointment_id")
            for a in result["actions_taken"]
        )

    # 1. The exact reported symptom
    r1, v1 = await run_case(
        "cardiologist next week", "I need a cardiologist appointment next week",
        token, org_id, patient_id, [],
        [("find_doctors called with specialization=Cardiology", fd_with("Cardiology")),
         ("no invented doctor names", no_invented),
         ("quoted times grounded in check_availability", times_grounded),
         ("cardiologist surfaced or offered",
          lambda r, t: "Ahmed" in r["response"] or "Raza" in r["response"])],
    )
    all_verdicts += v1

    # 2. Colloquial synonym
    _r2, v2 = await run_case(
        "skin doctor tomorrow", "Can I see a skin doctor tomorrow?",
        token, org_id, patient_id, [],
        [("find_doctors called with specialization=Dermatology", fd_with("Dermatology")),
         ("no invented doctor names", no_invented),
         ("quoted times grounded in check_availability", times_grounded)],
    )
    all_verdicts += v2

    # 3. Multi-turn: specialty arrives one turn later (history replay)
    r3a, v3a = await run_case(
        "multi-turn / turn 1", "I need an appointment next week",
        token, org_id, patient_id, [],
        [("no invented doctor names", no_invented)],
    )
    all_verdicts += v3a
    r3b, v3b = await run_case(
        "multi-turn / turn 2", "A cardiologist please",
        token, org_id, patient_id, r3a["updated_history"],
        [("find_doctors called with specialization=Cardiology", fd_with("Cardiology")),
         ("no invented doctor names", no_invented),
         ("quoted times grounded in check_availability", times_grounded)],
    )
    all_verdicts += v3b
    _r3c, v3c = await run_case(
        "multi-turn / turn 3 (booking)", "The earliest time works for me, please book it",
        token, org_id, patient_id, r3b["updated_history"],
        [("book_appointment executed successfully", booked_ok),
         ("no invented doctor names", no_invented)],
    )
    all_verdicts += v3c

    # 4. Small talk must not trigger tools
    _r4, v4 = await run_case(
        "small talk", "Hello, good morning",
        token, org_id, patient_id, [],
        [("no tool calls", lambda r, t: not t),
         ("no invented doctor names", no_invented)],
    )
    all_verdicts += v4

    # 5. Emergency path untouched (keyword gate, pre-Gemini)
    _r5, v5 = await run_case(
        "emergency", "I have chest pain right now",
        token, org_id, patient_id, [],
        [("emergency escalated", lambda r, t: r["is_emergency"] and r["escalated"]),
         ("no tool calls", lambda r, t: not t)],
    )
    all_verdicts += v5

    passed = sum(ok for _, ok in all_verdicts)
    print(f"\n{'=' * 50}\nRESULT: {passed}/{len(all_verdicts)} checks passed")


if __name__ == "__main__":
    asyncio.run(main())


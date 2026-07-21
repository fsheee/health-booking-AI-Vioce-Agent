"""End-to-end smoke test for the HITL approval workflow.

Runs against the real database via TestClient in a throwaway org.
Covers: VIP booking → queue → approve (executes booking),
low-confidence booking → queue → reject (no booking),
double-booking → queue, late patient cancellation → queue → approve (cancels).
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import app
from app.models.base import engine
from app.models.patient import Patient

client = TestClient(app)
RUN = uuid.uuid4().hex[:8]
ORG_SLUG = f"hitl-test-{RUN}"


def signup(role: str, name: str, **extra) -> str:
    r = client.post("/api/v1/auth/signup", json={
        "email": f"{role}-{RUN}@hitltest-mail.com",
        "password": "Str0ngPass!",
        "full_name": name,
        "org_slug": ORG_SLUG,
        "role": role,
        **extra,
    })
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def check(label: str, cond: bool, detail: str = ""):
    print(f"  {'OK ' if cond else 'FAIL'} - {label}" + (f" | {detail}" if detail else ""))
    assert cond, f"{label}: {detail}"


print(f"== HITL E2E ({ORG_SLUG}) ==")

front_desk = signup("front_desk", "Front Desk")
doctor_token = signup("doctor", "Dr. Test Cardio", specialization="Cardiology")
patient_token = signup("patient", "Pat Patient")

# Doctor id
doctors = client.get("/api/v1/doctors", headers=auth(front_desk)).json()
doctor_id = doctors[0]["id"]

# Patients: the signup-created one (for cancellation test) + a VIP one
patients = client.get("/api/v1/patients", headers=auth(front_desk)).json()
signup_patient_id = patients[0]["id"]

r = client.post("/api/v1/patients", headers=auth(front_desk), json={
    "first_name": "Vip", "last_name": "Person", "email": f"vip-{RUN}@hitltest-mail.com",
})
vip_patient_id = r.json()["id"]
with Session(engine) as s:
    p = s.get(Patient, uuid.UUID(vip_patient_id))
    p.is_vip = True
    s.add(p)
    s.commit()

tomorrow = (datetime.now(timezone.utc) + timedelta(days=2)).replace(
    hour=10, minute=0, second=0, microsecond=0
)

print("\n1. VIP booking routes to approval queue")
r = client.post("/api/v1/tools/book_appointment", headers=auth(front_desk), json={
    "doctor_id": doctor_id, "scheduled_at": tomorrow.isoformat(),
    "reason": "checkup", "patient_id": vip_patient_id,
})
check("status pending_approval", r.json().get("status") == "pending_approval", r.text)
check("no appointment created yet", r.json().get("appointment_id") is None)
vip_approval_id = r.json()["approval_request_id"]

print("\n2. Queue visible to staff")
r = client.get("/api/v1/approvals/pending", headers=auth(front_desk))
pending_ids = [a["id"] for a in r.json()]
check("VIP request in pending queue", vip_approval_id in pending_ids)
check("patient cannot view queue",
      client.get("/api/v1/approvals/pending", headers=auth(patient_token)).status_code == 403)

print("\n3. Approve executes the deferred booking")
r = client.post(f"/api/v1/approvals/{vip_approval_id}/approve",
                headers=auth(front_desk), json={"comment": "VIP confirmed by staff"})
body = r.json()
check("status approved", body["status"] == "approved", r.text)
check("reviewer comment stored", body["reviewer_comment"] == "VIP confirmed by staff")
check("appointment_id set after execution", body["appointment_id"] is not None)
appts = client.get("/api/v1/appointments", headers=auth(front_desk)).json()
check("appointment exists in org", any(a["id"] == body["appointment_id"] for a in appts))
vip_appt_time = tomorrow

print("\n4. Double-booking the same slot routes to queue")
r = client.post("/api/v1/tools/book_appointment", headers=auth(front_desk), json={
    "doctor_id": doctor_id, "scheduled_at": vip_appt_time.isoformat(),
    "patient_id": signup_patient_id,
})
check("double-booking flagged", r.json().get("status") == "pending_approval", r.text)
check("reason mentions conflict", "conflict" in r.json().get("message", "").lower())

print("\n5. Low-confidence booking → queue → reject (no side effects)")
slot2 = tomorrow.replace(hour=14)
r = client.post("/api/v1/tools/book_appointment", headers=auth(front_desk), json={
    "doctor_id": doctor_id, "scheduled_at": slot2.isoformat(),
    "patient_id": signup_patient_id, "ai_confidence": 0.55,
})
check("low confidence flagged", r.json().get("status") == "pending_approval", r.text)
low_conf_id = r.json()["approval_request_id"]
n_appts_before = len(client.get("/api/v1/appointments", headers=auth(front_desk)).json())
r = client.post(f"/api/v1/approvals/{low_conf_id}/reject",
                headers=auth(front_desk), json={"comment": "Could not verify request"})
check("status rejected", r.json()["status"] == "rejected", r.text)
n_appts_after = len(client.get("/api/v1/appointments", headers=auth(front_desk)).json())
check("no appointment created on reject", n_appts_before == n_appts_after)

print("\n6. Routine booking still auto-executes (no HITL)")
slot3 = tomorrow.replace(hour=15)
r = client.post("/api/v1/tools/book_appointment", headers=auth(front_desk), json={
    "doctor_id": doctor_id, "scheduled_at": slot3.isoformat(),
    "patient_id": signup_patient_id, "ai_confidence": 0.95,
})
check("auto-executed", r.json().get("status") == "scheduled", r.text)
check("appointment_id returned", r.json().get("appointment_id") is not None)

print("\n7. Patient late cancellation (<24h) → queue → approve cancels")
soon = (datetime.now(timezone.utc) + timedelta(hours=5)).replace(minute=0, second=0, microsecond=0)
r = client.post("/api/v1/appointments", headers=auth(front_desk), json={
    "patient_id": signup_patient_id, "doctor_id": doctor_id,
    "scheduled_at": soon.isoformat(), "duration_minutes": 30,
})
soon_appt_id = r.json()["id"]
r = client.delete(f"/api/v1/appointments/{soon_appt_id}", headers=auth(patient_token))
check("late cancel routed to queue", r.json().get("status") == "pending_approval", r.text)
cancel_approval_id = r.json()["approval_request_id"]
r = client.post(f"/api/v1/approvals/{cancel_approval_id}/approve",
                headers=auth(front_desk), json={"comment": "ok to cancel"})
check("cancel approval approved", r.json()["status"] == "approved", r.text)
r = client.get(f"/api/v1/appointments/{soon_appt_id}", headers=auth(front_desk))
check("appointment now cancelled", r.json()["status"] == "cancelled", r.text)

print("\n8. Patient cannot cancel someone else's appointment")
r = client.delete(f"/api/v1/appointments/{body['appointment_id']}", headers=auth(patient_token))
check("403 for foreign appointment", r.status_code == 403, r.text)

print("\n9. Decisions are idempotent")
r = client.post(f"/api/v1/approvals/{low_conf_id}/approve",
                headers=auth(front_desk), json={})
check("re-deciding a rejected request keeps rejected", r.json()["status"] == "rejected")

print("\n== ALL HITL E2E CHECKS PASSED ==")

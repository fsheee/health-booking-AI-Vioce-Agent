from fastapi import APIRouter

from app.api.v1.endpoints import appointments, approvals, auth, doctors, patients, tools, voice

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(patients.router)
router.include_router(doctors.router)
router.include_router(appointments.router)
router.include_router(approvals.router)
router.include_router(voice.router)
router.include_router(tools.router)

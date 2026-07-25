from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.dependencies import get_current_user, get_session
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    session: Session = Depends(get_session),
    payload: dict = Depends(get_current_user),
):
    service = DashboardService(session)
    return service.get_dashboard(payload["org_id"], payload["role"])

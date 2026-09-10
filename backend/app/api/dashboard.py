"""Dashboard statistics endpoint. Scoped to the requesting researcher."""
from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def dashboard_stats(user=Depends(get_current_user)):
    return dashboard_service.get_dashboard_stats(user["username"])

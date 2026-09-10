"""Report endpoints. Scoped to the requesting researcher."""
from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.services import report_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/prediction/{prediction_id}")
def prediction_report(prediction_id: str, user=Depends(get_current_user)):
    return report_service.get_prediction_report(prediction_id, user["username"])


@router.get("/athlete/{athlete_id}")
def athlete_report(athlete_id: str, user=Depends(get_current_user)):
    return report_service.get_athlete_report(athlete_id, user["username"])

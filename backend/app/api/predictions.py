"""Prediction endpoints. Scoped to the requesting researcher."""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user
from app.schemas.prediction import PredictionRequest
from app.services import prediction_service

router = APIRouter(prefix="/api", tags=["predictions"])


@router.post("/predictions", status_code=201)
def create_prediction(payload: PredictionRequest, user=Depends(get_current_user)):
    return prediction_service.create_prediction(payload, user["username"])


@router.get("/predictions")
def list_predictions(athlete_id: Optional[str] = Query(None), user=Depends(get_current_user)):
    return prediction_service.list_predictions(user["username"], athlete_id)


@router.get("/predictions/{prediction_id}")
def get_prediction(prediction_id: str, user=Depends(get_current_user)):
    return prediction_service.get_prediction(prediction_id, user["username"])


@router.get("/athletes/{athlete_id}/predictions")
def get_athlete_predictions(athlete_id: str, user=Depends(get_current_user)):
    return prediction_service.list_predictions(user["username"], athlete_id)

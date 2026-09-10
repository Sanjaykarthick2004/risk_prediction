"""SHAP explainability endpoints. Global/dependence are shared (one model); per-prediction
detail is scoped to the researcher who owns that prediction.
"""
from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.services import shap_service

router = APIRouter(prefix="/api/explainability", tags=["explainability"])


@router.get("/global")
def global_explanation(_user=Depends(get_current_user)):
    return shap_service.get_global_explanation()


@router.get("/{prediction_id}")
def prediction_explanation(prediction_id: str, user=Depends(get_current_user)):
    return shap_service.get_prediction_explanation(prediction_id, user["username"])


@router.get("/{prediction_id}/waterfall")
def waterfall(prediction_id: str, user=Depends(get_current_user)):
    return shap_service.get_waterfall_data(prediction_id, user["username"])


@router.get("/dependence/{feature}")
def dependence(feature: str, _user=Depends(get_current_user)):
    return shap_service.get_dependence(feature)

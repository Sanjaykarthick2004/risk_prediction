"""Model evaluation endpoints."""
from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.services import evaluation_service

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


@router.get("/models")
def model_comparison(_user=Depends(get_current_user)):
    return evaluation_service.get_model_comparison()


@router.get("/metrics")
def metrics(_user=Depends(get_current_user)):
    return evaluation_service.get_metrics()


@router.get("/confusion-matrix")
def confusion_matrix(_user=Depends(get_current_user)):
    return evaluation_service.get_confusion_matrix()


@router.get("/roc-curve")
def roc_curve(_user=Depends(get_current_user)):
    return evaluation_service.get_roc_curve()


@router.get("/precision-recall")
def precision_recall(_user=Depends(get_current_user)):
    return evaluation_service.get_precision_recall_curve()


@router.get("/modality-ablation")
def modality_ablation(_user=Depends(get_current_user)):
    return evaluation_service.get_modality_ablation()

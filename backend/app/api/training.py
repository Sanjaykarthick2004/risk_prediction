"""Model-training endpoints."""
from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.services import training_service

router = APIRouter(prefix="/api/training", tags=["training"])


@router.post("/train")
def train_baselines(_user=Depends(get_current_user)):
    return training_service.run_model_comparison()


@router.post("/xgboost")
def train_xgboost_default(_user=Depends(get_current_user)):
    return training_service.run_xgboost_training(n_search_iter=1)


@router.post("/optimize")
def optimize_xgboost(n_iter: int = 30, _user=Depends(get_current_user)):
    return training_service.run_xgboost_training(n_search_iter=n_iter)


@router.post("/ablation")
def modality_ablation(_user=Depends(get_current_user)):
    return training_service.run_modality_ablation()


@router.get("/status")
def training_status(_user=Depends(get_current_user)):
    return training_service.get_status()


@router.post("/auto-select-best-dataset")
def auto_select_best_dataset(n_iter: int = 30, _user=Depends(get_current_user)):
    """Compare every available dataset by accuracy, select the best, and train+persist on it."""
    return training_service.auto_select_best_dataset(n_search_iter=n_iter)

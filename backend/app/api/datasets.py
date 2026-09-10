"""Dataset upload/validation/processing endpoints."""
from fastapi import APIRouter, Depends, UploadFile

from app.core.dependencies import get_current_user
from app.services import dataset_service

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.post("/upload")
async def upload_dataset(file: UploadFile, _user=Depends(get_current_user)):
    return await dataset_service.upload_dataset(file)


@router.get("")
def list_datasets(_user=Depends(get_current_user)):
    return dataset_service.list_datasets()


@router.get("/training-selection")
def get_training_selection(_user=Depends(get_current_user)):
    return dataset_service.get_training_dataset_selection()


@router.get("/active-summary")
def active_summary(_user=Depends(get_current_user)):
    """Viva-ready overview of the dataset that will be used the next time
    training runs: population, actual record/feature counts, class
    distribution, etc. — see dataset_service.get_active_dataset_summary.
    """
    return dataset_service.get_active_dataset_summary()


@router.post("/{dataset_id}/validate")
def validate_dataset(dataset_id: str, _user=Depends(get_current_user)):
    return dataset_service.validate_uploaded_dataset(dataset_id)


@router.post("/{dataset_id}/process")
def process_dataset(dataset_id: str, _user=Depends(get_current_user)):
    return dataset_service.process_uploaded_dataset(dataset_id)


@router.post("/{dataset_id}/select-for-training")
def select_for_training(dataset_id: str, _user=Depends(get_current_user)):
    return dataset_service.select_dataset_for_training(dataset_id)


@router.post("/reset-training-selection")
def reset_training_selection(_user=Depends(get_current_user)):
    """Switch back to the default Trained Data (bundled synthetic dataset) for the next training run."""
    return dataset_service.reset_training_dataset_selection()

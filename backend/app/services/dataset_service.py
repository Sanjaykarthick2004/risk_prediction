"""Dataset upload, validation, and processing service."""
import io
import json
import logging
import os
from typing import List

import pandas as pd
from fastapi import HTTPException, UploadFile

from app.config import settings
from app.ml import feature_engineering, multimodal_fusion
from app.ml.data_loader import TARGET_COLUMN, load_raw_data
from app.ml.preprocessing import clean_dataset
from app.ml.validation import validate_dataset
from app.services import training_dataset_service
from app.utils.helpers import new_id

logger = logging.getLogger(__name__)

DATASETS_DIR = os.path.join(os.path.dirname(settings.raw_data_path), "uploads")
PROCESSED_DIR = os.path.dirname(settings.processed_data_path)


def _read_dataframe(filename: str, content: bytes) -> pd.DataFrame:
    # keep_default_na=False: `previous_injury_type` legitimately uses the
    # literal string "None" as a category; pandas' default NA-string list
    # would otherwise silently turn that into a fake missing value.
    if filename.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(content), keep_default_na=False, na_values=[""])
    if filename.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(content), keep_default_na=False, na_values=[""])
    raise HTTPException(status_code=400, detail="Unsupported file type. Upload a .csv or .xlsx file.")


def _meta_path(dataset_id: str) -> str:
    return os.path.join(DATASETS_DIR, f"{dataset_id}.meta.json")


def _processed_path(dataset_id: str) -> str:
    return os.path.join(PROCESSED_DIR, f"{dataset_id}_processed.csv")


def _preview_records(df: pd.DataFrame, n: int = 10) -> List[dict]:
    """Small JSON-safe preview (NaN -> null) — never the full dataset."""
    return json.loads(df.head(n).to_json(orient="records"))


async def upload_dataset(file: UploadFile) -> dict:
    content = await file.read()
    try:
        df = _read_dataframe(file.filename, content)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Could not parse file: {exc}") from exc

    os.makedirs(DATASETS_DIR, exist_ok=True)
    dataset_id = new_id("DS")
    path = os.path.join(DATASETS_DIR, f"{dataset_id}.csv")
    df.to_csv(path, index=False)

    with open(_meta_path(dataset_id), "w") as f:
        json.dump({"dataset_id": dataset_id, "filename": file.filename}, f)

    return {
        "dataset_id": dataset_id,
        "filename": file.filename,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "preview_rows": _preview_records(df),
    }


def list_datasets() -> List[dict]:
    if not os.path.exists(DATASETS_DIR):
        return []
    datasets = []
    for fname in sorted(os.listdir(DATASETS_DIR)):
        if fname.endswith(".csv"):
            dataset_id = fname.replace(".csv", "")
            path = os.path.join(DATASETS_DIR, fname)
            df = pd.read_csv(path, keep_default_na=False, na_values=[""])
            datasets.append({"dataset_id": dataset_id, "rows": len(df), "columns": len(df.columns)})
    return datasets


def _dataset_path(dataset_id: str) -> str:
    path = os.path.join(DATASETS_DIR, f"{dataset_id}.csv")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
    return path


def _dataset_filename(dataset_id: str) -> str:
    try:
        with open(_meta_path(dataset_id)) as f:
            return json.load(f).get("filename", f"{dataset_id}.csv")
    except FileNotFoundError:
        return f"{dataset_id}.csv"


def _categorize_validation(report: dict) -> dict:
    """Light categorization of the messages validate_dataset() already produced —
    does not re-run or duplicate any validation logic, just groups the existing
    errors/warnings under the checklist headings a reader expects to see.
    """
    text = " ".join(report["errors"] + report["warnings"]).lower()

    def status(is_error_kind: bool, is_warn_kind: bool) -> str:
        if is_error_kind:
            return "FAIL"
        if is_warn_kind:
            return "WARN"
        return "PASS"

    return {
        "required_columns": status("missing required columns" in text, False),
        "data_types": status("non-numeric values" in text or "negative values" in text, False),
        "value_ranges": status(False, "out-of-range" in text),
        "categories": status(False, "unrecognized categorical" in text),
    }


def validate_uploaded_dataset(dataset_id: str) -> dict:
    df = pd.read_csv(_dataset_path(dataset_id), keep_default_na=False, na_values=[""])
    report = validate_dataset(df, require_target=False)
    result = report.to_dict()
    result["summary"] = _categorize_validation(result)
    return result


def process_uploaded_dataset(dataset_id: str) -> dict:
    df = pd.read_csv(_dataset_path(dataset_id), keep_default_na=False, na_values=[""])
    rows_before = len(df)
    df = clean_dataset(df)
    df = feature_engineering.add_engineered_features(df)

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    processed_path = _processed_path(dataset_id)
    df.to_csv(processed_path, index=False)

    return {
        "dataset_id": dataset_id,
        "rows_before": rows_before,
        "rows_after": len(df),
        "duplicates_removed": rows_before - len(df),
        "missing_values_after_cleaning": int(df.isna().sum().sum()),
        "columns_after_processing": list(df.columns),
        "engineered_features": feature_engineering.ENGINEERED_FEATURES,
        "has_target_column": TARGET_COLUMN in df.columns,
        "processed_path": processed_path,
    }


def select_dataset_for_training(dataset_id: str) -> dict:
    processed_path = _processed_path(dataset_id)
    if not os.path.exists(processed_path):
        raise HTTPException(
            status_code=409,
            detail="This dataset hasn't been processed yet. Run Process before selecting it for training.",
        )

    df = pd.read_csv(processed_path, keep_default_na=False, na_values=[""])
    if TARGET_COLUMN not in df.columns:
        raise HTTPException(
            status_code=400,
            detail=f"This dataset has no '{TARGET_COLUMN}' column, so it cannot be used for training.",
        )

    filename = _dataset_filename(dataset_id)
    training_dataset_service.select_dataset(dataset_id=dataset_id, filename=filename, path=processed_path)
    return {"message": f"'{filename}' selected as the training dataset.", **training_dataset_service.get_active_dataset_info()}


def get_training_dataset_selection() -> dict:
    return training_dataset_service.get_active_dataset_info()


def reset_training_dataset_selection() -> dict:
    training_dataset_service.clear_selection()
    return {"message": "Reverted to Trained Data.", **training_dataset_service.get_active_dataset_info()}


def list_trainable_datasets() -> List[dict]:
    """The synthetic default, plus every uploaded dataset that has been processed
    and has the target column — i.e. every dataset that COULD be trained on.
    """
    candidates = [{"source": "synthetic", "dataset_id": None, "filename": training_dataset_service.SYNTHETIC_LABEL, "path": None}]
    if not os.path.exists(PROCESSED_DIR):
        return candidates

    for fname in sorted(os.listdir(PROCESSED_DIR)):
        if not fname.endswith("_processed.csv"):
            continue
        dataset_id = fname.replace("_processed.csv", "")
        path = os.path.join(PROCESSED_DIR, fname)
        try:
            columns = pd.read_csv(path, nrows=1, keep_default_na=False, na_values=[""]).columns
        except Exception:  # noqa: BLE001
            continue
        if TARGET_COLUMN not in columns:
            continue
        candidates.append({
            "source": "uploaded", "dataset_id": dataset_id,
            "filename": _dataset_filename(dataset_id), "path": path,
        })
    return candidates


def get_active_dataset_summary() -> dict:
    """Everything the Dataset page needs for a viva-ready summary of the
    dataset that will be used the NEXT time training runs: actual record/
    feature counts, missing values, duplicates, and class distribution,
    computed live from the data every time — never hardcoded.
    """
    active = training_dataset_service.get_active_dataset_info()
    df = load_raw_data(path=active["path"])
    report = validate_dataset(df, require_target=TARGET_COLUMN in df.columns)

    return {
        "dataset_name": active["label"],
        "source": active["source"],
        "population": "Running Athletes",
        "n_records": report.stats["n_rows"],
        "n_features": report.stats["n_columns"] - (1 if TARGET_COLUMN in df.columns else 0),
        "n_missing_values": report.stats["n_missing_values"],
        "n_duplicate_rows": report.stats["n_duplicate_rows"],
        "class_distribution": report.stats["target_distribution"],
        "n_modalities": len(multimodal_fusion.MODALITY_FEATURES),
        "target_column": TARGET_COLUMN,
        "is_valid": report.is_valid,
    }

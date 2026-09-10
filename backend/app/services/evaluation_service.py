"""Evaluation service: reads persisted metrics and recomputes curves from the
persisted model + a deterministic re-split of the raw data (same random_state
as training, so the test set is reproduced exactly).
"""
import json
import os

import joblib
import pandas as pd
from fastapi import HTTPException
from sklearn.metrics import precision_recall_curve, roc_curve

from app.config import settings
from app.ml import evaluate, preprocessing
from app.ml.data_loader import load_raw_data
from app.ml.prediction import ModelNotTrainedError, _load_artifacts
from app.services import training_service


def _require_metrics_file():
    if not os.path.exists(settings.model_metrics_path):
        raise HTTPException(status_code=409, detail="No trained model found. Run XGBoost training first.")


def get_model_comparison() -> dict:
    path = os.path.join(settings.metrics_dir, "model_comparison.csv")
    if not os.path.exists(path):
        raise HTTPException(status_code=409, detail="No model comparison results found. Run POST /api/training/train first.")
    df = pd.read_csv(path)
    return {"models": df.to_dict(orient="records")}


def get_metrics() -> dict:
    _require_metrics_file()
    with open(settings.model_metrics_path) as f:
        return json.load(f)


def _recompute_test_predictions():
    try:
        model, preprocessor, columns, _ = _load_artifacts()
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    df = load_raw_data(path=training_service.get_trained_dataset_path())
    data = preprocessing.prepare_dataset(df)  # same random_state -> same split as training
    y_test = data["y_test"]
    y_proba = model.predict_proba(data["X_test"])[:, 1]
    y_pred = model.predict(data["X_test"])
    return y_test, y_pred, y_proba


def get_confusion_matrix() -> dict:
    y_test, y_pred, _ = _recompute_test_predictions()
    cm = evaluate.get_confusion_matrix(y_test, y_pred)
    return {"matrix": cm.tolist(), "labels": ["No Injury (0)", "Injury (1)"]}


def _finite(value: float) -> float:
    """sklearn's roc_curve/precision_recall_curve emit inf sentinel thresholds; JSON has no inf."""
    if value == float("inf"):
        return 1.0
    if value == float("-inf"):
        return 0.0
    return round(float(value), 4)


def get_roc_curve() -> dict:
    y_test, _, y_proba = _recompute_test_predictions()
    fpr, tpr, thresholds = roc_curve(y_test, y_proba)
    return {
        "fpr": [round(float(v), 4) for v in fpr],
        "tpr": [round(float(v), 4) for v in tpr],
        "thresholds": [_finite(v) for v in thresholds],
    }


def get_precision_recall_curve() -> dict:
    y_test, _, y_proba = _recompute_test_predictions()
    precision, recall, thresholds = precision_recall_curve(y_test, y_proba)
    return {
        "precision": [round(float(v), 4) for v in precision],
        "recall": [round(float(v), 4) for v in recall],
        "thresholds": [_finite(v) for v in thresholds],
    }


def get_modality_ablation() -> dict:
    path = os.path.join(settings.metrics_dir, "modality_ablation_results.csv")
    if not os.path.exists(path):
        raise HTTPException(status_code=409, detail="No ablation results found. Run POST /api/training/ablation first.")
    df = pd.read_csv(path)
    return {"results": df.to_dict(orient="records")}

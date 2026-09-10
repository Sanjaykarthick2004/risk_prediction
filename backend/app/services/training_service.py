"""Training orchestration: model comparison and XGBoost training/optimization.

Kept simple for a college project — training runs synchronously inside the
request and updates an in-memory status dict the frontend can poll.
"""
import json
import logging
import os
from datetime import datetime
from typing import Optional

from xgboost import XGBClassifier

from app.config import settings
from app.ml import ablation, evaluate, preprocessing, train_models, train_xgboost
from app.ml.data_loader import load_raw_data
from app.ml.prediction import clear_artifact_cache
from app.ml.train_models import maybe_apply_smote
from app.services import dataset_service, training_dataset_service

logger = logging.getLogger(__name__)

_status = {"state": "idle", "last_action": None, "detail": None}


def _read_model_metrics() -> Optional[dict]:
    if not os.path.exists(settings.model_metrics_path):
        return None
    with open(settings.model_metrics_path) as f:
        return json.load(f)


def get_trained_dataset_path() -> Optional[str]:
    """The dataset path the CURRENTLY PERSISTED model was actually trained on
    (None means the default synthetic dataset). Evaluation/SHAP recomputation
    must use this — not the live "selected for next run" pointer — so results
    always match the model that's actually sitting on disk.
    """
    metrics = _read_model_metrics()
    if not metrics:
        return None
    return metrics.get("dataset_used", {}).get("path")


def get_status() -> dict:
    model_trained = os.path.exists(settings.model_path)
    metrics = _read_model_metrics()
    evaluation_available = os.path.exists(os.path.join(settings.metrics_dir, "model_comparison.csv")) or metrics is not None

    _status["model_artifacts_present"] = model_trained
    _status["model_version"] = settings.model_version
    _status["trained_at"] = metrics.get("trained_at") if metrics else None
    _status["trained_dataset"] = metrics.get("dataset_used") if metrics else None
    _status["selected_dataset"] = training_dataset_service.get_active_dataset_info()
    _status["workflow"] = {
        "dataset_ready": True,  # synthetic data is always available as a fallback
        "model_trained": model_trained,
        "evaluation_available": evaluation_available,
        "prediction_ready": model_trained,
        "shap_available": model_trained,
    }
    return _status


def run_model_comparison() -> dict:
    _status.update(state="running", last_action="model_comparison")
    try:
        active = training_dataset_service.get_active_dataset_info()
        results_df, _, _ = train_models.run_model_comparison(data_path=active["path"])
        result = results_df.reset_index().to_dict(orient="records")
        _status.update(state="completed", detail=f"Compared {len(result)} models")
        return {"models": result, "dataset_used": active}
    except Exception as exc:  # noqa: BLE001
        _status.update(state="failed", detail=str(exc))
        raise


def run_modality_ablation() -> dict:
    _status.update(state="running", last_action="modality_ablation")
    try:
        active = training_dataset_service.get_active_dataset_info()
        results_df = ablation.run_modality_ablation(data_path=active["path"])
        result = results_df.reset_index().to_dict(orient="records")
        _status.update(state="completed", detail=f"Ablation across {len(result)} modality configurations")
        return {"results": result, "dataset_used": active}
    except Exception as exc:  # noqa: BLE001
        _status.update(state="failed", detail=str(exc))
        raise


def run_xgboost_training(n_search_iter: int = 30) -> dict:
    _status.update(state="running", last_action="xgboost_training")
    try:
        active = training_dataset_service.get_active_dataset_info()
        result = train_xgboost.train_and_persist(
            n_search_iter=n_search_iter, data_path=active["path"], dataset_label=active["label"],
        )
        clear_artifact_cache()
        _status.update(state="completed", detail="XGBoost trained, optimized, and persisted")
        return result
    except Exception as exc:  # noqa: BLE001
        _status.update(state="failed", detail=str(exc))
        raise


def _quick_accuracy_check(candidate: dict) -> dict:
    """A fast, un-tuned XGBoost fit — just to RANK candidate datasets by accuracy.
    Not the model that gets persisted; see auto_select_best_dataset() for that.
    """
    df = load_raw_data(path=candidate["path"])
    data = preprocessing.prepare_dataset(df)
    X_train_bal, y_train_bal, _ = maybe_apply_smote(data["X_train"], data["y_train"])

    model = XGBClassifier(
        n_estimators=200, max_depth=5, learning_rate=0.08, random_state=settings.random_state,
        eval_metric="logloss",
    )
    model.fit(X_train_bal, y_train_bal)
    y_pred = model.predict(data["X_test"])
    y_proba = model.predict_proba(data["X_test"])[:, 1]
    metrics = evaluate.compute_metrics(data["y_test"], y_pred, y_proba)
    return {**candidate, **metrics, "n_rows": int(len(df))}


def auto_select_best_dataset(n_search_iter: int = 30) -> dict:
    """Quickly compare every available dataset (synthetic + all uploaded/processed
    ones with a target column) by accuracy, select whichever scores best, then run
    the FULL train-and-optimize pipeline on that winner so the persisted model is
    properly tuned — not just the quick comparison fit.
    """
    _status.update(state="running", last_action="auto_select_best_dataset")
    try:
        candidates = dataset_service.list_trainable_datasets()
        results = []
        for candidate in candidates:
            try:
                results.append(_quick_accuracy_check(candidate))
            except Exception as exc:  # noqa: BLE001
                results.append({**candidate, "error": str(exc)})

        scored = [r for r in results if "accuracy" in r]
        if not scored:
            raise RuntimeError("No trainable datasets available for comparison.")
        best = max(scored, key=lambda r: r["accuracy"])

        if best["source"] == "synthetic":
            training_dataset_service.clear_selection()
        else:
            training_dataset_service.select_dataset(
                dataset_id=best["dataset_id"], filename=best["filename"], path=best["path"],
            )

        training_result = run_xgboost_training(n_search_iter=n_search_iter)
        _status.update(state="completed", detail=f"Selected '{best['filename']}' (accuracy={best['accuracy']}) and retrained on it")
        return {"candidates": results, "selected": best, "training_result": training_result}
    except Exception as exc:  # noqa: BLE001
        _status.update(state="failed", detail=str(exc))
        raise

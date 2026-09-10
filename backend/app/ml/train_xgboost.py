"""Train, optimize, evaluate, and persist the final XGBoost model + preprocessing pipeline + SHAP explainer.

This is the single script that produces every artifact used by the
prediction API: models/xgboost_model.pkl, preprocessing_pipeline.pkl,
feature_columns.pkl, shap_explainer.pkl, model_metrics.json.
"""
import json
import logging
import os
import time

import joblib
import shap
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.model_selection import StratifiedKFold, cross_validate
from xgboost import XGBClassifier

from app.config import settings
from app.ml import evaluate, hyperparameter_tuning, preprocessing
from app.ml.data_loader import load_raw_data
from app.ml.train_models import maybe_apply_smote
from app.utils.helpers import utcnow

logger = logging.getLogger(__name__)

CV_SCORING = ["accuracy", "precision", "recall", "f1", "roc_auc", "average_precision"]


def cross_validate_model(model, X, y, cv_folds: int = 5, apply_smote: bool = False):
    """5-fold CV report for the final model, on the ORIGINAL (unbalanced) X/y.

    When `apply_smote` is True, SMOTE is applied fresh inside each fold via
    a pipeline (never on already-resampled data) — see hyperparameter_tuning.py
    for why that matters. `model` may already be fitted; cross_validate()
    clones it (resetting to its hyperparameters, unfitted) before each fold.
    """
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=settings.random_state)
    if apply_smote:
        estimator = ImbPipeline([("smote", SMOTE(random_state=settings.random_state)), ("clf", model)])
    else:
        estimator = model
    scores = cross_validate(estimator, X, y, cv=cv, scoring=CV_SCORING)
    summary = {}
    for metric in CV_SCORING:
        vals = scores[f"test_{metric}"]
        summary[metric] = {"mean": round(float(vals.mean()), 4), "std": round(float(vals.std()), 4)}
    return summary


def train_and_persist(n_search_iter: int = 30, data_path: str = None, dataset_label: str = None):
    training_started = time.monotonic()
    df = load_raw_data(path=data_path)
    data = preprocessing.prepare_dataset(df)
    X_train, X_test = data["X_train"], data["X_test"]
    y_train, y_test = data["y_train"], data["y_test"]
    feature_names = data["feature_names"]

    X_train_bal, y_train_bal, smote_applied = maybe_apply_smote(X_train, y_train)

    # Default XGBoost (baseline for the optimization experiment)
    default_model = XGBClassifier(
        n_estimators=300, max_depth=5, learning_rate=0.05, subsample=0.8,
        colsample_bytree=0.8, random_state=settings.random_state, eval_metric="logloss",
    )
    default_model.fit(X_train_bal, y_train_bal)
    default_pred = default_model.predict(X_test)
    default_proba = default_model.predict_proba(X_test)[:, 1]
    default_metrics = evaluate.compute_metrics(y_test, default_pred, default_proba)

    # Hyperparameter-optimized XGBoost — tuned on the ORIGINAL (unbalanced)
    # training split; SMOTE (if used) is applied fresh inside each CV fold
    # by tune_xgboost itself, avoiding synthetic-sample leakage across folds.
    best_model, best_params, best_cv_f1 = hyperparameter_tuning.tune_xgboost(
        X_train, y_train, n_iter=n_search_iter, apply_smote=smote_applied,
    )
    best_pred = best_model.predict(X_test)
    best_proba = best_model.predict_proba(X_test)[:, 1]
    optimized_metrics = evaluate.compute_metrics(y_test, best_pred, best_proba)

    cv_summary = cross_validate_model(best_model, X_train, y_train, apply_smote=smote_applied)

    # Persist artifacts
    os.makedirs(os.path.dirname(settings.model_path), exist_ok=True)
    joblib.dump(best_model, settings.model_path)
    joblib.dump(data["preprocessor"], settings.preprocessing_path)
    joblib.dump({"feature_names": feature_names, "raw_feature_columns": data["raw_feature_columns"]}, settings.feature_columns_path)

    explainer = shap.TreeExplainer(best_model)
    joblib.dump(explainer, settings.shap_path)

    metrics_payload = {
        "model_version": settings.model_version,
        "trained_at": utcnow().isoformat(),
        "dataset_used": {
            "source": "uploaded" if data_path else "synthetic",
            "label": dataset_label or "Trained Data",
            "path": data_path,
        },
        "default_xgboost": default_metrics,
        "optimized_xgboost": optimized_metrics,
        "best_params": best_params,
        "best_cv_f1_during_search": round(float(best_cv_f1), 4),
        "cross_validation_5fold": cv_summary,
        "smote_applied": smote_applied,
        "cv_methodology": (
            "SMOTE is applied fresh inside each cross-validation fold (imblearn "
            "Pipeline), not once before splitting, so synthetic minority samples "
            "cannot leak across a fold's train/validation boundary."
        ),
        "n_train": int(len(y_train_bal)),
        "n_test": int(len(y_test)),
        "training_time_seconds": round(time.monotonic() - training_started, 1),
    }
    os.makedirs(os.path.dirname(settings.model_metrics_path), exist_ok=True)
    with open(settings.model_metrics_path, "w") as f:
        json.dump(metrics_payload, f, indent=2)

    logger.info("Default XGBoost: %s", default_metrics)
    logger.info("Optimized XGBoost: %s", optimized_metrics)
    return metrics_payload


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = train_and_persist()
    print(json.dumps(result, indent=2))

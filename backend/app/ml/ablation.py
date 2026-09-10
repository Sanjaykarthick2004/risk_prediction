"""Modality-ablation experiment: train XGBoost on cumulative modality subsets
(M1..M6) and compare F1 / Recall / ROC-AUC / PR-AUC to see whether adding
modalities improves injury-risk prediction.
"""
import json
import logging
import os

import pandas as pd
from xgboost import XGBClassifier

from app.config import settings
from app.ml import evaluate, multimodal_fusion, preprocessing
from app.ml.data_loader import load_raw_data
from app.ml.train_models import maybe_apply_smote

logger = logging.getLogger(__name__)


def run_modality_ablation(save_outputs: bool = True, data_path: str = None) -> pd.DataFrame:
    df = load_raw_data(path=data_path)
    results = []

    for config_name, modalities in multimodal_fusion.ABLATION_CONFIGS.items():
        data = preprocessing.prepare_dataset(df, modalities=modalities)
        X_train, X_test = data["X_train"], data["X_test"]
        y_train, y_test = data["y_train"], data["y_test"]
        X_train_bal, y_train_bal, _ = maybe_apply_smote(X_train, y_train)

        model = XGBClassifier(
            n_estimators=300, max_depth=5, learning_rate=0.05, subsample=0.8,
            colsample_bytree=0.8, random_state=settings.random_state, eval_metric="logloss",
        )
        model.fit(X_train_bal, y_train_bal)
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        metrics = evaluate.compute_metrics(y_test, y_pred, y_proba)
        metrics["modality_configuration"] = config_name
        metrics["modalities"] = "+".join(modalities)
        results.append(metrics)
        logger.info("%s: %s", config_name, metrics)

    results_df = pd.DataFrame(results).set_index("modality_configuration")
    results_df = results_df[["modalities", "f1_score", "recall", "roc_auc", "pr_auc", "accuracy", "precision", "specificity"]]

    if save_outputs:
        os.makedirs(settings.metrics_dir, exist_ok=True)
        results_df.to_csv(os.path.join(settings.metrics_dir, "modality_ablation_results.csv"))

    return results_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = run_modality_ablation()
    print(res)

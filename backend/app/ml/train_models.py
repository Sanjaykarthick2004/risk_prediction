"""Baseline model comparison: LR, Decision Tree, Random Forest, SVM,
Gradient Boosting, and default XGBoost — all evaluated on an identical held-out test set.
"""
import json
import logging
import os

import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

from app.config import settings
from app.ml import evaluate, preprocessing
from app.ml.data_loader import load_raw_data

logger = logging.getLogger(__name__)

# Kernel SVMs scale poorly with training-set size (roughly quadratic or
# worse). On a normal college laptop, fitting SVC on the full SMOTE-balanced
# training set (which can be 10,000+ rows once the dataset is large) can
# take several minutes. To keep the app responsive, SVM alone is trained on
# a stratified random subsample capped at this size — every other model in
# the comparison, and the shared held-out test set, are unaffected. This is
# a documented practical accommodation, not a change to the evaluation
# methodology: SVM is still scored on the identical test split as everyone else.
MAX_SVM_TRAIN_SIZE = 4000

MODEL_FACTORY = {
    "Logistic Regression": lambda: LogisticRegression(max_iter=1000, random_state=settings.random_state),
    "Decision Tree": lambda: DecisionTreeClassifier(random_state=settings.random_state),
    "Random Forest": lambda: RandomForestClassifier(n_estimators=200, random_state=settings.random_state),
    "SVM": lambda: SVC(probability=True, random_state=settings.random_state),
    "Gradient Boosting": lambda: GradientBoostingClassifier(random_state=settings.random_state),
    "XGBoost": lambda: XGBClassifier(
        n_estimators=300, max_depth=5, learning_rate=0.05, subsample=0.8,
        colsample_bytree=0.8, random_state=settings.random_state, eval_metric="logloss",
    ),
}


def maybe_apply_smote(X_train, y_train):
    counts = np.bincount(y_train)
    minority_ratio = counts.min() / counts.sum()
    if minority_ratio < 0.4:
        logger.info("Class imbalance detected (minority ratio=%.2f). Applying SMOTE to training data only.", minority_ratio)
        sm = SMOTE(random_state=settings.random_state)
        X_res, y_res = sm.fit_resample(X_train, y_train)
        return X_res, y_res, True
    return X_train, y_train, False


def run_model_comparison(modalities=None, save_outputs: bool = True, data_path: str = None):
    df = load_raw_data(path=data_path)
    data = preprocessing.prepare_dataset(df, modalities=modalities)
    X_train, X_test = data["X_train"], data["X_test"]
    y_train, y_test = data["y_train"], data["y_test"]

    X_train_bal, y_train_bal, smote_applied = maybe_apply_smote(X_train, y_train)

    results = []
    trained_models = {}
    for name, factory in MODEL_FACTORY.items():
        model = factory()
        if name == "SVM" and len(y_train_bal) > MAX_SVM_TRAIN_SIZE:
            X_fit, _, y_fit, _ = train_test_split(
                X_train_bal, y_train_bal, train_size=MAX_SVM_TRAIN_SIZE,
                stratify=y_train_bal, random_state=settings.random_state,
            )
        else:
            X_fit, y_fit = X_train_bal, y_train_bal
        model.fit(X_fit, y_fit)
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        metrics = evaluate.compute_metrics(y_test, y_pred, y_proba)
        metrics["model"] = name
        results.append(metrics)
        trained_models[name] = model

    results_df = pd.DataFrame(results).set_index("model")
    results_df = results_df[["accuracy", "precision", "recall", "f1_score", "roc_auc", "pr_auc", "specificity"]]

    if save_outputs:
        os.makedirs(settings.metrics_dir, exist_ok=True)
        results_df.to_csv(os.path.join(settings.metrics_dir, "model_comparison.csv"))
        with open(os.path.join(settings.metrics_dir, "model_comparison_meta.json"), "w") as f:
            json.dump({"smote_applied": smote_applied, "n_train": int(len(y_train_bal)), "n_test": int(len(y_test))}, f, indent=2)

    return results_df, trained_models, data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df_results, _, _ = run_model_comparison()
    print(df_results)

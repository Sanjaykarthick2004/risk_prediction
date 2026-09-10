"""SHAP explainability helpers built on the persisted TreeExplainer + XGBoost model.

IMPORTANT: SHAP values describe how each feature moved the model's own
prediction. They must never be described as proof that a feature causes
injury — only that it "contributed positively/negatively to the model's
prediction".
"""
import logging
from typing import Dict, List

import numpy as np

logger = logging.getLogger(__name__)


def global_feature_importance(explainer, X, feature_names: List[str], top_n: int = 15) -> List[Dict]:
    shap_values = explainer.shap_values(X)
    mean_abs = np.abs(shap_values).mean(axis=0)
    order = np.argsort(mean_abs)[::-1][:top_n]
    return [{"feature": feature_names[i], "mean_abs_shap": round(float(mean_abs[i]), 5)} for i in order]


def local_explanation(explainer, x_row, feature_names: List[str], feature_values: List, top_n: int = 10) -> Dict:
    """x_row: 1-row 2D array (already preprocessed). Returns positive/negative contributors."""
    shap_values = explainer.shap_values(x_row)
    values = shap_values[0]
    base_value = explainer.expected_value
    if isinstance(base_value, (list, np.ndarray)):
        base_value = float(np.ravel(base_value)[0])

    contributions = [
        {"feature": feature_names[i], "feature_value": feature_values[i], "shap_value": round(float(values[i]), 5)}
        for i in range(len(feature_names))
    ]
    positive = sorted([c for c in contributions if c["shap_value"] > 0], key=lambda c: -c["shap_value"])[:top_n]
    negative = sorted([c for c in contributions if c["shap_value"] < 0], key=lambda c: c["shap_value"])[:top_n]

    return {
        "base_value": round(float(base_value), 5),
        "positive_contributors": positive,
        "negative_contributors": negative,
        "all_contributions": contributions,
    }


def dependence_values(explainer, X, feature_names: List[str], feature: str) -> Dict:
    if feature not in feature_names:
        raise ValueError(f"Unknown feature '{feature}'")
    idx = feature_names.index(feature)
    shap_values = explainer.shap_values(X)
    feature_column = X[:, idx] if not hasattr(X, "iloc") else X.iloc[:, idx].values
    return {
        "feature": feature,
        "feature_values": [round(float(v), 4) for v in feature_column],
        "shap_values": [round(float(v), 5) for v in shap_values[:, idx]],
    }

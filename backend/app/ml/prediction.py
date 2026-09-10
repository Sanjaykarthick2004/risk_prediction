"""End-to-end single-athlete prediction pipeline.

Assessment input (nested modality dicts, matching app.schemas.assessment)
        -> flatten to one row
        -> feature engineering (same logic as training)
        -> preprocessing pipeline (loaded, already fit at training time)
        -> XGBoost probability
        -> risk classification
        -> SHAP local explanation
"""
import logging
from functools import lru_cache
from typing import Dict

import joblib
import pandas as pd

from app.config import settings
from app.ml import feature_engineering, shap_explainer

logger = logging.getLogger(__name__)


class ModelNotTrainedError(Exception):
    pass


@lru_cache(maxsize=1)
def _load_artifacts():
    try:
        model = joblib.load(settings.model_path)
        preprocessor = joblib.load(settings.preprocessing_path)
        columns = joblib.load(settings.feature_columns_path)
        explainer = joblib.load(settings.shap_path)
    except FileNotFoundError as exc:
        raise ModelNotTrainedError(
            "Model artifacts not found. Train the model first (POST /api/training/xgboost)."
        ) from exc
    return model, preprocessor, columns, explainer


def clear_artifact_cache():
    _load_artifacts.cache_clear()


def flatten_assessment(demographic: Dict, training: Dict, physiological: Dict, recovery: Dict,
                        lifestyle: Dict, injury_history: Dict) -> pd.DataFrame:
    row = {**demographic, **training, **physiological, **recovery, **lifestyle, **injury_history}
    return pd.DataFrame([row])


def classify_risk(probability: float) -> str:
    if probability < settings.risk_threshold_low:
        return "LOW"
    if probability < settings.risk_threshold_medium:
        return "MEDIUM"
    return "HIGH"


def predict(demographic: Dict, training: Dict, physiological: Dict, recovery: Dict,
            lifestyle: Dict, injury_history: Dict) -> Dict:
    model, preprocessor, columns, explainer = _load_artifacts()
    feature_names = columns["feature_names"]
    raw_feature_columns = columns["raw_feature_columns"]

    df_row = flatten_assessment(demographic, training, physiological, recovery, lifestyle, injury_history)
    df_row = feature_engineering.add_engineered_features(df_row)
    df_row = df_row[[c for c in raw_feature_columns if c in df_row.columns]]

    X = preprocessor.transform(df_row)
    probability = float(model.predict_proba(X)[0, 1])
    risk_level = classify_risk(probability)

    explanation = shap_explainer.local_explanation(
        explainer, X, feature_names, feature_values=[round(float(v), 4) for v in X[0]],
    )

    return {
        "probability": round(probability, 4),
        "risk_level": risk_level,
        "model_version": settings.model_version,
        "top_risk_factors": explanation["positive_contributors"],
        "protective_factors": explanation["negative_contributors"],
        "shap_base_value": explanation["base_value"],
        "shap_contributions": explanation["all_contributions"],
    }

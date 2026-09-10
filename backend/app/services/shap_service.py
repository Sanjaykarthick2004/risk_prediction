"""SHAP explainability service: global importance, per-prediction detail, dependence."""
from fastapi import HTTPException

from app.config import settings
from app.database.mongodb import predictions_collection, shap_explanations_collection
from app.ml import preprocessing, shap_explainer
from app.ml.data_loader import load_raw_data
from app.ml.prediction import ModelNotTrainedError, _load_artifacts
from app.services import training_service


def get_global_explanation(sample_size: int = None) -> dict:
    """Global SHAP importance over a SAMPLE of the test split, not the whole
    (possibly 10,000+ row) dataset — recomputing SHAP values for every row on
    every page load would be needlessly expensive. `sample_size` defaults to
    `settings.shap_global_sample_size` (documented, configurable). Individual
    predictions (get_prediction_explanation) always use the specific
    athlete's own feature vector, never this sample.
    """
    sample_size = sample_size if sample_size is not None else settings.shap_global_sample_size
    try:
        _, _, columns, explainer = _load_artifacts()
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    df = load_raw_data(path=training_service.get_trained_dataset_path())
    data = preprocessing.prepare_dataset(df)
    X_sample = data["X_test"][:sample_size]
    importance = shap_explainer.global_feature_importance(explainer, X_sample, columns["feature_names"])
    return {"feature_importance": importance, "n_samples_used": int(len(X_sample))}


def get_prediction_explanation(prediction_id: str, owner: str) -> dict:
    prediction = predictions_collection.find_one({"prediction_id": prediction_id, "created_by": owner}, {"_id": 0})
    if not prediction:
        raise HTTPException(status_code=404, detail=f"Prediction '{prediction_id}' not found")

    shap_docs = list(shap_explanations_collection.find({"prediction_id": prediction_id}, {"_id": 0}))
    return {
        "prediction_id": prediction_id,
        "probability": prediction["probability"],
        "risk_level": prediction["risk_level"],
        "top_risk_factors": prediction["top_risk_factors"],
        "protective_factors": prediction["protective_factors"],
        "all_contributions": shap_docs,
    }


def get_waterfall_data(prediction_id: str, owner: str) -> dict:
    explanation = get_prediction_explanation(prediction_id, owner)
    contributions = sorted(explanation["all_contributions"], key=lambda c: -abs(c["shap_value"]))
    return {
        "prediction_id": prediction_id,
        "probability": explanation["probability"],
        "risk_level": explanation["risk_level"],
        "contributions_by_magnitude": contributions,
    }


def get_dependence(feature: str, sample_size: int = None) -> dict:
    sample_size = sample_size if sample_size is not None else settings.shap_global_sample_size
    try:
        _, _, columns, explainer = _load_artifacts()
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    df = load_raw_data(path=training_service.get_trained_dataset_path())
    data = preprocessing.prepare_dataset(df)
    X_sample = data["X_test"][:sample_size]

    try:
        return shap_explainer.dependence_values(explainer, X_sample, columns["feature_names"], feature)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

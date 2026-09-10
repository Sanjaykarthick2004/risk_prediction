"""Prediction service: runs the ML pipeline and stores results in MongoDB. Scoped per owner."""
import logging
from typing import List, Optional

from fastapi import HTTPException

from app.database.mongodb import predictions_collection, shap_explanations_collection
from app.ml.prediction import ModelNotTrainedError, predict as run_prediction
from app.schemas.prediction import PredictionRequest
from app.services.athlete_service import get_athlete
from app.utils.helpers import new_id, utcnow

logger = logging.getLogger(__name__)


def create_prediction(payload: PredictionRequest, owner: str) -> dict:
    athlete = get_athlete(payload.athlete_id, owner)
    demographic = {
        "age": athlete["age"], "gender": athlete["gender"], "sport": athlete["sport"],
        "event_type": athlete["event_type"], "height": athlete["height"], "weight": athlete["weight"],
        "experience_years": athlete["experience_years"],
    }

    try:
        result = run_prediction(
            demographic,
            payload.training.model_dump(),
            payload.physiological.model_dump(),
            payload.recovery.model_dump(),
            payload.lifestyle.model_dump(),
            payload.injury_history.model_dump(),
        )
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    prediction_id = new_id("PRED")
    now = utcnow()
    doc = {
        "prediction_id": prediction_id,
        "athlete_id": payload.athlete_id,
        "assessment_id": payload.assessment_id,
        "created_by": owner,
        "probability": result["probability"],
        "risk_level": result["risk_level"],
        "model_version": result["model_version"],
        "prediction_date": now,
        "top_risk_factors": result["top_risk_factors"],
        "protective_factors": result["protective_factors"],
    }
    predictions_collection.insert_one(dict(doc))

    shap_docs = []
    for contribution in result["shap_contributions"]:
        contribution_type = "risk" if contribution["shap_value"] > 0 else "protective"
        shap_docs.append({
            "prediction_id": prediction_id,
            "feature": contribution["feature"],
            "feature_value": contribution["feature_value"],
            "shap_value": contribution["shap_value"],
            "contribution_type": contribution_type,
        })
    if shap_docs:
        shap_explanations_collection.insert_many(shap_docs)

    return get_prediction(prediction_id, owner)


def list_predictions(owner: str, athlete_id: Optional[str] = None) -> List[dict]:
    query = {"created_by": owner}
    if athlete_id:
        query["athlete_id"] = athlete_id
    cursor = predictions_collection.find(query, {"_id": 0}).sort("prediction_date", -1)
    return list(cursor)


def get_prediction(prediction_id: str, owner: str) -> dict:
    doc = predictions_collection.find_one({"prediction_id": prediction_id, "created_by": owner}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Prediction '{prediction_id}' not found")
    return doc

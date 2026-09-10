"""Report generation using actual stored athlete/prediction/SHAP data. Scoped per owner."""
from fastapi import HTTPException

from app.core.constants import DISCLAIMER, PROJECT_TITLE
from app.database.mongodb import predictions_collection
from app.services.athlete_service import get_athlete
from app.services.shap_service import get_prediction_explanation


def get_prediction_report(prediction_id: str, owner: str) -> dict:
    prediction = predictions_collection.find_one({"prediction_id": prediction_id, "created_by": owner}, {"_id": 0})
    if not prediction:
        raise HTTPException(status_code=404, detail=f"Prediction '{prediction_id}' not found")

    athlete = get_athlete(prediction["athlete_id"], owner)
    explanation = get_prediction_explanation(prediction_id, owner)

    return {
        "project_title": PROJECT_TITLE,
        "athlete": athlete,
        "prediction": {
            "prediction_id": prediction["prediction_id"],
            "probability": prediction["probability"],
            "risk_level": prediction["risk_level"],
            "model_version": prediction["model_version"],
            "prediction_date": prediction["prediction_date"],
        },
        "top_risk_factors": explanation["top_risk_factors"],
        "protective_factors": explanation["protective_factors"],
        "disclaimer": DISCLAIMER,
    }


def get_athlete_report(athlete_id: str, owner: str) -> dict:
    athlete = get_athlete(athlete_id, owner)
    predictions = list(
        predictions_collection.find({"athlete_id": athlete_id, "created_by": owner}, {"_id": 0}).sort("prediction_date", -1)
    )
    return {
        "project_title": PROJECT_TITLE,
        "athlete": athlete,
        "predictions": predictions,
        "disclaimer": DISCLAIMER,
    }

"""Dashboard aggregate statistics, computed live from MongoDB (never hard-coded). Scoped per owner."""
from app.database.mongodb import assessments_collection, athletes_collection, predictions_collection


def get_dashboard_stats(owner: str) -> dict:
    total_athletes = athletes_collection.count_documents({"created_by": owner})
    total_assessments = assessments_collection.count_documents({"created_by": owner})
    total_predictions = predictions_collection.count_documents({"created_by": owner})

    high_risk = predictions_collection.count_documents({"created_by": owner, "risk_level": "HIGH"})
    medium_risk = predictions_collection.count_documents({"created_by": owner, "risk_level": "MEDIUM"})
    low_risk = predictions_collection.count_documents({"created_by": owner, "risk_level": "LOW"})

    probabilities = [p["probability"] for p in predictions_collection.find({"created_by": owner}, {"probability": 1})]
    average_risk = round(sum(probabilities) / len(probabilities), 4) if probabilities else None

    recent_predictions = list(
        predictions_collection.find({"created_by": owner}, {"_id": 0}).sort("prediction_date", -1).limit(10)
    )

    return {
        "total_athletes": total_athletes,
        "total_assessments": total_assessments,
        "total_predictions": total_predictions,
        "high_risk": high_risk,
        "medium_risk": medium_risk,
        "low_risk": low_risk,
        "average_predicted_risk": average_risk,
        "recent_predictions": recent_predictions,
    }

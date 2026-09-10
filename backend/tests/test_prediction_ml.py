"""Direct tests against the ML prediction module (bypassing the API/DB layer)."""
from app.ml.prediction import classify_risk, predict

DEMOGRAPHIC = {"age": 21, "gender": "Male", "sport": "Running", "event_type": "Long Distance", "height": 175, "weight": 62, "experience_years": 5}
TRAINING = {"training_hours_per_week": 9, "training_frequency": 6, "training_intensity": 8, "weekly_distance_km": 55, "long_run_distance_km": 18, "speed_work_sessions": 2, "training_load": 850, "acute_training_load": 900, "chronic_training_load": 700}
PHYSIOLOGICAL = {"resting_heart_rate": 72, "heart_rate_variability": 45, "fatigue_score": 8, "muscle_soreness": 7, "recovery_score": 40}
RECOVERY = {"sleep_hours": 5.5, "sleep_quality": 5, "recovery_days": 1, "rest_days": 1}
LIFESTYLE = {"stress_level": 7, "hydration_score": 60, "nutrition_score": 65}
INJURY_HISTORY = {"previous_injury": 1, "injury_count": 2, "previous_injury_type": "Muscle", "days_since_previous_injury": 90, "previous_recovery_duration": 45}


def test_classify_risk_boundaries():
    assert classify_risk(0.1) == "LOW"
    assert classify_risk(0.39) == "LOW"
    assert classify_risk(0.40) == "MEDIUM"
    assert classify_risk(0.69) == "MEDIUM"
    assert classify_risk(0.70) == "HIGH"
    assert classify_risk(0.99) == "HIGH"


def test_model_loads_and_predicts():
    result = predict(DEMOGRAPHIC, TRAINING, PHYSIOLOGICAL, RECOVERY, LIFESTYLE, INJURY_HISTORY)
    assert 0.0 <= result["probability"] <= 1.0
    assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH")


def test_shap_values_are_generated():
    result = predict(DEMOGRAPHIC, TRAINING, PHYSIOLOGICAL, RECOVERY, LIFESTYLE, INJURY_HISTORY)
    assert len(result["shap_contributions"]) > 0
    assert all("shap_value" in c for c in result["shap_contributions"])
    assert len(result["top_risk_factors"]) > 0 or len(result["protective_factors"]) > 0

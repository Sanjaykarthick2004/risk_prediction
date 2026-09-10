"""Integration test: athlete -> assessment -> prediction, hitting the real trained model."""
import pytest

ATHLETE_ID = "PYTEST-PRED-001"

ASSESSMENT_PAYLOAD = {
    "training": {"training_hours_per_week": 9, "training_frequency": 6, "training_intensity": 8,
                 "weekly_distance_km": 55, "long_run_distance_km": 18, "speed_work_sessions": 2,
                 "training_load": 850, "acute_training_load": 900, "chronic_training_load": 700},
    "physiological": {"resting_heart_rate": 72, "heart_rate_variability": 45, "fatigue_score": 8,
                       "muscle_soreness": 7, "recovery_score": 40},
    "recovery": {"sleep_hours": 5.5, "sleep_quality": 5, "recovery_days": 1, "rest_days": 1},
    "lifestyle": {"stress_level": 7, "hydration_score": 60, "nutrition_score": 65},
    "injury_history": {"previous_injury": 1, "injury_count": 2, "previous_injury_type": "Muscle",
                        "days_since_previous_injury": 90, "previous_recovery_duration": 45},
}


@pytest.fixture(scope="module")
def athlete(client, auth_headers):
    client.post("/api/athletes", json={
        "athlete_id": ATHLETE_ID, "name": "Prediction Test Athlete", "age": 24, "gender": "Male",
        "sport": "Running", "event_type": "Middle Distance", "height": 178, "weight": 64, "experience_years": 6,
    }, headers=auth_headers)
    return ATHLETE_ID


def test_create_assessment(client, auth_headers, athlete):
    res = client.post(f"/api/athletes/{athlete}/assessments", json=ASSESSMENT_PAYLOAD, headers=auth_headers)
    assert res.status_code == 201
    body = res.json()
    assert body["athlete_id"] == athlete
    assert "demographic" in body


def test_prediction_probability_and_risk_level(client, auth_headers, athlete):
    res = client.post("/api/predictions", json={"athlete_id": athlete, **ASSESSMENT_PAYLOAD}, headers=auth_headers)
    assert res.status_code == 201
    body = res.json()
    assert 0.0 <= body["probability"] <= 1.0
    assert body["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert body["model_version"]
    assert isinstance(body["top_risk_factors"], list)
    assert isinstance(body["protective_factors"], list)


def test_prediction_stored_and_retrievable(client, auth_headers, athlete):
    create_res = client.post("/api/predictions", json={"athlete_id": athlete, **ASSESSMENT_PAYLOAD}, headers=auth_headers)
    prediction_id = create_res.json()["prediction_id"]

    get_res = client.get(f"/api/predictions/{prediction_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["prediction_id"] == prediction_id

    history_res = client.get(f"/api/athletes/{athlete}/predictions", headers=auth_headers)
    assert history_res.status_code == 200
    assert any(p["prediction_id"] == prediction_id for p in history_res.json())


def test_prediction_for_missing_athlete_returns_404(client, auth_headers):
    res = client.post("/api/predictions", json={"athlete_id": "PYTEST-NO-SUCH-ATHLETE", **ASSESSMENT_PAYLOAD}, headers=auth_headers)
    assert res.status_code == 404

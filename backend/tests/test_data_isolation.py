"""Each researcher account must only see its own athletes/assessments/predictions —
one account's data must never leak into another's.
"""
import pytest

ASSESSMENT_PAYLOAD = {
    "training": {"training_hours_per_week": 7, "training_frequency": 5, "training_intensity": 6,
                 "weekly_distance_km": 35, "long_run_distance_km": 10, "speed_work_sessions": 1,
                 "training_load": 500, "acute_training_load": 500, "chronic_training_load": 500},
    "physiological": {"resting_heart_rate": 65, "heart_rate_variability": 60, "fatigue_score": 5,
                       "muscle_soreness": 5, "recovery_score": 65},
    "recovery": {"sleep_hours": 7, "sleep_quality": 6, "recovery_days": 2, "rest_days": 2},
    "lifestyle": {"stress_level": 5, "hydration_score": 70, "nutrition_score": 70},
    "injury_history": {"previous_injury": 0, "injury_count": 0, "previous_injury_type": "None",
                        "days_since_previous_injury": 3650, "previous_recovery_duration": 0},
}


@pytest.fixture
def second_user_headers(client):
    client.post("/api/auth/register", json={"username": "pytest_isolation_b", "password": "testpass123", "role": "RESEARCHER"})
    res = client.post("/api/auth/login", data={"username": "pytest_isolation_b", "password": "testpass123"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_athlete_list_is_isolated_per_account(client, auth_headers, second_user_headers):
    client.post("/api/athletes", json={
        "athlete_id": "PYTEST-ISO-001", "name": "Owned By A", "age": 22, "gender": "Male",
        "sport": "Running", "event_type": "Long Distance", "height": 180, "weight": 78, "experience_years": 4,
    }, headers=auth_headers)

    list_as_a = client.get("/api/athletes", headers=auth_headers).json()
    assert any(a["athlete_id"] == "PYTEST-ISO-001" for a in list_as_a)

    list_as_b = client.get("/api/athletes", headers=second_user_headers).json()
    assert not any(a["athlete_id"] == "PYTEST-ISO-001" for a in list_as_b)


def test_athlete_get_is_isolated_per_account(client, auth_headers, second_user_headers):
    client.post("/api/athletes", json={
        "athlete_id": "PYTEST-ISO-002", "name": "Owned By A", "age": 22, "gender": "Male",
        "sport": "Running", "event_type": "Long Distance", "height": 180, "weight": 78, "experience_years": 4,
    }, headers=auth_headers)

    assert client.get("/api/athletes/PYTEST-ISO-002", headers=auth_headers).status_code == 200
    # A different account gets 404, not the other account's athlete data.
    assert client.get("/api/athletes/PYTEST-ISO-002", headers=second_user_headers).status_code == 404


def test_prediction_and_dashboard_isolated_per_account(client, auth_headers, second_user_headers):
    client.post("/api/athletes", json={
        "athlete_id": "PYTEST-ISO-003", "name": "Owned By A", "age": 22, "gender": "Male",
        "sport": "Running", "event_type": "Long Distance", "height": 180, "weight": 78, "experience_years": 4,
    }, headers=auth_headers)
    pred_res = client.post("/api/predictions", json={"athlete_id": "PYTEST-ISO-003", **ASSESSMENT_PAYLOAD}, headers=auth_headers)
    prediction_id = pred_res.json()["prediction_id"]

    # Owner can fetch it.
    assert client.get(f"/api/predictions/{prediction_id}", headers=auth_headers).status_code == 200
    # Another account cannot, even by exact id.
    assert client.get(f"/api/predictions/{prediction_id}", headers=second_user_headers).status_code == 404
    # And it doesn't show up in another account's list.
    other_list = client.get("/api/predictions", headers=second_user_headers).json()
    assert not any(p["prediction_id"] == prediction_id for p in other_list)

    # Dashboard stats for the second account must not count the first account's data.
    dash_b = client.get("/api/dashboard/stats", headers=second_user_headers).json()
    assert not any(p["prediction_id"] == prediction_id for p in dash_b["recent_predictions"])

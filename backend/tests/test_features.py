import pandas as pd

from app.ml.feature_engineering import add_engineered_features


def _base_row(**overrides):
    row = {
        "height": 180, "weight": 72, "acute_training_load": 500, "chronic_training_load": 500,
        "training_load": 500, "training_hours_per_week": 10, "rest_days": 2, "recovery_days": 2,
        "sleep_hours": 7, "stress_level": 5, "fatigue_score": 5, "muscle_soreness": 5,
        "previous_injury": 0, "injury_count": 0, "days_since_previous_injury": 3650,
        "recovery_score": 70,
    }
    row.update(overrides)
    return pd.DataFrame([row])


def test_bmi_calculation():
    df = add_engineered_features(_base_row(height=180, weight=72))
    assert abs(df["bmi"].iloc[0] - 72 / (1.8 ** 2)) < 1e-6


def test_workload_ratio_division_by_zero_is_safe():
    df = add_engineered_features(_base_row(acute_training_load=500, chronic_training_load=0))
    assert df["workload_ratio"].iloc[0] == 1.0  # safe fallback, no crash/inf


def test_workload_ratio_normal_case():
    df = add_engineered_features(_base_row(acute_training_load=800, chronic_training_load=400))
    assert abs(df["workload_ratio"].iloc[0] - 2.0) < 1e-6


def test_sleep_deficit_never_negative():
    df = add_engineered_features(_base_row(sleep_hours=9))
    assert df["sleep_deficit"].iloc[0] == 0

    df2 = add_engineered_features(_base_row(sleep_hours=5))
    assert df2["sleep_deficit"].iloc[0] == 3


def test_injury_history_score_zero_when_no_prior_injury():
    df = add_engineered_features(_base_row(previous_injury=0, injury_count=0))
    assert df["injury_history_score"].iloc[0] == 0

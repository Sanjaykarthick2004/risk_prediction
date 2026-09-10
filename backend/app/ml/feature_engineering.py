"""Derived / engineered feature construction.

Feature dictionary (Feature, Description, Formula, Source modality, Reason):

1. bmi — Body mass index. weight_kg / height_m^2. Demographic.
   Standard body-composition indicator linked to injury susceptibility.
2. workload_ratio — Acute:chronic workload ratio (ACWR).
   acute_training_load / chronic_training_load. Training.
   Sports-science proxy for training-load spikes relative to accumulated
   fitness; spikes are associated with elevated injury risk.
3. training_load_per_hour — training_load / training_hours_per_week. Training.
   Captures training density rather than raw volume alone.
4. recovery_gap — rest_days - recovery_days. Recovery.
   Negative values indicate under-resting relative to prescribed need.
5. sleep_deficit — max(0, 8 - sleep_hours). Recovery.
   Chronic sleep deficit is linked to elevated injury risk and impaired recovery.
6. stress_fatigue_index — (stress_level + fatigue_score + muscle_soreness) / 3.
   Lifestyle + Physiological. Aggregates overlapping strain signals.
7. injury_history_score —
   previous_injury * (1 + injury_count) / (1 + days_since_previous_injury/365).
   Injury History. Recent, frequent prior injuries weigh more than old ones.
8. training_recovery_balance — training_load / (recovery_score + 1).
   Training + Physiological. Training demand vs. recovery capacity.

The same logic is used at training time and at prediction time (imported by
both app.ml.preprocessing and app.ml.prediction).
"""
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ENGINEERED_FEATURES = [
    "bmi", "workload_ratio", "training_load_per_hour", "recovery_gap",
    "sleep_deficit", "stress_fatigue_index", "injury_history_score",
    "training_recovery_balance",
]


def _safe_divide(numerator: pd.Series, denominator: pd.Series, fill_value: float = 0.0) -> pd.Series:
    denom = denominator.replace(0, np.nan)
    return (numerator / denom).fillna(fill_value)


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    height_m = df["height"] / 100.0
    df["bmi"] = _safe_divide(df["weight"], height_m ** 2)
    df["workload_ratio"] = _safe_divide(df["acute_training_load"], df["chronic_training_load"], fill_value=1.0)
    df["training_load_per_hour"] = _safe_divide(df["training_load"], df["training_hours_per_week"])
    df["recovery_gap"] = df["rest_days"] - df["recovery_days"]
    df["sleep_deficit"] = (8 - df["sleep_hours"]).clip(lower=0)
    df["stress_fatigue_index"] = (df["stress_level"] + df["fatigue_score"] + df["muscle_soreness"]) / 3.0
    df["injury_history_score"] = _safe_divide(
        df["previous_injury"] * (1 + df["injury_count"]),
        (1 + df["days_since_previous_injury"] / 365.0),
    )
    df["training_recovery_balance"] = _safe_divide(df["training_load"], df["recovery_score"] + 1)
    return df

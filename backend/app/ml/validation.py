"""Data validation utilities for the raw/uploaded athlete dataset."""
import logging
from typing import Dict, List

import pandas as pd

from app.ml.data_loader import ID_COLUMN, TARGET_COLUMN

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "athlete_id", "age", "gender", "sport", "event_type", "height", "weight",
    "experience_years", "training_hours_per_week", "training_frequency",
    "training_intensity", "weekly_distance_km", "long_run_distance_km",
    "speed_work_sessions", "training_load", "acute_training_load",
    "chronic_training_load", "resting_heart_rate", "heart_rate_variability",
    "fatigue_score", "muscle_soreness", "recovery_score", "sleep_hours",
    "sleep_quality", "recovery_days", "rest_days", "stress_level",
    "hydration_score", "nutrition_score", "previous_injury", "injury_count",
    "previous_injury_type", "days_since_previous_injury", "previous_recovery_duration",
]

VALIDATION_RANGES = {
    "age": (15, 60), "height": (100, 230), "weight": (30, 200),
    "experience_years": (0, 45), "training_hours_per_week": (0, 30),
    "training_frequency": (0, 14), "training_intensity": (1, 10),
    "weekly_distance_km": (0, 200), "long_run_distance_km": (0, 50),
    "speed_work_sessions": (0, 10), "training_load": (0, 3000),
    "acute_training_load": (0, 3000), "chronic_training_load": (0, 3000),
    "resting_heart_rate": (30, 120), "heart_rate_variability": (0, 200),
    "fatigue_score": (1, 10), "muscle_soreness": (1, 10),
    "recovery_score": (0, 100), "sleep_hours": (0, 16), "sleep_quality": (1, 10),
    "recovery_days": (0, 14), "rest_days": (0, 14), "stress_level": (1, 10),
    "hydration_score": (0, 100), "nutrition_score": (0, 100),
    "injury_count": (0, 20), "days_since_previous_injury": (0, 3650),
    "previous_recovery_duration": (0, 365),
}

# This experiment's research population is running athletes only, so `sport`
# is currently a single-value category. `event_type` distinguishes the
# running disciplines within that population.
CATEGORICAL_VALUES = {
    "gender": ["Male", "Female", "Other"],
    "sport": ["Running"],
    "event_type": ["Sprint", "Middle Distance", "Long Distance", "Cross Country", "General Running"],
    "previous_injury_type": [
        "None", "Shin Splints", "Runner's Knee", "IT Band Syndrome", "Ankle Injury",
        "Hamstring Strain", "Stress Injury", "Other",
    ],
}


class ValidationReport:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats: Dict = {}

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> Dict:
        return {"errors": self.errors, "warnings": self.warnings, "stats": self.stats, "is_valid": self.is_valid}


def validate_dataset(df: pd.DataFrame, require_target: bool = False) -> ValidationReport:
    report = ValidationReport()

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        report.errors.append(f"Missing required columns: {missing_cols}")
    if require_target and TARGET_COLUMN not in df.columns:
        report.errors.append(f"Missing target column: {TARGET_COLUMN}")
    if report.errors:
        return report

    dup_ids = df[ID_COLUMN].duplicated().sum() if ID_COLUMN in df.columns else 0
    if dup_ids:
        report.warnings.append(f"{dup_ids} duplicate athlete_id records found")

    full_dup_rows = df.duplicated().sum()
    if full_dup_rows:
        report.warnings.append(f"{full_dup_rows} fully duplicated rows found")

    missing_counts = df[REQUIRED_COLUMNS].isna().sum()
    missing_counts = missing_counts[missing_counts > 0]
    if len(missing_counts):
        report.warnings.append(f"Missing values detected: {missing_counts.to_dict()}")

    out_of_range = {}
    for col, (low, high) in VALIDATION_RANGES.items():
        if col not in df.columns:
            continue
        series = pd.to_numeric(df[col], errors="coerce")
        invalid_type = series.isna() & df[col].notna()
        if invalid_type.any():
            report.errors.append(f"Column '{col}' contains non-numeric values")
        bad = series[(series < low) | (series > high)]
        if len(bad):
            out_of_range[col] = int(len(bad))
    if out_of_range:
        report.warnings.append(f"Out-of-range values detected: {out_of_range}")

    for col in ["age", "height", "weight", "training_hours_per_week", "injury_count"]:
        if col in df.columns:
            series = pd.to_numeric(df[col], errors="coerce")
            if (series < 0).any():
                report.errors.append(f"Column '{col}' contains negative values")

    invalid_categories = {}
    for col, allowed in CATEGORICAL_VALUES.items():
        if col not in df.columns:
            continue
        bad_values = set(df[col].dropna().unique()) - set(allowed)
        if bad_values:
            invalid_categories[col] = list(bad_values)
    if invalid_categories:
        report.warnings.append(f"Unrecognized categorical values: {invalid_categories}")

    if TARGET_COLUMN in df.columns:
        bad_target = set(df[TARGET_COLUMN].dropna().unique()) - {0, 1}
        if bad_target:
            report.errors.append(f"Target column contains values other than 0/1: {bad_target}")

    report.stats = {
        "n_rows": len(df),
        "n_columns": len(df.columns),
        "n_missing_values": int(df[REQUIRED_COLUMNS].isna().sum().sum()),
        "n_duplicate_rows": int(full_dup_rows),
        "target_distribution": (
            df[TARGET_COLUMN].value_counts(normalize=True).round(4).to_dict()
            if TARGET_COLUMN in df.columns else None
        ),
    }
    return report

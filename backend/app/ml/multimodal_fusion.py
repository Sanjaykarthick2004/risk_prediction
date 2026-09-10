"""Modality definitions and feature-level fusion for the multimodal pipeline."""
from typing import Dict, List

MODALITY_FEATURES: Dict[str, List[str]] = {
    "demographic": ["age", "gender", "sport", "event_type", "height", "weight", "experience_years", "bmi"],
    "training": [
        "training_hours_per_week", "training_frequency", "training_intensity",
        "weekly_distance_km", "long_run_distance_km", "speed_work_sessions",
        "training_load", "acute_training_load", "chronic_training_load",
        "workload_ratio", "training_load_per_hour", "training_recovery_balance",
    ],
    "physiological": [
        "resting_heart_rate", "heart_rate_variability", "fatigue_score",
        "muscle_soreness", "recovery_score",
    ],
    "recovery": ["sleep_hours", "sleep_quality", "recovery_days", "rest_days", "recovery_gap", "sleep_deficit"],
    "lifestyle": ["stress_level", "hydration_score", "nutrition_score", "stress_fatigue_index"],
    "injury_history": [
        "previous_injury", "injury_count", "previous_injury_type",
        "days_since_previous_injury", "previous_recovery_duration",
        "injury_history_score",
    ],
}

# Named cumulative ablation configurations (M1..M6).
ABLATION_CONFIGS: Dict[str, List[str]] = {
    "M1_demographic": ["demographic"],
    "M2_demographic_training": ["demographic", "training"],
    "M3_demographic_training_recovery": ["demographic", "training", "recovery"],
    "M4_demographic_training_physiological": ["demographic", "training", "physiological"],
    "M5_demo_training_physio_recovery_lifestyle": [
        "demographic", "training", "physiological", "recovery", "lifestyle",
    ],
    "M6_all_modalities": ["demographic", "training", "physiological", "recovery", "lifestyle", "injury_history"],
}


def get_features_for_modalities(modalities: List[str]) -> List[str]:
    features: List[str] = []
    for modality in modalities:
        for col in MODALITY_FEATURES[modality]:
            if col not in features:
                features.append(col)
    return features


def get_all_features() -> List[str]:
    return get_features_for_modalities(list(MODALITY_FEATURES.keys()))

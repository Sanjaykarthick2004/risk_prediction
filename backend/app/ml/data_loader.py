"""Data loading and SYNTHETIC DEMONSTRATION DATA generation.

RESEARCH POPULATION: this project's current experiment studies RUNNING
ATHLETES only (sprint, middle-distance, long-distance, cross country, and
general/recreational running). A single-sport population gives more
consistent training-load and injury characteristics than pooling several
sports without enough representative data from each one.

No real-world, clinically validated injury dataset with confirmed future
injury outcomes is bundled with this academic project.
generate_synthetic_dataset() produces SYNTHETIC DEMONSTRATION DATA only, so
the full pipeline (validation, preprocessing, feature engineering, model
training, evaluation, SHAP) can be built and demonstrated end-to-end at a
realistic dataset size. Results from this data must never be presented as
real research findings or real athlete data collection — only as a working
software demonstration of the framework. See docs/methodology.md for the
full, honest description a viva examiner can be pointed to.

GENERATION METHOD (documented per academic-integrity requirements):
- Every field is drawn from a fixed distribution (normal/uniform/integer/
  categorical) with ranges chosen to look like a plausible running-athlete
  sample, not from any real dataset.
- A handful of fields are deliberately NOT independent — see
  `_apply_variable_relationships()` — so the dataset is a meaningful
  demonstration of multimodal modeling rather than pure noise:
    higher acute:chronic workload ratio  -> higher fatigue/soreness (weakly)
    lower sleep hours                    -> lower recovery score (weakly)
    previous injury / more prior injuries -> higher modeled injury-risk score
  These are modeling choices made for this demonstration dataset, not
  scientifically validated causal relationships.
- The target `injury_next_7_days` is sampled from a logistic function of a
  latent risk score built from a SUBSET of the above fields plus substantial
  independent random noise (see `_generate_target`), so it is realistic and
  learnable but never a deterministic/leaky function of any single input.
- Generation is fully reproducible: every call uses `numpy.random.default_rng(seed)`
  with `seed` defaulting to `settings.random_state` (42).
"""
import logging
import os

import numpy as np
import pandas as pd

from app.config import settings

logger = logging.getLogger(__name__)

TARGET_COLUMN = "injury_next_7_days"
ID_COLUMN = "athlete_id"

# This experiment's population is running athletes only. `sport` is kept as
# a column (rather than removed) so the schema stays compatible with the
# general multimodal architecture if a future study adds other sports.
SPORT = "Running"
EVENT_TYPES = ["Sprint", "Middle Distance", "Long Distance", "Cross Country", "General Running"]
EVENT_TYPE_WEIGHTS = [0.15, 0.20, 0.30, 0.15, 0.20]
GENDERS = ["Male", "Female", "Other"]
INJURY_TYPES = [
    "None", "Shin Splints", "Runner's Knee", "IT Band Syndrome", "Ankle Injury",
    "Hamstring Strain", "Stress Injury", "Other",
]

# Typical weekly distance (km) and speed-work volume differ by event type.
# These are illustrative demonstration values, not sports-science norms.
EVENT_TYPE_PROFILE = {
    "Sprint":           {"weekly_km_mean": 22, "weekly_km_sd": 8,  "long_run_frac": 0.12, "speed_sessions_range": (2, 5)},
    "Middle Distance":  {"weekly_km_mean": 40, "weekly_km_sd": 10, "long_run_frac": 0.20, "speed_sessions_range": (2, 4)},
    "Long Distance":    {"weekly_km_mean": 65, "weekly_km_sd": 16, "long_run_frac": 0.30, "speed_sessions_range": (1, 3)},
    "Cross Country":    {"weekly_km_mean": 55, "weekly_km_sd": 15, "long_run_frac": 0.28, "speed_sessions_range": (1, 3)},
    "General Running":  {"weekly_km_mean": 30, "weekly_km_sd": 12, "long_run_frac": 0.22, "speed_sessions_range": (0, 2)},
}


def _generate_base_fields(rng: np.random.Generator, n: int) -> dict:
    age = rng.integers(16, 46, n)
    gender = rng.choice(GENDERS, n, p=[0.52, 0.46, 0.02])
    event_type = rng.choice(EVENT_TYPES, n, p=EVENT_TYPE_WEIGHTS)
    height = rng.normal(171, 9, n).clip(145, 205)
    weight = rng.normal(62, 9, n).clip(40, 100)
    experience_years = (age - rng.integers(12, 20, n)).clip(0, None)

    weekly_km_mean = np.array([EVENT_TYPE_PROFILE[e]["weekly_km_mean"] for e in event_type])
    weekly_km_sd = np.array([EVENT_TYPE_PROFILE[e]["weekly_km_sd"] for e in event_type])
    long_run_frac = np.array([EVENT_TYPE_PROFILE[e]["long_run_frac"] for e in event_type])

    weekly_distance_km = rng.normal(weekly_km_mean, weekly_km_sd, n).clip(5, 160)
    long_run_distance_km = (weekly_distance_km * (long_run_frac + rng.normal(0, 0.05, n))).clip(2, 42)

    speed_lo = np.array([EVENT_TYPE_PROFILE[e]["speed_sessions_range"][0] for e in event_type])
    speed_hi = np.array([EVENT_TYPE_PROFILE[e]["speed_sessions_range"][1] for e in event_type])
    speed_work_sessions = np.array([rng.integers(lo, hi + 1) for lo, hi in zip(speed_lo, speed_hi)])

    # Training hours roughly track weekly distance (at an easy-pace estimate)
    # plus independent variation (cross-training, strength work, etc.).
    training_hours_per_week = (weekly_distance_km / 9.0 + rng.normal(1.5, 1.2, n)).clip(1, 22)
    training_frequency = rng.integers(2, 8, n)
    training_intensity = (1 + speed_work_sessions * 1.1 + rng.normal(3, 1.8, n)).clip(1, 10).round().astype(int)

    return {
        "age": age, "gender": gender, "event_type": event_type,
        "height": height, "weight": weight, "experience_years": experience_years,
        "weekly_distance_km": weekly_distance_km, "long_run_distance_km": long_run_distance_km,
        "speed_work_sessions": speed_work_sessions,
        "training_hours_per_week": training_hours_per_week, "training_frequency": training_frequency,
        "training_intensity": training_intensity,
    }


def _generate_load_and_physio_fields(rng: np.random.Generator, n: int, fields: dict) -> dict:
    weekly_distance_km = fields["weekly_distance_km"]
    training_intensity = fields["training_intensity"]

    # Training load is a function of volume x intensity (a common
    # sports-science convention), plus noise for individual variation.
    base_load = weekly_distance_km * (0.6 + 0.08 * training_intensity)
    acute_training_load = (base_load * rng.normal(1.0, 0.18, n)).clip(20, 2200)
    chronic_training_load = (acute_training_load * rng.normal(1.0, 0.15, n)).clip(20, 2200)
    training_load = acute_training_load
    workload_ratio = acute_training_load / np.where(chronic_training_load == 0, np.nan, chronic_training_load)
    workload_ratio = np.nan_to_num(workload_ratio, nan=1.0)

    resting_heart_rate = rng.normal(58, 7, n).clip(38, 95)
    heart_rate_variability = rng.normal(68, 18, n).clip(15, 140)

    # Fatigue/soreness trend upward with workload spikes (weak relationship
    # + noise, so it is a tendency, not a rule) — see module docstring.
    fatigue_score = (5 + 2.2 * (workload_ratio - 1.0) + rng.normal(0, 1.6, n)).clip(1, 10).round().astype(int)
    muscle_soreness = (5 + 2.0 * (workload_ratio - 1.0) + rng.normal(0, 1.6, n)).clip(1, 10).round().astype(int)

    sleep_hours = rng.normal(7.1, 1.2, n).clip(3.5, 10.5)
    # Recovery trends upward with more sleep, downward with fatigue (weak + noisy).
    recovery_score = (65 + 4.0 * (sleep_hours - 7) - 2.5 * (fatigue_score - 5) + rng.normal(0, 12, n)).clip(0, 100)

    return {
        "training_load": training_load, "acute_training_load": acute_training_load,
        "chronic_training_load": chronic_training_load,
        "resting_heart_rate": resting_heart_rate, "heart_rate_variability": heart_rate_variability,
        "fatigue_score": fatigue_score, "muscle_soreness": muscle_soreness,
        "sleep_hours": sleep_hours, "recovery_score": recovery_score,
        "_workload_ratio": workload_ratio,  # internal only, used for the target formula; not a saved column
    }


def _generate_remaining_fields(rng: np.random.Generator, n: int) -> dict:
    sleep_quality = rng.integers(1, 11, n)
    recovery_days = rng.integers(0, 4, n)
    rest_days = rng.integers(0, 4, n)

    stress_level = rng.integers(1, 11, n)
    hydration_score = rng.normal(70, 15, n).clip(0, 100)
    nutrition_score = rng.normal(70, 15, n).clip(0, 100)

    previous_injury = rng.choice([0, 1], n, p=[0.6, 0.4])
    injury_count = np.where(previous_injury == 1, rng.integers(1, 6, n), 0)
    previous_injury_type = np.where(previous_injury == 1, rng.choice(INJURY_TYPES[1:], n), "None")
    days_since_previous_injury = np.where(previous_injury == 1, rng.integers(10, 800, n), 3650)
    previous_recovery_duration = np.where(previous_injury == 1, rng.integers(3, 120, n), 0)

    return {
        "sleep_quality": sleep_quality, "recovery_days": recovery_days, "rest_days": rest_days,
        "stress_level": stress_level, "hydration_score": hydration_score, "nutrition_score": nutrition_score,
        "previous_injury": previous_injury, "injury_count": injury_count,
        "previous_injury_type": previous_injury_type,
        "days_since_previous_injury": days_since_previous_injury,
        "previous_recovery_duration": previous_recovery_duration,
    }


def _generate_target(rng: np.random.Generator, n: int, df: pd.DataFrame, workload_ratio: np.ndarray) -> np.ndarray:
    """Latent-risk-score target generation (documented, non-causal demo logic).

    Builds a plausible-but-noisy relationship between a subset of modalities
    and the binary outcome. Substantial independent noise keeps the target
    a genuinely separate (non-deterministic, non-leaky) outcome column, the
    same discipline a real prospective injury dataset would require.

    `_BASE_RATE_OFFSET` shifts the average modeled probability down from an
    unrealistic ~50% to a demonstration base rate of roughly 15-20% positive
    cases — closer to a plausible weekly injury incidence than a coin flip —
    while leaving the dataset naturally (not artificially/resampling-forced)
    imbalanced, so the class-imbalance-handling code path (SMOTE / class
    weighting) has something real to do. This is a modeling choice for the
    demonstration dataset, not a measured epidemiological rate.
    """
    z = (
        0.9 * (workload_ratio - 1.0)
        + 0.05 * (df["fatigue_score"] - 5)
        + 0.05 * (df["muscle_soreness"] - 5)
        + 0.04 * (df["stress_level"] - 5)
        - 0.03 * (df["sleep_hours"] - 7)
        - 0.02 * (df["recovery_score"] - 65) / 10
        + 0.20 * (df["speed_work_sessions"] - df["speed_work_sessions"].mean()) / (df["speed_work_sessions"].std() + 1e-6)
        + 0.6 * df["previous_injury"]
        + 0.15 * df["injury_count"]
        - 0.015 * df["experience_years"]
        + rng.normal(0, 1.1, n)
    )
    _BASE_RATE_OFFSET = 1.5
    prob = 1 / (1 + np.exp(-(z - z.mean() - _BASE_RATE_OFFSET)))
    return (rng.uniform(0, 1, n) < prob).astype(int)


def generate_synthetic_dataset(n_athletes: int = None, seed: int = None) -> pd.DataFrame:
    """Generate a SYNTHETIC DEMONSTRATION dataset of running athletes.

    n_athletes defaults to `settings.synthetic_dataset_size` (configurable;
    the academic experiment target is 5,000-10,000). seed defaults to
    `settings.random_state` (42) so generation is fully reproducible.
    See the module docstring for the documented generation method.
    """
    n = n_athletes if n_athletes is not None else settings.synthetic_dataset_size
    seed = seed if seed is not None else settings.random_state
    rng = np.random.default_rng(seed)

    athlete_id = [f"ATH-{i+1:05d}" for i in range(n)]
    base = _generate_base_fields(rng, n)
    load_physio = _generate_load_and_physio_fields(rng, n, base)
    workload_ratio = load_physio.pop("_workload_ratio")
    remaining = _generate_remaining_fields(rng, n)

    df = pd.DataFrame({
        "athlete_id": athlete_id,
        "age": base["age"], "gender": base["gender"], "sport": SPORT, "event_type": base["event_type"],
        "height": base["height"].round(1), "weight": base["weight"].round(1),
        "experience_years": base["experience_years"],
        "training_hours_per_week": base["training_hours_per_week"].round(1),
        "training_frequency": base["training_frequency"], "training_intensity": base["training_intensity"],
        "weekly_distance_km": base["weekly_distance_km"].round(1),
        "long_run_distance_km": base["long_run_distance_km"].round(1),
        "speed_work_sessions": base["speed_work_sessions"],
        "training_load": load_physio["training_load"].round(1),
        "acute_training_load": load_physio["acute_training_load"].round(1),
        "chronic_training_load": load_physio["chronic_training_load"].round(1),
        "resting_heart_rate": load_physio["resting_heart_rate"].round(1),
        "heart_rate_variability": load_physio["heart_rate_variability"].round(1),
        "fatigue_score": load_physio["fatigue_score"], "muscle_soreness": load_physio["muscle_soreness"],
        "recovery_score": load_physio["recovery_score"].round(1),
        "sleep_hours": load_physio["sleep_hours"].round(1),
        "sleep_quality": remaining["sleep_quality"], "recovery_days": remaining["recovery_days"],
        "rest_days": remaining["rest_days"], "stress_level": remaining["stress_level"],
        "hydration_score": remaining["hydration_score"].round(1),
        "nutrition_score": remaining["nutrition_score"].round(1),
        "previous_injury": remaining["previous_injury"], "injury_count": remaining["injury_count"],
        "previous_injury_type": remaining["previous_injury_type"],
        "days_since_previous_injury": remaining["days_since_previous_injury"],
        "previous_recovery_duration": remaining["previous_recovery_duration"],
    })

    df[TARGET_COLUMN] = _generate_target(rng, n, df, workload_ratio)
    return df


def read_athlete_csv(path: str) -> pd.DataFrame:
    """CSV reader shared by every dataset-reading path in the app.

    `previous_injury_type` legitimately uses the literal string "None" as a
    category (no prior injury). pandas' default NA-string list treats
    "None"/"NA"/"NULL"/etc. as missing, which would silently turn that valid
    category into fake missing values in every quality report. Reading with
    `keep_default_na=False` (and only an actually-empty cell counted as
    missing) avoids that false positive.
    """
    return pd.read_csv(path, keep_default_na=False, na_values=[""])


def load_raw_data(path: str = None) -> pd.DataFrame:
    path = path or settings.raw_data_path
    if not os.path.exists(path):
        logger.warning("Raw dataset not found at %s. Generating SYNTHETIC DEMONSTRATION DATA.", path)
        df = generate_synthetic_dataset()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False)
        return df
    return read_athlete_csv(path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = generate_synthetic_dataset()
    os.makedirs(os.path.dirname(settings.raw_data_path), exist_ok=True)
    data.to_csv(settings.raw_data_path, index=False)
    os.makedirs(os.path.dirname(settings.sample_data_path), exist_ok=True)
    data.head(50).to_csv(settings.sample_data_path, index=False)
    print(f"SYNTHETIC DEMONSTRATION DATA (Running athletes) generated: {data.shape}")
    print(data[TARGET_COLUMN].value_counts(normalize=True))

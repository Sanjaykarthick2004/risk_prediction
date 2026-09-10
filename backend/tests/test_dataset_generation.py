"""Tests for the configurable, reproducible running-athlete synthetic dataset generator."""
from app.ml.data_loader import EVENT_TYPES, TARGET_COLUMN, generate_synthetic_dataset
from app.ml.multimodal_fusion import get_all_features
from app.ml.validation import CATEGORICAL_VALUES, validate_dataset


def test_dataset_size_is_configurable():
    assert len(generate_synthetic_dataset(n_athletes=100, seed=1)) == 100
    assert len(generate_synthetic_dataset(n_athletes=1000, seed=1)) == 1000


def test_generation_is_reproducible_with_same_seed():
    df1 = generate_synthetic_dataset(n_athletes=200, seed=42)
    df2 = generate_synthetic_dataset(n_athletes=200, seed=42)
    assert df1.equals(df2)


def test_different_seeds_produce_different_data():
    df1 = generate_synthetic_dataset(n_athletes=200, seed=1)
    df2 = generate_synthetic_dataset(n_athletes=200, seed=2)
    assert not df1.equals(df2)


def test_population_is_running_only():
    df = generate_synthetic_dataset(n_athletes=300, seed=3)
    assert (df["sport"] == "Running").all()
    assert set(df["event_type"].unique()) <= set(EVENT_TYPES)


def test_generated_dataset_passes_validation():
    df = generate_synthetic_dataset(n_athletes=500, seed=4)
    report = validate_dataset(df, require_target=True)
    assert report.is_valid
    assert report.stats["n_missing_values"] == 0
    assert report.stats["n_duplicate_rows"] == 0


def test_categorical_values_match_running_schema():
    df = generate_synthetic_dataset(n_athletes=500, seed=5)
    assert set(df["sport"].unique()) <= set(CATEGORICAL_VALUES["sport"])
    assert set(df["event_type"].unique()) <= set(CATEGORICAL_VALUES["event_type"])
    assert set(df["previous_injury_type"].unique()) <= set(CATEGORICAL_VALUES["previous_injury_type"])


def test_target_is_binary_and_not_trivially_constant():
    df = generate_synthetic_dataset(n_athletes=2000, seed=6)
    assert set(df[TARGET_COLUMN].unique()) <= {0, 1}
    rate = df[TARGET_COLUMN].mean()
    assert 0.05 < rate < 0.6  # naturally imbalanced, not forced 50/50, not degenerate


def test_target_column_never_used_as_a_feature():
    assert TARGET_COLUMN not in get_all_features()


def test_running_specific_fields_present_and_match_hours_removed():
    df = generate_synthetic_dataset(n_athletes=50, seed=7)
    for col in ("event_type", "weekly_distance_km", "long_run_distance_km", "speed_work_sessions"):
        assert col in df.columns
    assert "position" not in df.columns
    assert "match_hours_per_week" not in df.columns

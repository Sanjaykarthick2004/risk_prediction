import pandas as pd

from app.ml.data_loader import generate_synthetic_dataset
from app.ml.validation import validate_dataset


def test_valid_synthetic_dataset_passes():
    df = generate_synthetic_dataset(n_athletes=50, seed=1)
    report = validate_dataset(df, require_target=True)
    assert report.is_valid


def test_missing_required_columns_detected():
    df = pd.DataFrame({"athlete_id": ["A1"], "age": [25]})
    report = validate_dataset(df)
    assert not report.is_valid
    assert "Missing required columns" in report.errors[0]


def test_out_of_range_values_flagged_as_warning():
    df = generate_synthetic_dataset(n_athletes=20, seed=2)
    df.loc[0, "age"] = 999  # out of range
    report = validate_dataset(df)
    assert report.is_valid  # out-of-range is a warning, not a hard error
    assert any("Out-of-range" in w for w in report.warnings)


def test_negative_values_rejected():
    df = generate_synthetic_dataset(n_athletes=20, seed=3)
    df.loc[0, "age"] = -5
    report = validate_dataset(df)
    assert not report.is_valid


def test_duplicate_rows_flagged():
    df = generate_synthetic_dataset(n_athletes=5, seed=4)
    df_with_dupes = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    report = validate_dataset(df_with_dupes)
    assert any("duplicate" in w.lower() for w in report.warnings)

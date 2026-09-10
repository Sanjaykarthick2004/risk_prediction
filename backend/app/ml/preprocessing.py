"""Reproducible preprocessing pipeline: cleaning, encoding, scaling.

Preprocessing is always fit on the training split only and persisted with
joblib so inference uses the exact same transformation as training.
"""
import logging
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.config import settings
from app.ml import feature_engineering, multimodal_fusion
from app.ml.data_loader import TARGET_COLUMN
from app.ml.validation import VALIDATION_RANGES

logger = logging.getLogger(__name__)

CATEGORICAL_COLUMNS = ["gender", "sport", "event_type", "previous_injury_type"]


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates(subset=["athlete_id"]) if "athlete_id" in df.columns else df.drop_duplicates()
    df = df.drop_duplicates()

    for col, (low, high) in VALIDATION_RANGES.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df.loc[(df[col] < low) | (df[col] > high), col] = np.nan
    return df


def build_preprocessing_pipeline(feature_columns: List[str]) -> Tuple[ColumnTransformer, List[str], List[str]]:
    categorical_cols = [c for c in feature_columns if c in CATEGORICAL_COLUMNS]
    numeric_cols = [c for c in feature_columns if c not in CATEGORICAL_COLUMNS]

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    preprocessor = ColumnTransformer([
        ("numeric", numeric_pipeline, numeric_cols),
        ("categorical", categorical_pipeline, categorical_cols),
    ])
    return preprocessor, numeric_cols, categorical_cols


def get_output_feature_names(preprocessor: ColumnTransformer, numeric_cols: List[str], categorical_cols: List[str]) -> List[str]:
    names = list(numeric_cols)
    if categorical_cols:
        encoder = preprocessor.named_transformers_["categorical"].named_steps["encoder"]
        names += list(encoder.get_feature_names_out(categorical_cols))
    return names


def prepare_dataset(df: pd.DataFrame, modalities: List[str] = None, test_size: float = 0.2):
    """clean -> engineer features -> fuse modalities -> stratified split -> fit preprocessing (train only)."""
    df = clean_dataset(df)
    df = feature_engineering.add_engineered_features(df)

    if modalities is None:
        modalities = list(multimodal_fusion.MODALITY_FEATURES.keys())
    feature_columns = multimodal_fusion.get_features_for_modalities(modalities)
    feature_columns = [c for c in feature_columns if c in df.columns]

    X = df[feature_columns]
    y = df[TARGET_COLUMN]

    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=settings.random_state
    )

    preprocessor, numeric_cols, categorical_cols = build_preprocessing_pipeline(feature_columns)
    X_train = preprocessor.fit_transform(X_train_raw)
    X_test = preprocessor.transform(X_test_raw)
    output_features = get_output_feature_names(preprocessor, numeric_cols, categorical_cols)

    return {
        "X_train": X_train, "X_test": X_test,
        "y_train": y_train.reset_index(drop=True), "y_test": y_test.reset_index(drop=True),
        "preprocessor": preprocessor, "feature_names": output_features,
        "raw_feature_columns": feature_columns,
    }

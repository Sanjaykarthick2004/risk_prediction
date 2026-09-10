"""Centralized backend configuration, loaded from environment variables (.env)."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "explainable_injury_ai"

    secret_key: str = "CHANGE_THIS_SECRET"
    access_token_expire_minutes: int = 60
    jwt_algorithm: str = "HS256"

    model_path: str = str(BACKEND_DIR / "models" / "xgboost_model.pkl")
    preprocessing_path: str = str(BACKEND_DIR / "models" / "preprocessing_pipeline.pkl")
    feature_columns_path: str = str(BACKEND_DIR / "models" / "feature_columns.pkl")
    shap_path: str = str(BACKEND_DIR / "models" / "shap_explainer.pkl")
    model_metrics_path: str = str(BACKEND_DIR / "models" / "model_metrics.json")

    raw_data_path: str = str(BACKEND_DIR / "data" / "raw" / "athlete_data.csv")
    processed_data_path: str = str(BACKEND_DIR / "data" / "processed" / "processed_data.csv")
    sample_data_path: str = str(BACKEND_DIR / "data" / "sample" / "sample_athlete_data.csv")

    figures_dir: str = str(BACKEND_DIR / "outputs" / "figures")
    metrics_dir: str = str(BACKEND_DIR / "outputs" / "metrics")
    shap_dir: str = str(BACKEND_DIR / "outputs" / "shap")
    reports_dir: str = str(BACKEND_DIR / "outputs" / "reports")

    cors_origins: str = "http://localhost:5173"
    frontend_url: str = "http://localhost:5173"

    reset_token_expire_minutes: int = 30

    # Risk classification thresholds — research/demonstration thresholds only,
    # NOT clinically validated.
    risk_threshold_low: float = 0.40
    risk_threshold_medium: float = 0.70

    random_state: int = 42
    model_version: str = "XGBoost-v2.0-running"

    # Size of the bundled SYNTHETIC DEMONSTRATION DATA generated for the
    # running-athlete injury-risk experiment (see app/ml/data_loader.py).
    # Configurable so the project can be re-run at a smaller size (faster,
    # for quick iteration) or larger size (more statistical power) on a
    # normal college laptop. 5,000-10,000 is the intended academic range;
    # avoid pushing this into the 100,000+ range without a reason.
    synthetic_dataset_size: int = 10000

    # Sample size used for global SHAP visualizations so the explainer never
    # has to recompute SHAP values across the entire (potentially 10,000+
    # row) dataset on every page load. Individual predictions always use the
    # athlete's own feature vector, never this sample.
    shap_global_sample_size: int = 800

    # extra="ignore": tolerate stray/legacy keys in .env (e.g. from an older
    # .env.example) instead of crashing the whole app on startup over an
    # unused setting.
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"), case_sensitive=False, extra="ignore",
    )

    @property
    def cors_origin_list(self):
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def model_post_init(self, __context) -> None:
        # .env may supply relative paths (e.g. "./models/xgboost_model.pkl"); resolve them
        # against BACKEND_DIR so behavior doesn't depend on the process's current directory
        # (e.g. when a notebook or test runs from a different cwd).
        for field in (
            "model_path", "preprocessing_path", "feature_columns_path", "shap_path",
            "model_metrics_path", "raw_data_path", "processed_data_path", "sample_data_path",
            "figures_dir", "metrics_dir", "shap_dir", "reports_dir",
        ):
            value = getattr(self, field)
            if not Path(value).is_absolute():
                object.__setattr__(self, field, str((BACKEND_DIR / value).resolve()))


settings = Settings()

"""ML pipeline tests run on a SMALL synthetic dataset (not the full 10,000-row
default) purely for test speed. These never call train_xgboost.train_and_persist
directly, so they never overwrite the real, already-trained model artifacts
under backend/models/ — only hyperparameter_tuning.tune_xgboost (a pure
function) and the save_outputs=False paths of model comparison / ablation
are exercised here.
"""
import pytest

from app.ml import ablation, hyperparameter_tuning, multimodal_fusion, preprocessing, train_models
from app.ml.data_loader import generate_synthetic_dataset, read_athlete_csv


@pytest.fixture(scope="module")
def small_dataset_path(tmp_path_factory):
    df = generate_synthetic_dataset(n_athletes=600, seed=11)
    path = tmp_path_factory.mktemp("data") / "small_running_dataset.csv"
    df.to_csv(path, index=False)
    return str(path)


def test_model_comparison_covers_all_six_models(small_dataset_path):
    results_df, trained_models, _ = train_models.run_model_comparison(save_outputs=False, data_path=small_dataset_path)
    expected = {"Logistic Regression", "Decision Tree", "Random Forest", "SVM", "Gradient Boosting", "XGBoost"}
    assert set(results_df.index) == expected
    for metric in ("accuracy", "precision", "recall", "f1_score", "roc_auc", "pr_auc", "specificity"):
        assert metric in results_df.columns
        assert results_df[metric].between(0, 1).all()


def test_xgboost_hyperparameter_search_returns_fitted_model_and_params(small_dataset_path):
    df = read_athlete_csv(small_dataset_path)
    data = preprocessing.prepare_dataset(df)
    best_model, best_params, best_score = hyperparameter_tuning.tune_xgboost(
        data["X_train"], data["y_train"], n_iter=3, cv_folds=3, apply_smote=True,
    )
    assert hasattr(best_model, "predict_proba")
    proba = best_model.predict_proba(data["X_test"])[:, 1]
    assert ((proba >= 0) & (proba <= 1)).all()
    expected_params = {
        "n_estimators", "max_depth", "learning_rate", "subsample",
        "colsample_bytree", "min_child_weight", "gamma", "reg_alpha", "reg_lambda",
    }
    assert set(best_params) == expected_params
    assert 0.0 <= best_score <= 1.0


def test_modality_ablation_runs_all_six_configurations(small_dataset_path):
    results_df = ablation.run_modality_ablation(save_outputs=False, data_path=small_dataset_path)
    assert set(results_df.index) == set(multimodal_fusion.ABLATION_CONFIGS.keys())
    for metric in ("f1_score", "recall", "roc_auc", "pr_auc"):
        assert metric in results_df.columns


def test_ablation_feature_counts_grow_from_m1_to_m6():
    """M1 (demographic-only) has the fewest features, M6 (all six modalities)
    has the most; M3/M4 are alternate branches (recovery vs. physiological
    added to M2) rather than a strictly nested chain, so only the endpoints
    and M2 (a common ancestor of both branches) are checked for ordering.
    """
    counts = {
        name: len(multimodal_fusion.get_features_for_modalities(mods))
        for name, mods in multimodal_fusion.ABLATION_CONFIGS.items()
    }
    assert counts["M1_demographic"] < counts["M2_demographic_training"]
    assert counts["M2_demographic_training"] < counts["M3_demographic_training_recovery"]
    assert counts["M2_demographic_training"] < counts["M4_demographic_training_physiological"]
    assert counts["M5_demo_training_physio_recovery_lifestyle"] < counts["M6_all_modalities"]
    assert counts["M1_demographic"] == min(counts.values())
    assert counts["M6_all_modalities"] == max(counts.values())

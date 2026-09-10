# Methodology

## Dataset
No real-world, clinically validated athlete injury dataset (with confirmed future injury
outcomes) is bundled with this project. `app/ml/data_loader.generate_synthetic_dataset()`
generates **SYNTHETIC DEMONSTRATION DATA** — clearly labelled as such everywhere it is used —
so the full pipeline can be built, trained, and demonstrated end-to-end. Results from this
data are software demonstrations of the framework, not real clinical or sports-science
findings. Real datasets could be substituted by uploading a CSV/Excel file with the same
columns via the Dataset page.

**Population**: running athletes only (`sport` = "Running" for every record), across five
`event_type` values (Sprint, Middle Distance, Long Distance, Cross Country, General Running) —
see [project_overview.md](project_overview.md) for why this experiment uses a single-sport
population rather than the small multi-sport sample an earlier prototype version used.

**Size**: `settings.synthetic_dataset_size` records (default **10,000**; configurable —
1,000/5,000/10,000/20,000 are all reasonable choices on a normal college laptop, avoid pushing
this into the 100,000+ range without a reason). Generation is fully reproducible:
`numpy.random.default_rng(seed)` with `seed` defaulting to `settings.random_state` (42).

**Generation method**: every field is drawn from a distribution (normal/uniform/integer/
categorical) with ranges chosen to look like a plausible running-athlete sample — not sampled
from, or fit to, any real dataset. Event-type-specific profiles (`EVENT_TYPE_PROFILE` in
`data_loader.py`) give Sprint/Middle Distance/Long Distance/Cross Country/General Running
different typical weekly distance, long-run fraction, and speed-work-session ranges. A handful
of fields are deliberately **not independent** (a modeling choice for a meaningful
demonstration, not a scientifically validated causal claim):
- higher acute:chronic workload ratio → higher fatigue/soreness (weakly, plus noise)
- lower sleep hours → lower recovery score (weakly, plus noise)
- previous injury / more prior injuries → higher modeled injury-risk score

**Target generation**: `injury_next_7_days` is sampled from a logistic function of a latent risk
score built from a subset of the above fields (workload ratio, fatigue, soreness, stress, sleep,
speed-work volume, injury history, experience) plus substantial independent random noise — see
`app/ml/data_loader._generate_target`. A constant offset (`_BASE_RATE_OFFSET`) shifts the
average modeled probability down to a demonstration base rate of ~15-20% positive cases (the
actual generated rate is ~23.7%), closer to a plausible weekly injury incidence than a coin
flip, while leaving the dataset naturally — not resampling-forced — imbalanced. This is a
modeling choice for the demonstration dataset, not a measured epidemiological rate, and must
never be described as one. Synthetic labels must never be described as real observed injuries.

## Avoiding Target Leakage
The target `injury_next_7_days` is **not** copied or thresholded directly from a predictor.
The synthetic generator instead builds a latent risk score from a subset of features (workload
ratio, fatigue, stress, sleep, injury history, experience) **plus substantial independent
random noise**, then samples the binary outcome from the resulting probability. This keeps the
relationship plausible without making the target a deterministic function of any input — the
same discipline a real dataset would need (the target must be a genuinely separate outcome
column, e.g. actually observed injuries in the following week, not derived from the same row's
predictors).

## Reading dataset CSVs (`app/ml/data_loader.read_athlete_csv`)
`previous_injury_type` legitimately uses the literal string `"None"` as a category (no prior
injury). pandas' default CSV reader treats `"None"`/`"NA"`/`"NULL"`/etc. as missing values,
which would silently turn every "no prior injury" row into a fake missing value in every
data-quality report. Every CSV read in this app (`load_raw_data`, dataset upload/validate/
process) uses `keep_default_na=False, na_values=[""]` instead, so only an actually-empty cell
counts as missing.

## Preprocessing (`app/ml/preprocessing.py`)
1. `clean_dataset` — drop duplicate `athlete_id` rows and duplicate full rows; clip
   out-of-range numeric values to `NaN` (rather than silently keeping impossible values).
2. `add_engineered_features` — see below.
3. Modality-based column selection (`multimodal_fusion.py`).
4. Stratified 80/20 train/test split (`random_state` fixed for reproducibility).
5. `ColumnTransformer`: numeric columns → median imputation + standard scaling; categorical
   columns → most-frequent imputation + one-hot encoding. **Fit only on the training split.**
6. The fitted pipeline is persisted with `joblib` and reused unchanged at prediction time.

## Feature Engineering (`app/ml/feature_engineering.py`)
| Feature | Formula | Modality | Rationale |
|---|---|---|---|
| `bmi` | weight_kg / height_m² | Demographic | Standard body-composition indicator |
| `workload_ratio` | acute_load / chronic_load | Training | ACWR — training-load spike proxy |
| `training_load_per_hour` | training_load / hours_per_week | Training | Training density vs. raw volume |
| `recovery_gap` | rest_days − recovery_days | Recovery | Under-resting relative to need |
| `sleep_deficit` | max(0, 8 − sleep_hours) | Recovery | Chronic sleep shortfall |
| `stress_fatigue_index` | mean(stress, fatigue, soreness) | Lifestyle+Physio | Aggregated strain |
| `injury_history_score` | prior_injury × (1+count) / (1+days/365) | Injury History | Recency-weighted burden |
| `training_recovery_balance` | training_load / (recovery_score+1) | Training+Physio | Demand vs. recovery capacity |

Division-by-zero is always handled by replacing a zero denominator with `NaN` before dividing
and filling the result with a safe default (never crashes, never produces `inf`).

## Multimodal Fusion (`app/ml/multimodal_fusion.py`)
Feature-level fusion: each modality contributes a fixed list of columns; `get_features_for_modalities`
concatenates them into one feature vector per athlete-assessment row. No deep-learning fusion
architecture is used — this keeps the pipeline explainable end-to-end with SHAP.

## Model Comparison (`app/ml/train_models.py`)
Logistic Regression, Decision Tree, Random Forest, SVM, Gradient Boosting, and default XGBoost
are trained on an identical preprocessed training split and evaluated on the same held-out
test split.

## Class Imbalance
`maybe_apply_smote` checks the minority-class ratio; if it drops below 0.4 it applies SMOTE —
**to the training split only**, never to the test split (`app/ml/train_models.py`). The running
dataset's ~23.7% positive rate triggers this.

For a single, non-cross-validated model fit (the default-vs-optimized comparison's "default"
baseline, and every model in the Experiment 1 comparison), applying SMOTE once to the training
split before that single fit is safe — there is no fold boundary for a synthetic sample to leak
across. **Inside cross-validation, this is different and requires more care**: resampling once
and then K-folding the already-resampled data lets synthetic minority samples (near-duplicates
of real ones) land in a fold's training partition while a near-identical real sample sits in
that fold's validation partition, leaking information across the split and inflating CV scores.
`app/ml/hyperparameter_tuning.py` and `train_xgboost.cross_validate_model` avoid this by
building an `imblearn.pipeline.Pipeline` (SMOTE + the classifier) and running
`RandomizedSearchCV`/`cross_validate` on the **original, unbalanced** training split — SMOTE is
then refit fresh inside every fold. This was caught during development: with the old
(pre-fix) approach, CV F1 read ~0.82 on this dataset while genuine held-out test F1 was ~0.11 —
a textbook leakage symptom — and it silently misled hyperparameter selection into picking
parameters that looked good on leaked folds rather than parameters that generalize. See
`docs/experiments.md` Experiment 2 for the before/after numbers.

## XGBoost Optimization (`app/ml/hyperparameter_tuning.py`, `train_xgboost.py`)
`RandomizedSearchCV` over `n_estimators`, `max_depth`, `learning_rate`, `subsample`,
`colsample_bytree`, `min_child_weight`, `gamma`, `reg_alpha`, `reg_lambda`, scored on F1 with
5-fold stratified cross-validation (SMOTE applied fresh inside each fold as described above).
The resulting best estimator is evaluated on the held-out test set and compared against a
default-hyperparameter XGBoost baseline.

## SHAP Explainability (`app/ml/shap_explainer.py`)
`shap.TreeExplainer` on the trained XGBoost model.
- **Global**: mean absolute SHAP value per feature over a test-set sample.
- **Local**: SHAP values for one prediction's preprocessed feature row, split into positive
  ("top risk factors") and negative ("protective factors") contributors.
- **Dependence**: SHAP value vs. feature value across a test-set sample, for a chosen feature.

SHAP values describe how a feature moved the *model's own output* — the application always
phrases this as "contributed to the model's prediction," never as a causal claim about injury.

## Modality Ablation (`app/ml/ablation.py`)
XGBoost is retrained from scratch on six cumulative modality configurations (M1 demographic-only
through M6 all-modalities) and compared on F1, recall, ROC-AUC, and PR-AUC — testing H1.

# Architecture

## High-Level Flow

```
React Frontend (Vite)
      |
    Axios (JWT bearer token)
      |
FastAPI Backend
  - API routes (auth, athletes, assessments, datasets, training, evaluation,
    predictions, explainability, reports, dashboard)
  - Pydantic validation
  - Service layer (business logic)
      |            |
      v            v
  ML Engine    MongoDB (PyMongo)
  (app/ml/*)   users, athletes, assessments,
               predictions, shap_explanations
```

## Frontend/Backend Separation
React never talks to MongoDB, the XGBoost model, or the SHAP explainer directly. Every piece
of data flows: **React → Axios → FastAPI route → service → (MongoDB and/or ML engine) → JSON → React**.

## Backend Layers
- **`app/api/`** — FastAPI routers. Thin: parse request, call a service, return its result.
- **`app/schemas/`** — Pydantic request/response models (validation happens here).
- **`app/services/`** — business logic: athlete/assessment CRUD, auth, training orchestration,
  prediction orchestration, SHAP/report assembly, dashboard aggregation.
- **`app/ml/`** — the actual machine-learning code: data loading, validation, preprocessing,
  feature engineering, multimodal fusion, model comparison, XGBoost training/optimization,
  evaluation metrics, SHAP explainability, modality ablation, and the single-athlete prediction
  pipeline. This code has no FastAPI or MongoDB imports — it is pure ML and is what the
  notebooks also import, so there is exactly one implementation of the ML logic.
- **`app/database/mongodb.py`** — the only place PyMongo is used.
- **`app/core/`** — security (bcrypt/JWT), FastAPI dependencies, logging, constants.

## Prediction Pipeline (single athlete)
```
Assessment input (6 modality dicts)
      -> flatten into one row
      -> feature engineering (same function used at training time)
      -> preprocessing pipeline (fit at training time, loaded via joblib)
      -> XGBoost.predict_proba
      -> risk classification (LOW/MEDIUM/HIGH thresholds)
      -> SHAP TreeExplainer local explanation
      -> stored in MongoDB (predictions, shap_explanations)
      -> returned as JSON to React
```

## Why MongoDB (not SQL)
This project deliberately uses MongoDB/PyMongo instead of PostgreSQL/SQLAlchemy, matching the
"college project" scope: no migrations system, no ORM relationship mapping — just five
straightforward collections with a handful of indexes (see [database_design.md](database_design.md)).

## Why synchronous training (not a task queue)
Model training happens inside a normal HTTP request. For the bundled 10,000-row running-athlete
dataset, measured runs ranged from ~1.5-2 minutes (quiet system) up to several minutes (system
under load, e.g. other heavy processes competing for CPU) for the 6-model baseline comparison
or the XGBoost optimize step; the modality ablation is consistently well under 30 seconds.
There is no fixed target time — `model_metrics.json`'s `training_time_seconds` field always
records the actual duration of the last real run, which is what the app displays rather than
a documented estimate. All of this is on a normal laptop CPU, no GPU required. The frontend
disables the triggering button and shows a loading indicator while a run is in progress. A task
queue (Celery, RQ) was deliberately not introduced, per the project's "no over-engineering"
constraint; kernel SVM (the slowest baseline model) is capped to a stratified subsample of its
SMOTE-balanced training data (`app/ml/train_models.py: MAX_SVM_TRAIN_SIZE`) since SVC training
time scales very poorly with dataset size — every other model, and the shared held-out test
set, are unaffected.

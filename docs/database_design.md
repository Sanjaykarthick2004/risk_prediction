# Database Design (MongoDB)

Connection: `mongodb://localhost:27017`, database `explainable_injury_ai` (configurable via
`backend/.env`). Accessed only through `app/database/mongodb.py` (PyMongo).

## Collections

### `users`
```json
{ "username": "researcher1", "password_hash": "<bcrypt hash>", "role": "RESEARCHER", "created_at": "..." }
```
Index: unique on `username`. Passwords are always bcrypt-hashed; plaintext is never stored or logged.

### `athletes`
```json
{
  "athlete_id": "ATH-001", "name": "...", "age": 21, "gender": "Male", "sport": "Running",
  "event_type": "Long Distance", "height": 175, "weight": 62, "experience_years": 5,
  "created_at": "...", "updated_at": "..."
}
```
`sport` is currently always `"Running"` — this experiment's research population is running
athletes only (see [project_overview.md](project_overview.md)); `event_type` distinguishes the
running disciplines (Sprint / Middle Distance / Long Distance / Cross Country / General Running).
Index: unique on `athlete_id` (the application-level primary identifier — no other PII, such
as phone/address/government ID, is collected).

### `assessments`
```json
{
  "assessment_id": "ASM-...", "athlete_id": "ATH-001", "assessment_date": "...",
  "demographic": { "age": 21, "gender": "Male", "...": "snapshot from athletes at assessment time" },
  "training": { "training_hours_per_week": 12, "...": "..." },
  "physiological": { "...": "..." },
  "recovery": { "...": "..." },
  "lifestyle": { "...": "..." },
  "injury_history": { "...": "..." }
}
```
Indexes: `athlete_id`, `assessment_date`. Each of the six modalities is a nested sub-document
matching the Pydantic schemas in `app/schemas/assessment.py`.

### `predictions`
```json
{
  "prediction_id": "PRED-...", "athlete_id": "ATH-001", "assessment_id": "ASM-...",
  "probability": 0.58, "risk_level": "MEDIUM", "model_version": "XGBoost-v2.0-running",
  "prediction_date": "...", "top_risk_factors": [...], "protective_factors": [...]
}
```
Indexes: `athlete_id`, `prediction_date`.

### `shap_explanations`
```json
{ "prediction_id": "PRED-...", "feature": "sleep_hours", "feature_value": 5.5, "shap_value": -0.03, "contribution_type": "protective" }
```
Index: `prediction_id`. One document per feature per prediction, so a prediction's full SHAP
breakdown can be re-fetched without re-running the model.

## Relationships
```
users (independent — application accounts, not linked to athlete data)

athletes
   └── assessments (by athlete_id)
          └── predictions (by athlete_id + assessment_id)
                 └── shap_explanations (by prediction_id)
```

Relationships are enforced in the service layer (e.g. `assessment_service.create_assessment`
looks up the athlete and 404s if missing) rather than by MongoDB foreign keys, since MongoDB
has none — this is the simplification appropriate for a document database in a college project.

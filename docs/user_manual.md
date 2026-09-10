# User Manual

## 1. Start MongoDB
Make sure the MongoDB Community Server service is running (Windows Services →
`MongoDB`, or `net start MongoDB`). Default: `mongodb://localhost:27017`.

## 2. Start the backend
```bash
cd backend
venv\Scripts\activate
python run.py
```
Backend runs at `http://localhost:8000`. Visit `http://localhost:8000/docs` for interactive
API docs.

## 3. Start the frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`.

## 4. Register / Login
Open `http://localhost:5173` → "New researcher? Register" → create a username/password →
you're logged in (JWT stored in the browser).

## 5. Train the model (first time only)
The bundled dataset is 10,000 synthetic running-athlete records by default — training runs
synchronously and takes longer than a tiny dataset would, but is still laptop-friendly (no GPU
needed). Go to **Model Training**:
1. Click **Run Model Comparison** — trains and compares 6 baseline algorithms (a couple of
   minutes on a quiet system, longer if the machine is under load; the button is disabled and
   a loading indicator shown while it runs).
2. Click **Train & Optimize XGBoost** — this is the one that actually produces the model
   artifacts used for prediction (`models/xgboost_model.pkl`, etc.): a default fit, a
   30-iteration hyperparameter search with 5-fold CV, and a final CV report. The exact duration
   varies with system load — the Model Training page always shows the actual measured time
   from the last real run, not an estimate.
3. (Optional) Click **Run Modality Ablation** to reproduce the M1–M6 experiment (~15 seconds).

Until step 2 completes at least once, the Prediction page will return a
"Model artifacts not found" error — this is expected, not a bug.

## 6. Add an athlete
Go to **Athletes → + Add Athlete**, fill in the demographic profile, save.

## 7. Run a prediction
Go to **Prediction**, select the athlete, fill in the six-modality assessment form, click
**Predict Injury Risk**. You'll see the probability, LOW/MEDIUM/HIGH risk level, and the
top risk/protective factors (from SHAP) — all computed live, nothing is pre-canned.

## 8. Explore explainability
Go to **Explainability** to see:
- Global SHAP feature importance (bar chart, over a test-set sample).
- Individual waterfall: paste a `prediction_id` (from Prediction History) to see every
  feature's contribution to that one prediction.
- Feature dependence: pick a feature to see how its value relates to its SHAP contribution.

## 9. Check evaluation
Go to **Evaluation** for the model comparison table, confusion matrix, ROC curve, and
precision-recall curve — computed from the currently persisted model and a reproducible
test split.

## 10. Generate a report
Go to **Reports**, paste a `prediction_id`, and click **Print / Save as PDF** (uses the
browser's native print dialog — no extra PDF library needed).

## 11. Prediction history
Go to **Prediction History** to see every prediction ever made, with links into
Explainability and Reports for each one.

## Troubleshooting
- **Dashboard shows "database: unavailable"** — MongoDB isn't running, or `MONGODB_URI` in
  `backend/.env` is wrong.
- **Prediction fails with 409 "Model artifacts not found"** — run Model Training → Train &
  Optimize XGBoost first.
- **CORS error in the browser console** — check `CORS_ORIGINS` in `backend/.env` matches the
  frontend's actual origin (default `http://localhost:5173`).

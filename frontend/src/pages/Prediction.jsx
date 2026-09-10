import {
  Activity, AlertOctagon, Brain, ClipboardCheck, Coffee, HeartPulse, ShieldAlert, Target, User,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { listAthletes } from "../api/athleteApi";
import { createAssessment } from "../api/assessmentApi";
import { createPrediction } from "../api/predictionApi";
import {
  Alert, Button, Card, FormField, PageHeader, RiskBadge, Stepper, useToast,
} from "../components/ui";
import { extractErrorMessage } from "../components/common/ErrorMessage";

// Mirrors app/config.py Settings.risk_threshold_low/medium and app/ml/prediction.classify_risk —
// not exposed via an API endpoint, so duplicated here; these are application/model
// thresholds, not clinically validated cut-points (see the disclaimer below).
const RISK_THRESHOLDS = { low: 0.40, medium: 0.70 };

const DEFAULTS = {
  training: { training_hours_per_week: 8, training_frequency: 5, training_intensity: 6, weekly_distance_km: 35, long_run_distance_km: 10, speed_work_sessions: 1, training_load: 500, acute_training_load: 500, chronic_training_load: 500 },
  physiological: { resting_heart_rate: 65, heart_rate_variability: 60, fatigue_score: 5, muscle_soreness: 5, recovery_score: 65 },
  recovery: { sleep_hours: 7, sleep_quality: 6, recovery_days: 2, rest_days: 2 },
  lifestyle: { stress_level: 5, hydration_score: 70, nutrition_score: 70 },
  injury_history: { previous_injury: 0, injury_count: 0, previous_injury_type: "None", days_since_previous_injury: 3650, previous_recovery_duration: 0 },
};

const STEPS = [
  { key: "athlete", label: "Athlete", icon: User },
  { key: "training", label: "Training", icon: Activity },
  { key: "physiological", label: "Physiological", icon: HeartPulse },
  { key: "recovery", label: "Recovery", icon: Coffee },
  { key: "lifestyle", label: "Lifestyle", icon: Brain },
  { key: "injury_history", label: "Previous Injury", icon: ShieldAlert },
  { key: "review", label: "Review", icon: ClipboardCheck },
];

export default function Prediction() {
  const toast = useToast();
  const [params] = useSearchParams();
  const [athletes, setAthletes] = useState([]);
  const [athleteId, setAthleteId] = useState(params.get("athlete_id") || "");
  const [form, setForm] = useState(JSON.parse(JSON.stringify(DEFAULTS)));
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [modelNotReady, setModelNotReady] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => { listAthletes().then(setAthletes); }, []);

  function updateField(section, field, value) {
    setForm((f) => ({ ...f, [section]: { ...f[section], [field]: value } }));
  }

  const step = STEPS[stepIndex];
  const selectedAthlete = athletes.find((a) => a.athlete_id === athleteId);
  const canGoNext = step.key !== "athlete" || !!athleteId;

  async function handleGenerate() {
    setBusy(true);
    setError("");
    setModelNotReady(false);
    setResult(null);
    try {
      const numericForm = numerify(form);
      const assessment = await createAssessment(athleteId, numericForm);
      const prediction = await createPrediction({ athlete_id: athleteId, assessment_id: assessment.assessment_id, ...numericForm });
      setResult(prediction);
      toast("Prediction generated successfully.", "success");
    } catch (err) {
      if (err?.response?.status === 409) {
        setModelNotReady(true);
      } else {
        setError(extractErrorMessage(err));
        toast("Prediction could not be generated.", "error");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader
        icon={Target}
        title="Injury Risk Prediction"
        description="Work through the six-modality assessment, then generate an explainable injury-risk prediction."
      />

      {modelNotReady && (
        <div className="card model-not-ready">
          <AlertOctagon size={28} color="var(--red)" />
          <div>
            <h3>Model Not Ready</h3>
            <p className="text-secondary">The XGBoost model has not been trained yet. Please go to:</p>
            <p className="not-ready-path">
              <Link to="/training">Model Training</Link> → <b>Train &amp; Optimize XGBoost</b>
            </p>
          </div>
        </div>
      )}

      <Card>
        <Stepper
          steps={STEPS}
          active={step.key}
          completed={STEPS.slice(0, stepIndex).map((s) => s.key)}
          onStepClick={(key) => setStepIndex(STEPS.findIndex((s) => s.key === key))}
        />

        {step.key === "athlete" && (
          <FormField label="Select Athlete" required wide>
            <select value={athleteId} onChange={(e) => setAthleteId(e.target.value)} required>
              <option value="">-- Select Athlete --</option>
              {athletes.map((a) => <option key={a.athlete_id} value={a.athlete_id}>{a.athlete_id} — {a.name} ({a.event_type})</option>)}
            </select>
          </FormField>
        )}

        {step.key === "training" && (
          <div className="form-grid">
            <FormField label="Training Hours/Week" unit="hrs"><Num value={form.training.training_hours_per_week} onChange={(v) => updateField("training", "training_hours_per_week", v)} /></FormField>
            <FormField label="Training Frequency" unit="days/week"><Num value={form.training.training_frequency} onChange={(v) => updateField("training", "training_frequency", v)} /></FormField>
            <FormField label="Training Intensity" unit="1–10"><Num value={form.training.training_intensity} onChange={(v) => updateField("training", "training_intensity", v)} /></FormField>
            <FormField label="Weekly Distance" unit="km"><Num value={form.training.weekly_distance_km} onChange={(v) => updateField("training", "weekly_distance_km", v)} /></FormField>
            <FormField label="Long Run Distance" unit="km"><Num value={form.training.long_run_distance_km} onChange={(v) => updateField("training", "long_run_distance_km", v)} /></FormField>
            <FormField label="Speed Work Sessions" unit="/week"><Num value={form.training.speed_work_sessions} onChange={(v) => updateField("training", "speed_work_sessions", v)} /></FormField>
            <FormField label="Training Load"><Num value={form.training.training_load} onChange={(v) => updateField("training", "training_load", v)} /></FormField>
            <FormField label="Acute Training Load"><Num value={form.training.acute_training_load} onChange={(v) => updateField("training", "acute_training_load", v)} /></FormField>
            <FormField label="Chronic Training Load"><Num value={form.training.chronic_training_load} onChange={(v) => updateField("training", "chronic_training_load", v)} /></FormField>
          </div>
        )}

        {step.key === "physiological" && (
          <div className="form-grid">
            <FormField label="Resting Heart Rate" unit="bpm"><Num value={form.physiological.resting_heart_rate} onChange={(v) => updateField("physiological", "resting_heart_rate", v)} /></FormField>
            <FormField label="Heart Rate Variability" unit="ms"><Num value={form.physiological.heart_rate_variability} onChange={(v) => updateField("physiological", "heart_rate_variability", v)} /></FormField>
            <FormField label="Fatigue" unit="1–10"><Num value={form.physiological.fatigue_score} onChange={(v) => updateField("physiological", "fatigue_score", v)} /></FormField>
            <FormField label="Muscle Soreness" unit="1–10"><Num value={form.physiological.muscle_soreness} onChange={(v) => updateField("physiological", "muscle_soreness", v)} /></FormField>
            <FormField label="Recovery Score" unit="/100"><Num value={form.physiological.recovery_score} onChange={(v) => updateField("physiological", "recovery_score", v)} /></FormField>
          </div>
        )}

        {step.key === "recovery" && (
          <div className="form-grid">
            <FormField label="Sleep Duration" unit="hrs/night"><Num value={form.recovery.sleep_hours} onChange={(v) => updateField("recovery", "sleep_hours", v)} /></FormField>
            <FormField label="Sleep Quality" unit="1–10"><Num value={form.recovery.sleep_quality} onChange={(v) => updateField("recovery", "sleep_quality", v)} /></FormField>
            <FormField label="Recovery Days" unit="days"><Num value={form.recovery.recovery_days} onChange={(v) => updateField("recovery", "recovery_days", v)} /></FormField>
            <FormField label="Rest Days" unit="days"><Num value={form.recovery.rest_days} onChange={(v) => updateField("recovery", "rest_days", v)} /></FormField>
          </div>
        )}

        {step.key === "lifestyle" && (
          <div className="form-grid">
            <FormField label="Stress Level" unit="1–10"><Num value={form.lifestyle.stress_level} onChange={(v) => updateField("lifestyle", "stress_level", v)} /></FormField>
            <FormField label="Hydration Score" unit="/100"><Num value={form.lifestyle.hydration_score} onChange={(v) => updateField("lifestyle", "hydration_score", v)} /></FormField>
            <FormField label="Nutrition Score" unit="/100"><Num value={form.lifestyle.nutrition_score} onChange={(v) => updateField("lifestyle", "nutrition_score", v)} /></FormField>
          </div>
        )}

        {step.key === "injury_history" && (
          <div className="form-grid">
            <FormField label="Previous Injury">
              <select value={form.injury_history.previous_injury} onChange={(e) => updateField("injury_history", "previous_injury", e.target.value)}>
                <option value={0}>No</option>
                <option value={1}>Yes</option>
              </select>
            </FormField>
            <FormField label="Injury Count"><Num value={form.injury_history.injury_count} onChange={(v) => updateField("injury_history", "injury_count", v)} /></FormField>
            <FormField label="Previous Injury Type">
              <select value={form.injury_history.previous_injury_type} onChange={(e) => updateField("injury_history", "previous_injury_type", e.target.value)}>
                {["None", "Shin Splints", "Runner's Knee", "IT Band Syndrome", "Ankle Injury", "Hamstring Strain", "Stress Injury", "Other"].map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </FormField>
            <FormField label="Days Since Previous Injury" unit="days"><Num value={form.injury_history.days_since_previous_injury} onChange={(v) => updateField("injury_history", "days_since_previous_injury", v)} /></FormField>
            <FormField label="Previous Recovery Duration" unit="days"><Num value={form.injury_history.previous_recovery_duration} onChange={(v) => updateField("injury_history", "previous_recovery_duration", v)} /></FormField>
          </div>
        )}

        {step.key === "review" && (
          <div className="review-step">
            <p className="text-secondary">
              Reviewing assessment for <b>{selectedAthlete ? `${selectedAthlete.name} (${selectedAthlete.athlete_id})` : athleteId}</b>.
              Go back to any step to make changes.
            </p>
            <div className="detail-grid">
              <div><b>Training Hours/Week</b><br />{form.training.training_hours_per_week}</div>
              <div><b>Weekly Distance</b><br />{form.training.weekly_distance_km} km</div>
              <div><b>Fatigue</b><br />{form.physiological.fatigue_score}/10</div>
              <div><b>Recovery Score</b><br />{form.physiological.recovery_score}/100</div>
              <div><b>Sleep</b><br />{form.recovery.sleep_hours} hrs</div>
              <div><b>Stress Level</b><br />{form.lifestyle.stress_level}/10</div>
              <div><b>Previous Injury</b><br />{form.injury_history.previous_injury ? "Yes" : "No"}</div>
            </div>

            {error && <Alert tone="error" title="We couldn't generate this prediction." details={error}>Please try again. If the problem continues, check the backend service.</Alert>}

            <Button icon={Target} loading={busy} onClick={handleGenerate} size="lg">
              {busy ? "Generating Prediction…" : "Generate Prediction"}
            </Button>
          </div>
        )}

        <div className="stepper-nav">
          <Button variant="ghost" disabled={stepIndex === 0} onClick={() => setStepIndex((i) => i - 1)}>Back</Button>
          {step.key !== "review" && (
            <Button disabled={!canGoNext} onClick={() => setStepIndex((i) => i + 1)}>Next</Button>
          )}
        </div>
      </Card>

      {result && <PredictionResult result={result} athlete={selectedAthlete} />}
    </div>
  );
}

function numerify(form) {
  const out = {};
  for (const section of Object.keys(form)) {
    out[section] = {};
    for (const [k, v] of Object.entries(form[section])) {
      out[section][k] = k === "previous_injury_type" ? v : Number(v);
    }
  }
  return out;
}

function Num({ value, onChange }) {
  return <input type="number" step="any" value={value} onChange={(e) => onChange(e.target.value)} required />;
}

function RiskScale({ probability }) {
  const pct = Math.round(probability * 100);
  return (
    <div className="risk-scale">
      <div className="risk-scale-track">
        <span className="risk-scale-seg risk-scale-low" style={{ width: `${RISK_THRESHOLDS.low * 100}%` }} />
        <span className="risk-scale-seg risk-scale-medium" style={{ width: `${(RISK_THRESHOLDS.medium - RISK_THRESHOLDS.low) * 100}%` }} />
        <span className="risk-scale-seg risk-scale-high" style={{ width: `${(1 - RISK_THRESHOLDS.medium) * 100}%` }} />
        <span className="risk-scale-marker" style={{ left: `${pct}%` }}>{pct}%</span>
      </div>
      <div className="risk-scale-labels">
        <span>LOW · 0%</span>
        <span>MEDIUM · {Math.round(RISK_THRESHOLDS.low * 100)}%</span>
        <span>HIGH · {Math.round(RISK_THRESHOLDS.medium * 100)}%</span>
        <span>100%</span>
      </div>
      <p className="text-caption" style={{ marginTop: 6 }}>
        Application/model thresholds — not clinically validated cut-points.
      </p>
    </div>
  );
}

function PredictionResult({ result, athlete }) {
  return (
    <div className="card result-card">
      <div className="page-header" style={{ marginBottom: 4 }}>
        <h3>Injury Risk Assessment</h3>
        <span className="prediction-id-chip">{result.prediction_id}</span>
      </div>
      <div className="result-row">
        <div>
          <div className="text-secondary">Probability</div>
          <div className="big-number">{(result.probability * 100).toFixed(1)}%</div>
        </div>
        <div>
          <div className="text-secondary">Risk Level</div>
          <RiskBadge level={result.risk_level} size="lg" />
        </div>
        <div>
          <div className="text-secondary">Athlete</div>
          <div>{athlete ? athlete.name : result.athlete_id}</div>
        </div>
        <div>
          <div className="text-secondary">Model</div>
          <div>{result.model_version}</div>
        </div>
      </div>

      <RiskScale probability={result.probability} />

      <div className="result-actions">
        <Button variant="ghost" size="sm" to={`/explainability?prediction_id=${result.prediction_id}`}>View SHAP Explanation</Button>
        <Button variant="ghost" size="sm" to={`/reports?prediction_id=${result.prediction_id}`}>Generate Report</Button>
      </div>

      <div className="factors-grid">
        <div>
          <h4>Top Risk Factors</h4>
          <ul className="factor-list risk">
            {result.top_risk_factors.map((f) => (
              <li key={f.feature}>{f.feature} <span className="shap-value">(+{f.shap_value.toFixed(3)})</span></li>
            ))}
          </ul>
        </div>
        <div>
          <h4>Protective Factors</h4>
          <ul className="factor-list protective">
            {result.protective_factors.map((f) => (
              <li key={f.feature}>{f.feature} <span className="shap-value">({f.shap_value.toFixed(3)})</span></li>
            ))}
          </ul>
        </div>
      </div>

    </div>
  );
}

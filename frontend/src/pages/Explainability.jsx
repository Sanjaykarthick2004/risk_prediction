import { Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ScatterChart, Scatter } from "recharts";
import { getDependence, getGlobalExplanation, getWaterfall } from "../api/shapApi";
import { Alert, Card, EmptyState, FormField, PageHeader, RiskBadge, Tooltip as UiTooltip } from "../components/ui";
import { extractErrorMessage } from "../components/common/ErrorMessage";
import Loading from "../components/common/Loading";

const DEPENDENCE_FEATURES = ["workload_ratio", "fatigue_score", "sleep_hours", "stress_level", "previous_injury", "recovery_score"];

export default function Explainability() {
  const [params] = useSearchParams();
  const [global, setGlobal] = useState(null);
  const [waterfall, setWaterfall] = useState(null);
  const [waterfallError, setWaterfallError] = useState("");
  const [predictionId, setPredictionId] = useState(params.get("prediction_id") || "");
  const [feature, setFeature] = useState("");
  const [dependence, setDependence] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getGlobalExplanation().then(setGlobal).catch((err) => setError(extractErrorMessage(err)));
  }, []);

  useEffect(() => {
    if (predictionId) {
      setWaterfallError("");
      getWaterfall(predictionId).then(setWaterfall).catch((err) => setWaterfallError(extractErrorMessage(err)));
    } else {
      setWaterfall(null);
    }
  }, [predictionId]);

  async function loadDependence(feat) {
    setFeature(feat);
    try {
      setDependence(await getDependence(feat));
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  const positive = waterfall?.contributions_by_magnitude.filter((c) => c.shap_value > 0) || [];
  const negative = waterfall?.contributions_by_magnitude.filter((c) => c.shap_value <= 0) || [];

  return (
    <div>
      <PageHeader
        icon={Sparkles}
        title="Explainability"
        description="SHAP values show how each feature contributed to (or reduced) the model's prediction. They describe model behavior — not medical causation."
      />
      {error && <Alert tone="error" title="We couldn't load explainability data.">{error}</Alert>}

      <Card
        title="Global Model Explanation"
        description="Which features matter most to the model overall, computed from a sample of the held-out test set."
      >
        {!global && <Loading text="Preparing SHAP explanation... (train the model first if empty)" />}
        {global && (
          <>
            <ResponsiveContainer width="100%" height={Math.max(300, global.feature_importance.length * 28)}>
              <BarChart data={global.feature_importance} layout="vertical" margin={{ left: 140 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="feature" width={140} />
                <Tooltip />
                <Bar dataKey="mean_abs_shap" name="Mean |SHAP|" fill="var(--ai-accent)" />
              </BarChart>
            </ResponsiveContainer>
            <p className="text-caption">Based on {global.n_samples_used} sampled test-set rows.</p>
          </>
        )}
      </Card>

      <Card
        title="Why did the model make this prediction?"
        description="Explore the features that contributed most to the model's current prediction."
      >
        <FormField label="Prediction ID" helper="Paste an ID from Prediction History.">
          <input value={predictionId} onChange={(e) => setPredictionId(e.target.value)} placeholder="PRED-xxxxxxxxxxxx" />
        </FormField>

        {waterfallError && <Alert tone="error">{waterfallError}</Alert>}

        {!predictionId && !waterfallError && (
          <EmptyState icon={Sparkles} title="No prediction selected" description="Enter a prediction ID above, or open a prediction from Prediction History." />
        )}

        {waterfall && (
          <div>
            <div className="result-row" style={{ margin: "6px 0 18px" }}>
              <div>
                <div className="text-secondary">Predicted Probability</div>
                <div className="big-number" style={{ fontSize: "1.6rem" }}>{(waterfall.probability * 100).toFixed(1)}%</div>
              </div>
              <div>
                <div className="text-secondary">Risk Level</div>
                <RiskBadge level={waterfall.risk_level} size="lg" />
              </div>
            </div>

            <div className="factors-grid">
              <div>
                <h4>Increased Predicted Risk</h4>
                <ContributionBars items={positive} tone="risk" />
              </div>
              <div>
                <h4>Reduced Predicted Risk</h4>
                <ContributionBars items={negative} tone="protective" />
              </div>
            </div>

            <UiTooltip text="SHAP values describe how features contributed to the model's prediction. They do not establish causal relationships.">
              <p className="text-caption" style={{ marginTop: 14, cursor: "help", textDecoration: "underline dotted" }}>
                What do these values mean?
              </p>
            </UiTooltip>
          </div>
        )}
      </Card>

      <Card title="Feature Dependence" description="How a feature's value relates to its effect on the model's prediction, across a sample of the test set.">
        <div className="feature-picker">
          {DEPENDENCE_FEATURES.map((f) => (
            <button key={f} className={`btn btn-sm ${feature === f ? "btn-primary" : "btn-ghost"}`} onClick={() => loadDependence(f)}>{f}</button>
          ))}
        </div>
        {!dependence && <EmptyState icon={Sparkles} title="Pick a feature" description="Select a feature above to see how its value relates to its SHAP contribution." />}
        {dependence && (
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart>
              <CartesianGrid />
              <XAxis dataKey="x" name={dependence.feature} type="number" label={{ value: dependence.feature, position: "insideBottom", dy: 10 }} />
              <YAxis dataKey="y" name="SHAP value" type="number" label={{ value: "SHAP value", angle: -90 }} />
              <Tooltip />
              <Scatter data={dependence.feature_values.map((v, i) => ({ x: v, y: dependence.shap_values[i] }))} fill="var(--ai-accent)" />
            </ScatterChart>
          </ResponsiveContainer>
        )}
      </Card>
    </div>
  );
}

function ContributionBars({ items, tone }) {
  if (items.length === 0) return <p className="text-secondary">None.</p>;
  const max = Math.max(...items.map((i) => Math.abs(i.shap_value)), 0.0001);
  return (
    <ul className="contribution-bars">
      {items.map((c) => (
        <li key={c.feature}>
          <div className="contribution-bar-label">
            <span>{c.feature}</span>
            <span className="shap-value">{c.shap_value > 0 ? "+" : ""}{c.shap_value.toFixed(3)}</span>
          </div>
          <div className="contribution-bar-track">
            <div
              className={`contribution-bar-fill contribution-bar-${tone}`}
              style={{ width: `${(Math.abs(c.shap_value) / max) * 100}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

import { Activity, CheckCircle2, Trophy, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  autoSelectBestDataset, getTrainingStatus, optimizeXgboost, runAblation, trainBaselines,
} from "../api/evaluationApi";
import { Alert, Button, Card, PageHeader, useToast } from "../components/ui";
import { extractErrorMessage } from "../components/common/ErrorMessage";
import Loading from "../components/common/Loading";
import WorkflowStatus from "../components/common/WorkflowStatus";

export default function ModelTraining() {
  const toast = useToast();
  const [status, setStatus] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [comparisonDataset, setComparisonDataset] = useState(null);
  const [xgboostResult, setXgboostResult] = useState(null);
  const [ablation, setAblation] = useState(null);
  const [ablationDataset, setAblationDataset] = useState(null);
  const [autoSelect, setAutoSelect] = useState(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  useEffect(() => { refreshStatus(); }, []);

  function refreshStatus() {
    getTrainingStatus().then(setStatus).catch(() => {});
  }

  async function handleTrainBaselines() {
    setBusy("baselines"); setError("");
    try {
      const res = await trainBaselines();
      setComparison(res.models);
      setComparisonDataset(res.dataset_used);
      toast("Model comparison complete.", "success");
    } catch (err) { setError(extractErrorMessage(err)); }
    finally { setBusy(""); }
  }

  async function handleOptimizeXgboost() {
    setBusy("xgboost"); setError("");
    try {
      setXgboostResult(await optimizeXgboost(30));
      refreshStatus();
      toast("XGBoost training and optimization complete.", "success");
    } catch (err) { setError(extractErrorMessage(err)); }
    finally { setBusy(""); }
  }

  async function handleAblation() {
    setBusy("ablation"); setError("");
    try {
      const res = await runAblation();
      setAblation(res.results);
      setAblationDataset(res.dataset_used);
      toast("Modality ablation complete.", "success");
    } catch (err) { setError(extractErrorMessage(err)); }
    finally { setBusy(""); }
  }

  async function handleAutoSelect() {
    setBusy("autoselect"); setError("");
    try {
      setAutoSelect(await autoSelectBestDataset(30));
      refreshStatus();
      toast("Best dataset selected and model retrained.", "success");
    } catch (err) { setError(extractErrorMessage(err)); }
    finally { setBusy(""); }
  }

  return (
    <div>
      <PageHeader
        icon={Activity}
        title="Model Training"
        description="Compare machine-learning models and optimize XGBoost for running-athlete injury-risk prediction."
      />
      <WorkflowStatus />
      {error && <Alert tone="error" title="That experiment couldn't complete.">{error}</Alert>}

      <ModelStatusCard status={status} />

      <Card title="Experiment 1: Model Comparison" description="Compare six machine-learning algorithms using the same dataset and evaluation procedure: Logistic Regression, Decision Tree, Random Forest, SVM, Gradient Boosting, and XGBoost.">
        <Button onClick={handleTrainBaselines} loading={busy === "baselines"}>Run Model Comparison</Button>
        {busy === "baselines" && <Loading text="Training baseline models... this can take a moment." />}
        {comparison && (
          <>
            {comparisonDataset && <DatasetCaption info={comparisonDataset} />}
            <MetricsTable rows={comparison} nameKey="model" />
          </>
        )}
      </Card>

      <Card title="Experiment 2: XGBoost Optimization" description="Train XGBoost and optimize its hyperparameters using RandomizedSearchCV with 5-fold cross-validation, then compare it against a default (un-tuned) XGBoost.">
        <p className="text-caption" style={{ marginTop: -6 }}>Randomized Search — Iterations: 30 · Cross-validation: 5-fold</p>
        <Button onClick={handleOptimizeXgboost} loading={busy === "xgboost"}>Train &amp; Optimize XGBoost</Button>
        {busy === "xgboost" && <Loading text="Optimizing XGBoost... please wait while the model searches the parameter space." />}
        {xgboostResult && (
          <div>
            <ul className="checklist">
              <li><CheckCircle2 size={15} /> Training Status: Completed</li>
              <li><CheckCircle2 size={15} /> Model: Optimized XGBoost ({xgboostResult.model_version})</li>
              <li><CheckCircle2 size={15} /> Preprocessing pipeline saved</li>
              <li><CheckCircle2 size={15} /> SHAP explainer saved</li>
              <li><CheckCircle2 size={15} /> Training Time: {xgboostResult.training_time_seconds}s</li>
            </ul>
            <DatasetCaption info={xgboostResult.dataset_used} />
            <h4>Default vs. Optimized</h4>
            <MetricsTable rows={[
              { model: "Default XGBoost", ...xgboostResult.default_xgboost },
              { model: "Optimized XGBoost", ...xgboostResult.optimized_xgboost },
            ]} nameKey="model" />
            <h4>Best Parameters (found via search)</h4>
            <pre className="code-block">{JSON.stringify(xgboostResult.best_params, null, 2)}</pre>
            <h4>5-Fold Cross-Validation (Optimized Model)</h4>
            <pre className="code-block">{JSON.stringify(xgboostResult.cross_validation_5fold, null, 2)}</pre>
          </div>
        )}
      </Card>

      <Card title="Experiment 3: Multimodal Ablation Study" description="Evaluate whether adding different athlete-data modalities improves model performance, from demographic-only (M1) up to all six modalities (M6).">
        <div className="ablation-legend">
          <span><b>M1</b> Demographic</span>
          <span><b>M2</b> + Training</span>
          <span><b>M3</b> + Recovery</span>
          <span><b>M4</b> + Physiological</span>
          <span><b>M5</b> + Lifestyle</span>
          <span><b>M6</b> All Modalities</span>
        </div>
        <Button onClick={handleAblation} loading={busy === "ablation"}>Run Modality Ablation</Button>
        {busy === "ablation" && <Loading text="Training across modality configurations..." />}
        {ablation && (
          <>
            {ablationDataset && <DatasetCaption info={ablationDataset} />}
            <MetricsTable rows={ablation} nameKey="modality_configuration" />
            <h4 style={{ marginTop: 18 }}>F1 / Recall / ROC-AUC by Modality Configuration</h4>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={ablation}>
                <CartesianGrid strokeDasharray="3 3" stroke="#eceef1" />
                <XAxis dataKey="modality_configuration" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 1]} />
                <Tooltip />
                <Legend />
                <Bar dataKey="f1_score" name="F1-score" fill="var(--accent)" />
                <Bar dataKey="recall" name="Recall" fill="#0c9d45" />
                <Bar dataKey="roc_auc" name="ROC-AUC" fill="#e11d48" />
              </BarChart>
            </ResponsiveContainer>
          </>
        )}
      </Card>

      <Card title="Auto-Select Best Dataset" description="Quickly compares every available dataset — the default plus any you've uploaded and processed — by accuracy, then fully trains and saves the model on whichever one scores best.">
        <Button icon={Trophy} onClick={handleAutoSelect} loading={busy === "autoselect"}>Auto-Select Best Dataset</Button>
        {busy === "autoselect" && <Loading text="Quickly evaluating each dataset, then fully training on the winner... this can take a minute." />}
        {autoSelect && (
          <div style={{ marginTop: 16 }}>
            <div className="disclaimer-box" style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Trophy size={16} color="var(--accent)" />
              Selected <b>{autoSelect.selected.source === "synthetic" ? "Trained Data" : autoSelect.selected.filename}</b>
              {" "}(accuracy {autoSelect.selected.accuracy}) — trained and saved.
            </div>
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr><th>Dataset</th><th>Rows</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>ROC-AUC</th></tr>
                </thead>
                <tbody>
                  {autoSelect.candidates.map((c, i) => {
                    const label = c.source === "synthetic" ? "Trained Data" : c.filename;
                    const isWinner = c.dataset_id === autoSelect.selected.dataset_id && c.source === autoSelect.selected.source;
                    return (
                      <tr key={i} style={isWinner ? { background: "var(--accent-soft)" } : undefined}>
                        <td>{isWinner && <Trophy size={13} style={{ verticalAlign: "-2px", marginRight: 4 }} />}{label}</td>
                        <td>{c.n_rows ?? "—"}</td>
                        <td>{c.accuracy ?? "error"}</td>
                        <td>{c.precision ?? "—"}</td>
                        <td>{c.recall ?? "—"}</td>
                        <td>{c.f1_score ?? "—"}</td>
                        <td>{c.roc_auc ?? "—"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

function ModelStatusCard({ status }) {
  if (!status) return <Loading text="Checking model status..." />;
  const trained = status.model_artifacts_present;
  const datasetLabel = status.trained_dataset?.label || status.selected_dataset?.label || "Trained Data";

  return (
    <Card title="Model Status">
      {trained ? (
        <div className="status-card-grid">
          <div><b>Population</b>Running Athletes</div>
          <div><b>Model</b>XGBoost</div>
          <div><b>Version</b>{status.model_version}</div>
          <div><b>Status</b><span className="badge badge-low">Trained</span></div>
          <div><b>Dataset</b>{datasetLabel}</div>
          <div><b>Last Trained</b>{status.trained_at ? new Date(status.trained_at).toLocaleString() : "Not available"}</div>
        </div>
      ) : (
        <Alert tone="warning">
          <XCircle size={16} style={{ verticalAlign: "-3px", marginRight: 4 }} />
          Not Trained — run <b>Train &amp; Optimize XGBoost</b> below.
        </Alert>
      )}
    </Card>
  );
}

function DatasetCaption({ info }) {
  if (!info) return null;
  const label = info.source === "synthetic" ? "Trained Data" : info.label;
  return (
    <p className="dataset-caption">
      <b className="dataset-summary-label">Dataset Used</b>
      <span className="dataset-summary-value">{label}</span>
    </p>
  );
}

function MetricsTable({ rows, nameKey }) {
  if (!rows || rows.length === 0) return null;
  const metricKeys = Object.keys(rows[0]).filter((k) => k !== nameKey && k !== "modalities");
  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead><tr><th>{nameKey === "model" ? "Model" : "Configuration"}</th>{metricKeys.map((k) => <th key={k}>{k}</th>)}</tr></thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row[nameKey]}>
              <td>{row[nameKey]}</td>
              {metricKeys.map((k) => <td key={k}>{typeof row[k] === "number" ? row[k].toFixed(4) : row[k]}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

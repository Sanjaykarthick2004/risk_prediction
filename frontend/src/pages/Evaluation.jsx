import { FileBarChart } from "lucide-react";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  getConfusionMatrix, getMetrics, getModalityAblation, getModelComparison, getPrecisionRecall,
  getRocCurve, getTrainingStatus,
} from "../api/evaluationApi";
import { Alert, Card, PageHeader, Tooltip as UiTooltip } from "../components/ui";
import Loading from "../components/common/Loading";
import { extractErrorMessage } from "../components/common/ErrorMessage";
import WorkflowStatus from "../components/common/WorkflowStatus";

const METRIC_LABELS = {
  accuracy: "Accuracy", precision: "Precision", recall: "Recall", f1_score: "F1-score",
  roc_auc: "ROC-AUC", pr_auc: "PR-AUC", specificity: "Specificity",
};

const METRIC_EXPLANATIONS = {
  accuracy: "Percentage of predictions that were correct overall.",
  precision: "Among predicted positive cases, how many were actually positive.",
  recall: "Among actual positive cases, how many were correctly identified.",
  f1_score: "A combined measure of precision and recall.",
  roc_auc: "Measures how well the model separates the two classes across thresholds.",
  pr_auc: "Summarizes the precision-recall relationship; useful when positive cases are less common.",
  specificity: "Among actual negative cases, how many were correctly identified.",
};

/** 409 = "nothing trained/run yet" — that's an expected first-run state, not an error. */
function isNotAvailable(err) {
  return err?.response?.status === 409;
}

export default function Evaluation() {
  const [status, setStatus] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [comparisonUnavailable, setComparisonUnavailable] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [metricsUnavailable, setMetricsUnavailable] = useState(false);
  const [cm, setCm] = useState(null);
  const [roc, setRoc] = useState(null);
  const [pr, setPr] = useState(null);
  const [curvesUnavailable, setCurvesUnavailable] = useState(false);
  const [ablation, setAblation] = useState(null);
  const [ablationUnavailable, setAblationUnavailable] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getTrainingStatus().then(setStatus).catch(() => {});

    getModelComparison().then((r) => setComparison(r.models))
      .catch((err) => (isNotAvailable(err) ? setComparisonUnavailable(true) : setError(extractErrorMessage(err))));

    getMetrics().then(setMetrics)
      .catch((err) => (isNotAvailable(err) ? setMetricsUnavailable(true) : setError(extractErrorMessage(err))));

    Promise.all([getConfusionMatrix(), getRocCurve(), getPrecisionRecall()])
      .then(([cmR, rocR, prR]) => { setCm(cmR); setRoc(rocR); setPr(prR); })
      .catch((err) => (isNotAvailable(err) ? setCurvesUnavailable(true) : setError(extractErrorMessage(err))));

    getModalityAblation().then((r) => setAblation(r.results))
      .catch((err) => (isNotAvailable(err) ? setAblationUnavailable(true) : setError(extractErrorMessage(err))));
  }, []);

  const optimized = metrics?.optimized_xgboost;
  const datasetLabel = status?.trained_dataset?.label
    ?? (status?.selected_dataset?.source === "synthetic" ? "Trained Data" : status?.selected_dataset?.label);

  return (
    <div>
      <PageHeader
        icon={FileBarChart}
        title="Model Evaluation"
        description="Research-quality evaluation of the current XGBoost model, computed from the persisted model and a reproducible held-out test split."
      />
      <WorkflowStatus />
      {error && <Alert tone="error" title="We couldn't load the evaluation results.">{error}</Alert>}

      {status && (
        <Card title="Evaluation Context">
          <div className="status-card-grid">
            <div><b>Population</b>Running Athletes</div>
            <div><b>Model</b>XGBoost</div>
            <div><b>Version</b>{status.model_version}</div>
            <div><b>Dataset</b>{datasetLabel || "Not available"}</div>
            <div><b>Training Status</b>
              {status.workflow.model_trained ? <span className="badge badge-low">Completed</span> : <span className="badge badge-medium">Not Trained</span>}
            </div>
            <div><b>Evaluation</b>
              {status.workflow.evaluation_available ? <span className="badge badge-low">Available</span> : <span className="badge badge-medium">Not Available</span>}
            </div>
          </div>
        </Card>
      )}

      <Card title="Model Comparison">
        {comparisonUnavailable && <Alert tone="info">Not available — run Experiment 1 (Model Comparison) on the Model Training page.</Alert>}
        {comparison && (
          <div className="table-scroll">
            <table className="data-table">
              <thead><tr><th>Model</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>ROC-AUC</th><th>PR-AUC</th></tr></thead>
              <tbody>
                {comparison.map((m) => (
                  <tr key={m.model}>
                    <td>{m.model}</td><td>{m.accuracy}</td><td>{m.precision}</td>
                    <td>{m.recall}</td><td>{m.f1_score}</td><td>{m.roc_auc}</td><td>{m.pr_auc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {!comparison && !comparisonUnavailable && <Loading />}
      </Card>

      <Card title="XGBoost Metrics">
        {metricsUnavailable && <Alert tone="info">Not available — run Experiment 2 (Train &amp; Optimize XGBoost) on the Model Training page.</Alert>}
        {optimized && (
          <>
            <table className="data-table">
              <thead><tr><th>Metric</th><th>Score</th></tr></thead>
              <tbody>
                {Object.entries(METRIC_LABELS).map(([key, label]) => (
                  <tr key={key}>
                    <td>
                      <UiTooltip text={METRIC_EXPLANATIONS[key]}><span style={{ textDecoration: "underline dotted", cursor: "help" }}>{label}</span></UiTooltip>
                    </td>
                    <td>{optimized[key] ?? "Not available"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
        {!optimized && !metricsUnavailable && <Loading />}
      </Card>

      <Card title="Confusion Matrix" description="How the model's predictions compare to the actual outcomes on the held-out test set.">
        {curvesUnavailable && <Alert tone="info">Not available — run Experiment 2 (Train &amp; Optimize XGBoost) on the Model Training page.</Alert>}
        {cm && (
          <table className="data-table confusion-matrix">
            <thead><tr><th></th><th>Predicted No Injury</th><th>Predicted Injury</th></tr></thead>
            <tbody>
              <tr>
                <th>Actual No Injury</th>
                <td>{cm.matrix[0][0]}<div className="text-caption">True Negative</div></td>
                <td>{cm.matrix[0][1]}<div className="text-caption">False Positive</div></td>
              </tr>
              <tr>
                <th>Actual Injury</th>
                <td>{cm.matrix[1][0]}<div className="text-caption">False Negative</div></td>
                <td>{cm.matrix[1][1]}<div className="text-caption">True Positive</div></td>
              </tr>
            </tbody>
          </table>
        )}
      </Card>

      {roc && (
        <Card title="ROC Curve">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={roc.fpr.map((v, i) => ({ fpr: v, tpr: roc.tpr[i] }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="fpr" type="number" label={{ value: "False Positive Rate", position: "insideBottom", dy: 10 }} />
              <YAxis dataKey="tpr" domain={[0, 1]} label={{ value: "True Positive Rate", angle: -90 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="tpr" name="Model" stroke="var(--accent)" dot={false} />
            </LineChart>
          </ResponsiveContainer>
          <p className="text-caption">AUC: {metrics?.optimized_xgboost?.roc_auc ?? "—"}</p>
        </Card>
      )}

      {pr && (
        <Card title="Precision-Recall Curve">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={pr.recall.map((v, i) => ({ recall: v, precision: pr.precision[i] }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="recall" type="number" domain={[0, 1]} label={{ value: "Recall", position: "insideBottom", dy: 10 }} />
              <YAxis dataKey="precision" domain={[0, 1]} label={{ value: "Precision", angle: -90 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="precision" name="Model" stroke="#16a34a" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      )}

      <Card title="Modality Ablation Analysis" description="How model performance changes when individual data modalities are excluded.">
        {ablationUnavailable && <Alert tone="info">Not available — run Experiment 3 (Modality Ablation) on the Model Training page.</Alert>}
        {ablation && (
          <>
            <div className="table-scroll">
              <table className="data-table">
                <thead><tr><th>Configuration</th><th>Modalities</th><th>F1</th><th>Recall</th><th>ROC-AUC</th><th>PR-AUC</th></tr></thead>
                <tbody>
                  {ablation.map((r) => (
                    <tr key={r.modality_configuration}>
                      <td>{r.modality_configuration}</td><td>{r.modalities}</td>
                      <td>{r.f1_score}</td><td>{r.recall}</td><td>{r.roc_auc}</td><td>{r.pr_auc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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
    </div>
  );
}

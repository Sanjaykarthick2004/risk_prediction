import { ClipboardList, Download, Printer } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getAthleteReport, getPredictionReport } from "../api/reportApi";
import { Alert, Button, Card, FormField, PageHeader, RiskBadge, Tabs } from "../components/ui";
import { extractErrorMessage } from "../components/common/ErrorMessage";

const REPORT_TYPES = [
  { key: "prediction", label: "Prediction Report", icon: ClipboardList },
  { key: "athlete", label: "Athlete Profile Report", icon: ClipboardList },
];

export default function Reports() {
  const [params] = useSearchParams();
  const [reportType, setReportType] = useState(params.get("athlete_id") ? "athlete" : "prediction");
  const [predictionId, setPredictionId] = useState(params.get("prediction_id") || "");
  const [athleteId, setAthleteId] = useState(params.get("athlete_id") || "");
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");
  const [savingPdf, setSavingPdf] = useState(false);
  const reportRef = useRef(null);

  useEffect(() => {
    setReport(null);
    setError("");
    if (reportType === "prediction" && predictionId) {
      getPredictionReport(predictionId).then(setReport).catch((err) => setError(extractErrorMessage(err)));
    }
    if (reportType === "athlete" && athleteId) {
      getAthleteReport(athleteId).then(setReport).catch((err) => setError(extractErrorMessage(err)));
    }
  }, [reportType, predictionId, athleteId]);

  function handlePrint() {
    window.print();
  }

  async function handleSaveAsPdf() {
    setSavingPdf(true);
    try {
      const html2pdf = (await import("html2pdf.js")).default;
      const filename = reportType === "prediction" ? `${report.prediction.prediction_id}_report.pdf` : `${report.athlete.athlete_id}_athlete_report.pdf`;
      await html2pdf()
        .from(reportRef.current)
        .set({
          margin: 12,
          filename,
          html2canvas: { scale: 2 },
          jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
        })
        .save();
    } finally {
      setSavingPdf(false);
    }
  }

  return (
    <div>
      <PageHeader icon={ClipboardList} title="Reports" description="Generate a printable report from actual stored prediction and athlete data." />

      <Card className="no-print">
        <Tabs tabs={REPORT_TYPES} active={reportType} onChange={setReportType} />
        {reportType === "prediction" ? (
          <FormField label="Prediction ID">
            <input value={predictionId} onChange={(e) => setPredictionId(e.target.value)} placeholder="PRED-xxxxxxxxxxxx" />
          </FormField>
        ) : (
          <FormField label="Athlete ID">
            <input value={athleteId} onChange={(e) => setAthleteId(e.target.value)} placeholder="ATH-0001" />
          </FormField>
        )}
        {report && (
          <div className="row-actions" style={{ marginTop: 10 }}>
            <Button variant="ghost" icon={Printer} onClick={handlePrint}>Print</Button>
            <Button icon={Download} onClick={handleSaveAsPdf} loading={savingPdf}>Save as PDF</Button>
          </div>
        )}
      </Card>

      {error && <Alert tone="error" title="We couldn't generate this report.">{error}</Alert>}

      {report && reportType === "prediction" && (
        <div className="card report-card" ref={reportRef}>
          <div className="report-header">
            <h2>{report.project_title}</h2>
            <RiskBadge level={report.prediction.risk_level} size="lg" />
          </div>
          <hr />

          <section className="report-section">
            <h3>Athlete Information</h3>
            <div className="detail-grid">
              <div><b>Name</b><br />{report.athlete.name}</div>
              <div><b>Athlete ID</b><br />{report.athlete.athlete_id}</div>
              <div><b>Age</b><br />{report.athlete.age}</div>
              <div><b>Gender</b><br />{report.athlete.gender}</div>
              <div><b>Sport</b><br />{report.athlete.sport}</div>
              <div><b>Event Type</b><br />{report.athlete.event_type}</div>
            </div>
          </section>

          <section className="report-section">
            <h3>Prediction</h3>
            <div className="detail-grid">
              <div><b>Prediction ID</b><br />{report.prediction.prediction_id}</div>
              <div><b>Date</b><br />{new Date(report.prediction.prediction_date).toLocaleString()}</div>
              <div><b>Probability</b><br />{(report.prediction.probability * 100).toFixed(1)}%</div>
              <div><b>Risk Level</b><br />{report.prediction.risk_level}</div>
              <div><b>Model Version</b><br />{report.prediction.model_version}</div>
            </div>
          </section>

          <section className="report-section">
            <h3>Top Risk Factors</h3>
            <ul className="factor-list risk">
              {report.top_risk_factors.map((f) => (
                <li key={f.feature}>{f.feature} <span className="shap-value">(+{f.shap_value.toFixed(3)})</span></li>
              ))}
            </ul>
          </section>

          <section className="report-section">
            <h3>Protective Factors</h3>
            <ul className="factor-list protective">
              {report.protective_factors.map((f) => (
                <li key={f.feature}>{f.feature} <span className="shap-value">({f.shap_value.toFixed(3)})</span></li>
              ))}
            </ul>
          </section>

          <hr />
        </div>
      )}

      {report && reportType === "athlete" && (
        <div className="card report-card" ref={reportRef}>
          <div className="report-header">
            <h2>{report.project_title}</h2>
            <span className="text-caption">{report.predictions.length} prediction(s) on record</span>
          </div>
          <hr />

          <section className="report-section">
            <h3>Athlete Information</h3>
            <div className="detail-grid">
              <div><b>Name</b><br />{report.athlete.name}</div>
              <div><b>Athlete ID</b><br />{report.athlete.athlete_id}</div>
              <div><b>Age</b><br />{report.athlete.age}</div>
              <div><b>Gender</b><br />{report.athlete.gender}</div>
              <div><b>Sport</b><br />{report.athlete.sport}</div>
              <div><b>Event Type</b><br />{report.athlete.event_type}</div>
              <div><b>Height</b><br />{report.athlete.height} cm</div>
              <div><b>Weight</b><br />{report.athlete.weight} kg</div>
              <div><b>Experience</b><br />{report.athlete.experience_years} yrs</div>
            </div>
          </section>

          <section className="report-section">
            <h3>Prediction History</h3>
            {report.predictions.length === 0 ? (
              <p className="text-secondary">No predictions recorded for this athlete yet.</p>
            ) : (
              <div className="table-scroll">
                <table className="data-table">
                  <thead><tr><th>Date</th><th>Probability</th><th>Risk Level</th><th>Model</th></tr></thead>
                  <tbody>
                    {report.predictions.map((p) => (
                      <tr key={p.prediction_id}>
                        <td>{new Date(p.prediction_date).toLocaleString()}</td>
                        <td>{(p.probability * 100).toFixed(1)}%</td>
                        <td><RiskBadge level={p.risk_level} /></td>
                        <td>{p.model_version}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <hr />
        </div>
      )}
    </div>
  );
}

import {
  AlertTriangle, CheckCircle2, Cog, Columns3, Database, FileSpreadsheet, Hash,
  RotateCcw, Rows3, ShieldCheck, Sparkles, UploadCloud,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import {
  getTrainingSelection, processDataset, resetTrainingSelection,
  selectDatasetForTraining, uploadDataset, validateDataset,
} from "../api/datasetApi";
import { Alert, Button, Card, PageHeader, Stat, useToast } from "../components/ui";
import { extractErrorMessage } from "../components/common/ErrorMessage";
import WorkflowStatus from "../components/common/WorkflowStatus";

const CHECK_LABELS = {
  required_columns: "Required Columns",
  data_types: "Data Types",
  value_ranges: "Value Ranges",
  categories: "Categories",
};

export default function Dataset() {
  const toast = useToast();
  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [uploaded, setUploaded] = useState(null);
  const [validation, setValidation] = useState(null);
  const [processed, setProcessed] = useState(null);
  const [selection, setSelection] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  useEffect(() => { refreshSelection(); }, []);

  function refreshSelection() {
    getTrainingSelection().then(setSelection).catch(() => {});
  }

  async function handleUpload() {
    if (!file) return;
    setBusy("upload"); setError(""); setValidation(null); setProcessed(null);
    try {
      const res = await uploadDataset(file);
      setUploaded(res);
      toast(`Uploaded ${res.filename} (${res.rows} rows).`, "success");
    } catch (err) { setError(extractErrorMessage(err)); }
    finally { setBusy(""); }
  }

  async function handleValidate() {
    setBusy("validate"); setError("");
    try {
      const res = await validateDataset(uploaded.dataset_id);
      setValidation(res);
      toast(res.is_valid ? "Dataset validated successfully." : "Dataset contains validation warnings.", res.is_valid ? "success" : "warning");
    } catch (err) { setError(extractErrorMessage(err)); }
    finally { setBusy(""); }
  }

  async function handleProcess() {
    setBusy("process"); setError("");
    try {
      setProcessed(await processDataset(uploaded.dataset_id));
      toast("Dataset processed successfully.", "success");
    } catch (err) { setError(extractErrorMessage(err)); }
    finally { setBusy(""); }
  }

  async function handleSelectForTraining() {
    setBusy("select"); setError("");
    try {
      await selectDatasetForTraining(uploaded.dataset_id);
      refreshSelection();
      toast("Dataset selected for training.", "success");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusy("");
    }
  }

  async function handleResetToSynthetic() {
    setBusy("reset"); setError("");
    try {
      await resetTrainingSelection();
      refreshSelection();
      toast("Reverted to Trained Data.", "success");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusy("");
    }
  }

  const isActiveSelection = selection?.dataset_id === uploaded?.dataset_id;

  return (
    <div>
      <PageHeader
        icon={Database}
        title="Dataset"
        description="Validate and prepare running-athlete data for machine-learning training."
      />

      <WorkflowStatus />

      <Card>
        <div className="check-row" style={{ borderBottom: "none" }}>
          <span className="dataset-summary">
            <b className="dataset-summary-label">Current Training Dataset</b>
            <span className="dataset-summary-value">
              {selection?.source === "synthetic" ? "Trained Data" : selection?.label || "—"}
            </span>
          </span>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span className={`badge ${selection?.source === "uploaded" ? "badge-low" : "badge-medium"}`}>
              {selection?.source === "uploaded" ? "Uploaded" : "Trained Data (default)"}
            </span>
            {selection?.source === "uploaded" && (
              <Button variant="ghost" size="sm" icon={RotateCcw} onClick={handleResetToSynthetic} loading={busy === "reset"}>
                Reset to Trained Data
              </Button>
            )}
          </div>
        </div>
      </Card>

      {error && <Alert tone="error" title="We couldn't complete that step.">{error}</Alert>}

      {/* Step 1 — Upload */}
      <Card>
        <StepHeader step={1} icon={UploadCloud} title="Upload" done={!!uploaded} />

        <div className="dropzone" onClick={() => fileInputRef.current?.click()}>
          <FileSpreadsheet size={26} strokeWidth={1.8} />
          <div>
            <div className="dropzone-title">{file ? file.name : "Click to choose a CSV or Excel file"}</div>
            <div className="dropzone-hint">.csv, .xlsx, .xls</div>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={(e) => setFile(e.target.files[0])}
            hidden
          />
        </div>

        <Button icon={UploadCloud} onClick={handleUpload} disabled={!file} loading={busy === "upload"}>
          Upload Dataset
        </Button>

        {uploaded && (
          <>
            <div className="card-grid" style={{ marginTop: 16, marginBottom: 0 }}>
              <Stat icon={Database} label="Dataset ID" value={uploaded.dataset_id} />
              <Stat icon={Rows3} label="Rows" value={uploaded.rows} />
              <Stat icon={Columns3} label="Columns" value={uploaded.columns} />
            </div>

            <div style={{ marginTop: 18 }}>
              <h4 style={{ marginBottom: 8 }}>Dataset Preview</h4>
              <p className="text-secondary" style={{ marginTop: 0 }}>
                File: {uploaded.filename} — showing the first {uploaded.preview_rows.length} of {uploaded.rows} rows.
              </p>
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>{uploaded.column_names.map((c) => <th key={c}>{c}</th>)}</tr>
                  </thead>
                  <tbody>
                    {uploaded.preview_rows.map((row, i) => (
                      <tr key={i}>
                        {uploaded.column_names.map((c) => <td key={c}>{String(row[c] ?? "")}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </Card>

      {/* Step 2 — Validate */}
      <Card style={{ opacity: uploaded ? 1 : 0.5 }}>
        <StepHeader step={2} icon={ShieldCheck} title="Validate" done={!!validation} />
        <Button icon={ShieldCheck} onClick={handleValidate} disabled={!uploaded} loading={busy === "validate"}>
          Validate Dataset
        </Button>

        {validation && (
          <div style={{ marginTop: 16 }}>
            <h4 style={{ marginBottom: 4 }}>Validation Summary</h4>
            {Object.entries(validation.summary).map(([key, status]) => (
              <div className="check-row" key={key}>
                <span>{CHECK_LABELS[key]}</span>
                <span className={`check-status ${status}`}>{status}</span>
              </div>
            ))}
            <div className="check-row">
              <span>Errors</span>
              <span className={`check-status ${validation.errors.length ? "FAIL" : "PASS"}`}>{validation.errors.length}</span>
            </div>
            <div className="check-row">
              <span>Warnings</span>
              <span className={`check-status ${validation.warnings.length ? "WARN" : "PASS"}`}>{validation.warnings.length}</span>
            </div>

            <div className={`validity-pill ${validation.is_valid ? "valid" : "invalid"}`} style={{ marginTop: 12 }}>
              {validation.is_valid ? <CheckCircle2 size={15} /> : <AlertTriangle size={15} />}
              {validation.is_valid ? "Overall: Valid" : "Overall: Invalid"}
            </div>

            <div className="card-grid" style={{ marginTop: 14, marginBottom: 0 }}>
              <Stat icon={Rows3} label="Rows" value={validation.stats.n_rows} />
              <Stat icon={Columns3} label="Columns" value={validation.stats.n_columns} />
              <Stat icon={Hash} label="Missing Values" value={validation.stats.n_missing_values} />
              <Stat icon={Hash} label="Duplicate Rows" value={validation.stats.n_duplicate_rows} />
            </div>

            {validation.errors.length > 0 && (
              <Alert tone="error" title="Errors">{validation.errors.join("; ")}</Alert>
            )}
            {validation.warnings.length > 0 && (
              <Alert tone="warning" title="Warnings">{validation.warnings.join("; ")}</Alert>
            )}
          </div>
        )}
      </Card>

      {/* Step 3 — Process */}
      <Card style={{ opacity: uploaded ? 1 : 0.5 }}>
        <StepHeader step={3} icon={Cog} title="Process" done={!!processed} />
        <p className="text-secondary">Cleans duplicates/out-of-range values and adds the engineered features (BMI, workload ratio, etc.).</p>
        <Button icon={Cog} onClick={handleProcess} disabled={!uploaded} loading={busy === "process"}>
          Process Dataset
        </Button>

        {processed && (
          <div style={{ marginTop: 16 }}>
            <h4 style={{ marginBottom: 4 }}>Processing Complete</h4>
            <div className="card-grid" style={{ marginBottom: 0 }}>
              <Stat icon={Rows3} label="Original Rows" value={processed.rows_before} />
              <Stat icon={Rows3} label="Final Rows" value={processed.rows_after} />
              <Stat icon={Hash} label="Duplicates Removed" value={processed.duplicates_removed} />
            </div>

            <h4 style={{ marginTop: 18, marginBottom: 6 }}>Engineered Features</h4>
            <ul className="checklist">
              {processed.engineered_features.map((f) => (
                <li key={f}><CheckCircle2 size={15} /> {f}</li>
              ))}
            </ul>

            {!processed.has_target_column && (
              <Alert tone="warning">
                This dataset has no <code>injury_next_7_days</code> column, so it can't be used
                for Model Training — it can still be inspected here, that's all.
              </Alert>
            )}

            {processed.has_target_column && (
              <div style={{ marginTop: 16 }}>
                {isActiveSelection ? (
                  <div className="disclaimer-box" style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <CheckCircle2 size={16} color="var(--green-dark)" /> Dataset selected for training
                  </div>
                ) : (
                  <Button icon={Sparkles} onClick={handleSelectForTraining} loading={busy === "select"}>
                    Use This Dataset for Training
                  </Button>
                )}
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}

function StepHeader({ step, icon: Icon, title, done }) {
  return (
    <div className="step-header">
      <div className={`step-badge ${done ? "done" : ""}`}>{done ? <CheckCircle2 size={16} /> : step}</div>
      <Icon size={17} strokeWidth={2} />
      <h3>{title}</h3>
    </div>
  );
}

import { CheckCircle2, Circle } from "lucide-react";
import { useEffect, useState } from "react";
import { getTrainingStatus } from "../../api/evaluationApi";

const STEPS = [
  { key: "dataset_ready", label: "Dataset" },
  { key: "model_trained", label: "Model Training" },
  { key: "evaluation_available", label: "Evaluation" },
  { key: "prediction_ready", label: "Prediction" },
  { key: "shap_available", label: "Explainability" },
];

export default function WorkflowStatus() {
  const [workflow, setWorkflow] = useState(null);

  useEffect(() => {
    getTrainingStatus().then((s) => setWorkflow(s.workflow)).catch(() => {});
  }, []);

  if (!workflow) return null;

  return (
    <div className="workflow-status">
      {STEPS.map((step, i) => {
        const ready = !!workflow[step.key];
        return (
          <div className="workflow-step" key={step.key}>
            <div className={`workflow-icon ${ready ? "ready" : "pending"}`}>
              {ready ? <CheckCircle2 size={15} /> : <Circle size={15} />}
            </div>
            <span className={ready ? "" : "muted"}>{i + 1}. {step.label}</span>
            {i < STEPS.length - 1 && <span className="workflow-arrow">→</span>}
          </div>
        );
      })}
    </div>
  );
}

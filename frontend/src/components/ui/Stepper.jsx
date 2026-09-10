import { Check } from "lucide-react";

/**
 * Horizontal step indicator for multi-step workflows (the assessment wizard).
 * `steps`: [{ key, label }]. `completed`: Set/array of step keys already done.
 */
export default function Stepper({ steps, active, completed = [], onStepClick }) {
  const completedSet = new Set(completed);
  return (
    <ol className="stepper">
      {steps.map((step, i) => {
        const isDone = completedSet.has(step.key);
        const isActive = step.key === active;
        const clickable = !!onStepClick && (isDone || isActive);
        return (
          <li key={step.key} className={`stepper-item ${isActive ? "stepper-active" : ""} ${isDone ? "stepper-done" : ""}`}>
            <button
              type="button"
              className="stepper-dot"
              disabled={!clickable}
              onClick={() => clickable && onStepClick(step.key)}
              aria-current={isActive ? "step" : undefined}
            >
              {isDone ? <Check size={13} /> : i + 1}
            </button>
            <span className="stepper-label">{step.label}</span>
            {i < steps.length - 1 && <span className="stepper-connector" />}
          </li>
        );
      })}
    </ol>
  );
}

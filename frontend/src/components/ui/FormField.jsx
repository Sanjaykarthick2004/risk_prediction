/**
 * Label + control + unit + helper/error text, in one place, so every field in
 * the app looks and behaves the same (visible label, not a placeholder-as-label).
 */
export default function FormField({ label, unit, helper, error, required, wide, children }) {
  return (
    <label className={`form-field ${wide ? "form-field-wide" : ""} ${error ? "form-field-error" : ""}`}>
      <span className="form-field-label">
        {label}{required && <span className="form-field-required" aria-hidden="true"> *</span>}
      </span>
      <span className="form-field-control">
        {children}
        {unit && <span className="form-field-unit">{unit}</span>}
      </span>
      {error ? (
        <span className="form-field-message form-field-message-error" role="alert">{error}</span>
      ) : helper ? (
        <span className="form-field-message">{helper}</span>
      ) : null}
    </label>
  );
}

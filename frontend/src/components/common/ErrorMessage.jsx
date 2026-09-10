export default function ErrorMessage({ message }) {
  if (!message) return null;
  return <div className="error-box">{message}</div>;
}

export function extractErrorMessage(err) {
  const detail = err?.response?.data?.detail;
  if (Array.isArray(detail)) {
    // FastAPI/Pydantic 422 validation errors: a list of {loc, msg, type} objects.
    return detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
  }
  if (typeof detail === "string") return detail;
  return err?.message || "Something went wrong.";
}

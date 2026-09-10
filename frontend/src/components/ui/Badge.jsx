const TONE_CLASS = {
  neutral: "badge-neutral", success: "badge-low", warning: "badge-medium",
  danger: "badge-high", info: "badge-info", ai: "badge-ai",
};

export default function Badge({ tone = "neutral", size, children }) {
  return <span className={`badge ${TONE_CLASS[tone] || TONE_CLASS.neutral} ${size === "lg" ? "badge-lg" : ""}`}>{children}</span>;
}

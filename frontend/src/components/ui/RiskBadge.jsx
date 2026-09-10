import { AlertOctagon, AlertTriangle, CheckCircle2 } from "lucide-react";

const RISK_META = {
  LOW: { icon: CheckCircle2, className: "badge-low" },
  MEDIUM: { icon: AlertTriangle, className: "badge-medium" },
  HIGH: { icon: AlertOctagon, className: "badge-high" },
};

/** Risk is ALWAYS shown as icon + text + color together — never color alone. */
export default function RiskBadge({ level, probability, size }) {
  const meta = RISK_META[level] || RISK_META.LOW;
  const Icon = meta.icon;
  return (
    <span className={`badge risk-badge ${meta.className} ${size === "lg" ? "badge-lg" : ""}`}>
      <Icon size={size === "lg" ? 16 : 13} />
      {level} RISK
      {probability != null && <span className="risk-badge-prob">{(probability * 100).toFixed(1)}%</span>}
    </span>
  );
}

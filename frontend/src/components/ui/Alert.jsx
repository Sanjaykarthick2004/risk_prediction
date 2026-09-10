import { AlertTriangle, CheckCircle2, Info, XCircle } from "lucide-react";
import { useState } from "react";

const TONE_META = {
  info: { icon: Info, className: "alert-info" },
  success: { icon: CheckCircle2, className: "alert-success" },
  warning: { icon: AlertTriangle, className: "alert-warning" },
  error: { icon: XCircle, className: "alert-error" },
};

/** Inline banner for page-level messages. `details` (e.g. raw backend error text)
 * is hidden behind a disclosure toggle rather than shown to the user directly. */
export default function Alert({ tone = "info", title, children, details }) {
  const [showDetails, setShowDetails] = useState(false);
  const meta = TONE_META[tone] || TONE_META.info;
  const Icon = meta.icon;
  return (
    <div className={`alert ${meta.className}`} role={tone === "error" ? "alert" : undefined}>
      <Icon size={18} className="alert-icon" />
      <div className="alert-body">
        {title && <div className="alert-title">{title}</div>}
        {children && <div className="alert-message">{children}</div>}
        {details && (
          <>
            <button type="button" className="alert-details-toggle" onClick={() => setShowDetails((s) => !s)}>
              {showDetails ? "Hide technical details" : "Show technical details"}
            </button>
            {showDetails && <pre className="alert-details">{details}</pre>}
          </>
        )}
      </div>
    </div>
  );
}

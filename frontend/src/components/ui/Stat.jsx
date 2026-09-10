const TONE_STYLE_CLASS = { low: "stat-icon-low", medium: "stat-icon-medium", high: "stat-icon-high" };

/** The one metric-tile implementation — replaces the duplicated StatCard/MiniStat
 * defined separately in Dashboard.jsx and Dataset.jsx. */
export default function Stat({ icon: Icon, label, value, tone, hint }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${tone ? TONE_STYLE_CLASS[tone] : ""}`}>
        <Icon size={18} strokeWidth={2.2} />
      </div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      {hint && <div className="stat-hint">{hint}</div>}
    </div>
  );
}

import {
  Activity, ClipboardList, Database, FileBarChart, History, LayoutDashboard,
  Sparkles, Target, Users,
} from "lucide-react";
import { NavLink } from "react-router-dom";

/** Grouped nav — mirrors the routes that actually exist in App.jsx. No entries
 * for pages that don't exist (e.g. no separate "Assessments" or "Ablation
 * Analysis" routes — those live inside Prediction and Model Training/Evaluation). */
const GROUPS = [
  { label: "Overview", items: [{ to: "/dashboard", label: "Dashboard", icon: LayoutDashboard }] },
  { label: "Athlete Management", items: [{ to: "/athletes", label: "Athletes", icon: Users }] },
  {
    label: "Data & AI",
    items: [
      { to: "/dataset", label: "Dataset", icon: Database },
      { to: "/training", label: "Model Training", icon: Activity },
      { to: "/prediction", label: "Prediction", icon: Target },
      { to: "/history", label: "Prediction History", icon: History },
    ],
  },
  { label: "Explainability", items: [{ to: "/explainability", label: "SHAP Explainability", icon: Sparkles }] },
  { label: "Model Evaluation", items: [{ to: "/evaluation", label: "Evaluation", icon: FileBarChart }] },
  { label: "Reports", items: [{ to: "/reports", label: "Reports", icon: ClipboardList }] },
];

/** `collapsed`: icon-only rail with a tooltip carrying the label. `onNavigate`: called
 * after a link click (used to close the mobile drawer). */
export default function NavLinks({ collapsed = false, onNavigate }) {
  return (
    <nav className="sidebar-nav">
      {GROUPS.map((group) => (
        <div className="nav-group" key={group.label}>
          {!collapsed && <div className="nav-group-label">{group.label}</div>}
          {group.items.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={onNavigate}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
              title={collapsed ? label : undefined}
            >
              <Icon size={18} strokeWidth={2} />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </div>
      ))}
    </nav>
  );
}

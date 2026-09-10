import {
  ClipboardList, History, LayoutDashboard, Sparkles, Target, Users,
} from "lucide-react";
import { NavLink } from "react-router-dom";

/** Grouped nav. Dataset, Model Training, and Evaluation are deliberately not
 * listed here (the student only needs Prediction day-to-day, and the model
 * is already trained) — but their routes/pages/backend endpoints are all
 * still fully intact, reachable directly at /dataset, /training, /evaluation
 * whenever the research/training side of the project needs to be shown or
 * re-run. This list only controls what appears in the sidebar. */
const GROUPS = [
  { label: "Overview", items: [{ to: "/dashboard", label: "Dashboard", icon: LayoutDashboard }] },
  { label: "Athlete Management", items: [{ to: "/athletes", label: "Athletes", icon: Users }] },
  {
    label: "Prediction",
    items: [
      { to: "/prediction", label: "Prediction", icon: Target },
      { to: "/history", label: "Prediction History", icon: History },
    ],
  },
  { label: "Explainability", items: [{ to: "/explainability", label: "SHAP Explainability", icon: Sparkles }] },
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

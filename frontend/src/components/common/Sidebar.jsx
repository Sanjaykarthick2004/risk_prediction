import { LogOut } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import BrandMark from "./BrandMark";
import NavLinks from "./NavLinks";

export default function Sidebar() {
  const { user, logout } = useAuth();
  const initial = (user?.username || "?").charAt(0).toUpperCase();

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <BrandMark />
        <span className="brand-text">Injury AI</span>
      </div>

      <NavLinks />

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <span className="user-avatar">{initial}</span>
          <div>
            <div className="user-name">{user?.username}</div>
            <div className="user-role">{user?.role}</div>
          </div>
        </div>
        <button className="btn btn-ghost btn-block" onClick={logout} title="Logout">
          <LogOut size={16} strokeWidth={2} />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}

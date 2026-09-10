import { Menu } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import BrandMark from "./BrandMark";

/**
 * Mobile-only bar (hidden on desktop via CSS — the sidebar is always visible
 * there, so a persistent desktop topbar would just be empty chrome with no
 * real content: there's no search or notification backend to put in it).
 */
export default function Topbar({ onOpenMenu }) {
  const { user } = useAuth();
  const initial = (user?.username || "?").charAt(0).toUpperCase();

  return (
    <header className="topbar">
      <button type="button" className="icon-btn icon-btn-ghost" aria-label="Open menu" onClick={onOpenMenu}>
        <Menu size={20} />
      </button>
      <div className="topbar-brand">
        <BrandMark />
        <span className="brand-text">Injury AI</span>
      </div>
      <span className="user-avatar" title={user?.username}>{initial}</span>
    </header>
  );
}

import { X } from "lucide-react";
import { useEffect } from "react";
import { createPortal } from "react-dom";

/** Slide-in panel from the left, used for the mobile sidebar. */
export default function Drawer({ open, onClose, children }) {
  useEffect(() => {
    if (!open) return;
    function onKeyDown(e) { if (e.key === "Escape") onClose(); }
    document.addEventListener("keydown", onKeyDown);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div className="drawer-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="drawer-panel" role="dialog" aria-modal="true">
        <button type="button" className="icon-btn icon-btn-ghost drawer-close" aria-label="Close menu" onClick={onClose}>
          <X size={18} />
        </button>
        {children}
      </div>
    </div>,
    document.body,
  );
}

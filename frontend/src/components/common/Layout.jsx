import { useState } from "react";
import { Drawer } from "../ui";
import BrandMark from "./BrandMark";
import NavLinks from "./NavLinks";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

export default function Layout({ children }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="app-shell">
      <div className="sidebar-desktop">
        <Sidebar />
      </div>

      <Topbar onOpenMenu={() => setMobileOpen(true)} />

      <Drawer open={mobileOpen} onClose={() => setMobileOpen(false)}>
        <div className="sidebar-brand">
          <BrandMark />
          <span className="brand-text">Injury AI</span>
        </div>
        <NavLinks onNavigate={() => setMobileOpen(false)} />
      </Drawer>

      <main className="main-content">{children}</main>
    </div>
  );
}

import { ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";

/** `items`: [{ label, to? }] — the last item (no `to`) renders as the current page, not a link. */
export default function Breadcrumb({ items }) {
  return (
    <nav className="breadcrumb" aria-label="Breadcrumb">
      {items.map((item, i) => (
        <span key={item.label} className="breadcrumb-item">
          {item.to ? <Link to={item.to}>{item.label}</Link> : <span aria-current="page">{item.label}</span>}
          {i < items.length - 1 && <ChevronRight size={13} className="breadcrumb-sep" />}
        </span>
      ))}
    </nav>
  );
}

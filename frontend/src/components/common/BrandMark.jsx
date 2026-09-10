import { Activity } from "lucide-react";

export default function BrandMark({ className = "brand-mark" }) {
  return (
    <span className={className} aria-label="Injury AI logo">
      <Activity size={26} strokeWidth={2.4} />
    </span>
  );
}
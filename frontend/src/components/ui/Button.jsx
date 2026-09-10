import { Loader2 } from "lucide-react";
import { Link } from "react-router-dom";

/**
 * Single Button implementation for the whole app — variant/size props instead
 * of one-off page styles. `to` renders a Link styled as a button (for
 * navigation actions like "View SHAP Explanation").
 */
export default function Button({
  variant = "primary", size = "md", loading = false, disabled = false,
  icon: Icon, to, type = "button", className = "", children, ...rest
}) {
  const classes = [
    "btn",
    variant === "primary" && "btn-primary",
    variant === "ghost" && "btn-ghost",
    variant === "link" && "btn-link",
    variant === "danger" && "btn-danger",
    size === "lg" && "btn-lg",
    size === "sm" && "btn-sm",
    className,
  ].filter(Boolean).join(" ");

  const content = (
    <>
      {loading ? <Loader2 size={size === "sm" ? 13 : 16} className="btn-spinner" /> : Icon && <Icon size={size === "sm" ? 13 : 16} />}
      {children}
    </>
  );

  if (to) {
    return <Link to={to} className={classes} {...rest}>{content}</Link>;
  }
  return (
    <button type={type} className={classes} disabled={disabled || loading} aria-busy={loading} {...rest}>
      {content}
    </button>
  );
}

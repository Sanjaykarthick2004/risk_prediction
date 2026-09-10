/** Icon-only button. `label` is required and becomes the accessible name (never a bare icon with no name). */
export default function IconButton({ icon: Icon, label, variant = "ghost", size = 18, className = "", ...rest }) {
  return (
    <button
      type="button"
      className={`icon-btn icon-btn-${variant} ${className}`}
      aria-label={label}
      title={label}
      {...rest}
    >
      <Icon size={size} strokeWidth={2} />
    </button>
  );
}

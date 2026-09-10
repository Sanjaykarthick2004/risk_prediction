/** Lightweight CSS-only tooltip — wraps any element, shows `text` on hover/focus. */
export default function Tooltip({ text, children }) {
  return (
    <span className="tooltip-wrap" tabIndex={0}>
      {children}
      <span className="tooltip-bubble" role="tooltip">{text}</span>
    </span>
  );
}

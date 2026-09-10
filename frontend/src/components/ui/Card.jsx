/** Standard card shell. `title`/`description`/`actions` render a consistent card header
 * so pages stop hand-rolling <h3> + flex-row actions differently each time. */
export default function Card({ title, description, actions, className = "", children, ...rest }) {
  return (
    <div className={`card ${className}`} {...rest}>
      {(title || actions) && (
        <div className="card-head">
          <div>
            {title && <h3>{title}</h3>}
            {description && <p className="text-secondary card-head-desc">{description}</p>}
          </div>
          {actions && <div className="card-head-actions">{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

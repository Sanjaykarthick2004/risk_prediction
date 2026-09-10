import Breadcrumb from "./Breadcrumb";

/** Consistent page header: icon + title + one-line description + action slot + optional breadcrumb. */
export default function PageHeader({ icon: Icon, title, description, actions, breadcrumb }) {
  return (
    <div className="page-header-block">
      {breadcrumb && <Breadcrumb items={breadcrumb} />}
      <div className="page-header">
        <div>
          <h1>{Icon && <Icon size={22} className="page-title-icon" />}{title}</h1>
          {description && <p className="page-description">{description}</p>}
        </div>
        {actions && <div className="page-header-actions">{actions}</div>}
      </div>
    </div>
  );
}

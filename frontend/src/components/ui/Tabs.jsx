/** Accessible tabs. `tabs`: [{ key, label, icon }]. Controlled via `active`/`onChange`. */
export default function Tabs({ tabs, active, onChange }) {
  return (
    <div className="tabs" role="tablist">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const selected = tab.key === active;
        return (
          <button
            key={tab.key}
            role="tab"
            type="button"
            aria-selected={selected}
            className={`tab ${selected ? "tab-active" : ""}`}
            onClick={() => onChange(tab.key)}
          >
            {Icon && <Icon size={15} />}
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

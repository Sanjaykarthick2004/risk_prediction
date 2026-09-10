/** Layout-preserving loading placeholders — avoid a blank page while data loads. */
export function SkeletonLine({ width = "100%", height = 14 }) {
  return <span className="skeleton skeleton-line" style={{ width, height }} />;
}

export function SkeletonCard({ lines = 3 }) {
  return (
    <div className="card skeleton-card">
      <SkeletonLine width="40%" height={18} />
      {Array.from({ length: lines }).map((_, i) => (
        <SkeletonLine key={i} width={i === lines - 1 ? "60%" : "90%"} />
      ))}
    </div>
  );
}

export function SkeletonStatRow({ count = 4 }) {
  return (
    <div className="card-grid">
      {Array.from({ length: count }).map((_, i) => (
        <div className="card skeleton-card" key={i}>
          <SkeletonLine width={38} height={38} />
          <SkeletonLine width="50%" height={22} />
          <SkeletonLine width="70%" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonTable({ rows = 5, cols = 4 }) {
  return (
    <div className="skeleton-table">
      {Array.from({ length: rows }).map((_, r) => (
        <div className="skeleton-table-row" key={r}>
          {Array.from({ length: cols }).map((_, c) => <SkeletonLine key={c} />)}
        </div>
      ))}
    </div>
  );
}

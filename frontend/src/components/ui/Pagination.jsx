import { ChevronLeft, ChevronRight } from "lucide-react";

/** Client-side pagination. `total` items, `pageSize`, controlled `page` (1-indexed). */
export default function Pagination({ page, pageSize, total, onChange }) {
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  if (pageCount <= 1) return null;

  const start = (page - 1) * pageSize + 1;
  const end = Math.min(total, page * pageSize);

  return (
    <div className="pagination">
      <span className="pagination-summary">{start}–{end} of {total}</span>
      <div className="pagination-controls">
        <button type="button" className="icon-btn icon-btn-ghost" aria-label="Previous page" disabled={page <= 1} onClick={() => onChange(page - 1)}>
          <ChevronLeft size={16} />
        </button>
        <span className="pagination-page">Page {page} of {pageCount}</span>
        <button type="button" className="icon-btn icon-btn-ghost" aria-label="Next page" disabled={page >= pageCount} onClick={() => onChange(page + 1)}>
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}

/** Slices `items` for the current page — plain client-side pagination (no backend list endpoint supports offset/limit yet). */
export function paginate(items, page, pageSize) {
  const start = (page - 1) * pageSize;
  return items.slice(start, start + pageSize);
}

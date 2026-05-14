export function Pagination({ page, size, total, onPage }: {
  page: number; size: number; total: number; onPage: (p: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / size));
  return (
    <div className="flex items-center justify-between mt-3 text-sm">
      <span className="text-ink/60">Total: {total}</span>
      <div className="flex gap-1">
        <button className="btn-outline" disabled={page<=1} onClick={() => onPage(page-1)}>‹</button>
        <span className="px-3 py-2">{page} / {pages}</span>
        <button className="btn-outline" disabled={page>=pages} onClick={() => onPage(page+1)}>›</button>
      </div>
    </div>
  );
}

interface PaginationProps {
  page: number
  totalPages: number
  totalRows: number
  pageSize: number
  onPageChange: (page: number) => void
  itemLabel?: string
}

export function Pagination({ page, totalPages, totalRows, pageSize, onPageChange, itemLabel = 'batches' }: PaginationProps) {
  const start = totalRows === 0 ? 0 : (page - 1) * pageSize + 1
  const end = Math.min(page * pageSize, totalRows)

  return (
    <div className="flex flex-col items-center justify-between gap-3 border-t border-border px-4 py-3 sm:flex-row">
      <p className="tabular-figures text-[13px] text-text-muted">
        Showing <span className="font-semibold text-text">{start.toLocaleString()}–{end.toLocaleString()}</span> of{' '}
        <span className="font-semibold text-text">{totalRows.toLocaleString()}</span> {itemLabel}
      </p>
      <div className="flex items-center gap-1.5">
        <button
          type="button"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          className="rounded-lg border border-border-strong px-3 py-1.5 text-[12.5px] font-medium text-text transition-colors hover:bg-surface-sunken disabled:cursor-not-allowed disabled:opacity-40"
        >
          Previous
        </button>
        <span className="tabular-figures px-2 text-[12.5px] text-text-muted">
          Page {page} of {Math.max(totalPages, 1)}
        </span>
        <button
          type="button"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
          className="rounded-lg border border-border-strong px-3 py-1.5 text-[12.5px] font-medium text-text transition-colors hover:bg-surface-sunken disabled:cursor-not-allowed disabled:opacity-40"
        >
          Next
        </button>
      </div>
    </div>
  )
}

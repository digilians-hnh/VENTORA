import type { ValidationResponse } from '@/types/api'

export function ValidationPanel({ result }: { result: ValidationResponse }) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <div className="flex flex-wrap items-center gap-4">
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[12.5px] font-semibold ${
            result.valid
              ? 'bg-[color:var(--color-success)]/10 text-[color:var(--color-success)]'
              : 'bg-[color:var(--color-danger)]/10 text-[color:var(--color-danger)]'
          }`}
        >
          <span
            className="h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: result.valid ? 'var(--color-success)' : 'var(--color-danger)' }}
          />
          {result.valid ? 'Valid' : 'Validation failed'}
        </span>
        <span className="tabular-figures text-[13px] text-text-muted">
          <span className="font-semibold text-text">{result.n_valid_rows}</span> valid rows
        </span>
        <span className="tabular-figures text-[13px] text-text-muted">
          <span className="font-semibold text-[color:var(--color-danger)]">{result.n_invalid_rows}</span> invalid rows
        </span>
      </div>

      {result.errors.length > 0 && (
        <div className="mt-4 max-h-56 overflow-y-auto rounded-xl border border-[color:var(--color-danger)]/25 bg-[color:var(--color-danger)]/[0.04] p-3">
          <ul className="space-y-1.5 text-[12.5px] text-text">
            {result.errors.slice(0, 50).map((err, i) => (
              <li key={i}>
                {err.row !== null && <span className="tabular-figures font-semibold">Row {err.row}</span>}{' '}
                <span className="font-medium">{err.field}:</span> {err.message}
              </li>
            ))}
          </ul>
          {result.errors.length > 50 && (
            <p className="mt-2 text-[12px] text-text-muted">…and {result.errors.length - 50} more.</p>
          )}
        </div>
      )}

      {result.preview.length > 0 && (
        <div className="mt-4">
          <p className="mb-2 text-[12px] font-semibold uppercase tracking-wide text-text-muted">
            Preview ({result.preview.length} row{result.preview.length === 1 ? '' : 's'})
          </p>
          <div className="overflow-x-auto rounded-xl border border-border">
            <table className="w-full min-w-[600px] border-collapse text-left text-[12.5px]">
              <thead>
                <tr className="border-b border-border bg-surface-sunken/60">
                  {Object.keys(result.preview[0]).map((key) => (
                    <th key={key} className="whitespace-nowrap px-3 py-2 font-semibold text-text-muted">
                      {key}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.preview.map((row, i) => (
                  <tr key={i} className="border-b border-border last:border-b-0">
                    {Object.keys(result.preview[0]).map((key) => (
                      <td key={key} className="tabular-figures whitespace-nowrap px-3 py-2 text-text">
                        {row[key] === null || row[key] === undefined ? '—' : String(row[key])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

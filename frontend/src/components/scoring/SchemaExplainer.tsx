import { useState } from 'react'

import type { InputSchemaResponse } from '@/types/api'

export function SchemaExplainer({ schema }: { schema: InputSchemaResponse | undefined }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <h3 className="text-[15px] font-semibold text-text">What VENTORA needs to score inventory</h3>
      <p className="mt-1.5 text-[13.5px] leading-relaxed text-text-muted">
        Live scoring runs the same trained models used everywhere else in VENTORA. Those models expect two
        pre-engineered tables, not raw sales data — this isn't a simplified upload, it's the real input the models
        were trained on.
      </p>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-border bg-surface-sunken/50 p-4">
          <p className="text-[13px] font-semibold text-text">1. Batch-level data</p>
          <p className="mt-1 text-[12.5px] leading-relaxed text-text-muted">
            One row per inventory batch: what it is, when it was received, current stock, days until expiry, and
            its recent demand history (trailing averages, variability, SNAP/event day counts).
          </p>
        </div>
        <div className="rounded-xl border border-border bg-surface-sunken/50 p-4">
          <p className="text-[13px] font-semibold text-text">2. Category-demand data</p>
          <p className="mt-1 text-[12.5px] leading-relaxed text-text-muted">
            One row per product category represented in your batches: recent demand lags and rolling averages,
            used to forecast near-term demand for that category.
          </p>
        </div>
      </div>

      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className="mt-4 text-[12.5px] font-medium text-[color:var(--color-brand-green)] hover:underline"
      >
        {expanded ? 'Hide full field list' : 'Show full field list'}
      </button>

      {expanded && schema && (
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <p className="mb-2 text-[11.5px] font-semibold uppercase tracking-wide text-text-muted">
              Batch-level fields
            </p>
            <ul className="space-y-2">
              {schema.batch_fields.map((f) => (
                <li key={f.name} className="text-[12.5px]">
                  <span className="tabular-figures font-semibold text-text">{f.name}</span>{' '}
                  <span className="text-text-muted">— {f.description}</span>
                  {f.allowed_values && (
                    <div className="mt-0.5 text-[11px] text-text-muted">
                      Allowed: {f.allowed_values.join(', ')}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="mb-2 text-[11.5px] font-semibold uppercase tracking-wide text-text-muted">
              Category-demand fields
            </p>
            <ul className="space-y-2">
              {schema.category_demand_fields.map((f) => (
                <li key={f.name} className="text-[12.5px]">
                  <span className="tabular-figures font-semibold text-text">{f.name}</span>{' '}
                  <span className="text-text-muted">— {f.description}</span>
                  {f.allowed_values && (
                    <div className="mt-0.5 text-[11px] text-text-muted">
                      Allowed: {f.allowed_values.join(', ')}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}

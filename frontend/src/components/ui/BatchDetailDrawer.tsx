import { RiskBadge } from '@/components/ui/RiskBadge'
import { MetricDisplay } from '@/components/ui/MetricDisplay'
import { CloseIcon } from '@/components/ui/icons'
import { INTERVENTION_SCOPE_LABEL, formatNumber, formatProbability } from '@/theme/risk'
import type { BatchRecord } from '@/types/api'

export function BatchDetailDrawer({ batch, onClose }: { batch: BatchRecord | null; onClose: () => void }) {
  if (!batch) return null

  return (
    <div className="fixed inset-0 z-50">
      <button type="button" aria-label="Close details" className="absolute inset-0 bg-black/40" onClick={onClose} />
      <aside className="absolute right-0 top-0 flex h-dvh w-full max-w-[420px] flex-col bg-surface shadow-xl">
        <div className="flex items-start justify-between gap-3 border-b border-border px-5 py-4">
          <div>
            <p className="text-[12px] font-medium text-text-muted">Batch</p>
            <p className="tabular-figures text-[16px] font-semibold text-text">{batch.batch_id}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close details"
            className="rounded-lg p-1.5 text-text-muted hover:bg-surface-sunken hover:text-text"
          >
            <CloseIcon />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          <div className="flex items-center gap-2">
            <RiskBadge level={batch.risk_level} />
            <span className="text-[12.5px] text-text-muted">
              {INTERVENTION_SCOPE_LABEL[batch.intervention_scope] ?? batch.intervention_scope}
            </span>
          </div>

          <div className="mt-5">
            <h3 className="text-[11px] font-semibold uppercase tracking-wide text-text-muted">Item</h3>
            <div className="mt-1 divide-y divide-border">
              <MetricDisplay label="Item ID" value={batch.item_id} />
              <MetricDisplay label="Category" value={batch.category} />
              {batch.food_category && <MetricDisplay label="Food category" value={batch.food_category} />}
            </div>
          </div>

          <div className="mt-5">
            <h3 className="text-[11px] font-semibold uppercase tracking-wide text-text-muted">Inventory & demand</h3>
            <div className="mt-1 divide-y divide-border">
              <MetricDisplay label="Days until expiry" value={formatNumber(batch.days_until_expiry)} />
              <MetricDisplay label="Current inventory" value={formatNumber(batch.current_inventory)} />
              <MetricDisplay
                label="Expected demand before expiry"
                value={formatNumber(batch.expected_demand_before_expiry, 1)}
              />
              <MetricDisplay
                label="Potential excess inventory"
                value={formatNumber(batch.potential_excess_inventory, 1)}
                emphasis
              />
            </div>
          </div>

          <div className="mt-5">
            <h3 className="text-[11px] font-semibold uppercase tracking-wide text-text-muted">Risk assessment</h3>
            <div className="mt-1 divide-y divide-border">
              <MetricDisplay label="Spoilage probability" value={formatProbability(batch.spoilage_probability)} />
              <MetricDisplay
                label="Expected waste exposure"
                value={formatNumber(batch.expected_waste_exposure, 1)}
                emphasis
              />
              <MetricDisplay label="Risk score" value={formatProbability(batch.risk_score)} emphasis />
            </div>
          </div>

          <div className="mt-5">
            <h3 className="text-[11px] font-semibold uppercase tracking-wide text-text-muted">Recommendation</h3>
            <p className="mt-2 rounded-xl border border-border bg-surface-sunken/60 p-3 text-[13.5px] leading-relaxed text-text">
              {batch.recommendation}
            </p>
          </div>
        </div>
      </aside>
    </div>
  )
}

import { useState } from 'react'

import { EmptyState } from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/ErrorState'
import { Pagination } from '@/components/ui/Pagination'
import { PageHeader } from '@/components/ui/PageHeader'
import { RiskBadge } from '@/components/ui/RiskBadge'
import { TableSkeleton } from '@/components/ui/LoadingSkeleton'
import { useRecommendations } from '@/hooks/useApiQueries'
import { INTERVENTION_SCOPE_LABEL, RISK_COLOR, formatNumber } from '@/theme/risk'
import type { RiskLevel } from '@/types/api'

const PAGE_SIZE = 12

const TABS: RiskLevel[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']

export function RecommendationsPage() {
  const [activeTab, setActiveTab] = useState<RiskLevel>('CRITICAL')
  const [page, setPage] = useState(1)

  const { data, isLoading, isFetching, isError, error, refetch } = useRecommendations(activeTab, page, PAGE_SIZE)

  function handleTabChange(level: RiskLevel) {
    setActiveTab(level)
    setPage(1)
  }

  return (
    <div>
      <PageHeader
        title="Recommendations"
        description="Concrete, scoped actions for each batch — grouped by risk level and ranked by expected waste exposure."
      />

      <div className="mb-5 flex flex-wrap gap-2 border-b border-border pb-3" role="tablist">
        {TABS.map((level) => {
          const active = level === activeTab
          return (
            <button
              key={level}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => handleTabChange(level)}
              className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-[13px] font-semibold transition-colors ${
                active ? 'text-white' : 'border border-border-strong text-text-muted hover:text-text'
              }`}
              style={active ? { backgroundColor: RISK_COLOR[level] } : undefined}
            >
              <span
                className="h-1.5 w-1.5 rounded-full"
                style={{ backgroundColor: active ? 'white' : RISK_COLOR[level] }}
              />
              {level}
            </button>
          )
        })}
      </div>

      {(activeTab === 'HIGH' || activeTab === 'CRITICAL') && (
        <div className="mb-5 rounded-xl border border-[color:var(--color-warning)]/40 bg-[color:var(--color-warning)]/10 px-4 py-3 text-[13px] text-text">
          These batches carry the highest expected waste exposure. Recommendations reflect a small-batch snapshot —
          verify against live inventory counts before acting at scale.
        </div>
      )}

      {isError ? (
        <ErrorState message={error instanceof Error ? error.message : 'Unknown error'} onRetry={() => refetch()} />
      ) : isLoading || !data ? (
        <TableSkeleton rows={6} cols={4} />
      ) : data.rows.length === 0 ? (
        <EmptyState title={`No ${activeTab.toLowerCase()} risk batches`} description="Nothing to show for this risk level right now." />
      ) : (
        <>
          <div className={`grid grid-cols-1 gap-3 transition-opacity lg:grid-cols-2 ${isFetching ? 'opacity-60' : ''}`}>
            {data.rows.map((rec) => (
              <div key={rec.batch_id} className="rounded-2xl border border-border bg-surface p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="tabular-figures text-[13px] font-semibold text-text">{rec.batch_id}</p>
                    <p className="text-[12px] text-text-muted">
                      {rec.item_id} · {rec.category}
                    </p>
                  </div>
                  <RiskBadge level={rec.risk_level} size="sm" />
                </div>

                <p className="mt-3 text-[13.5px] leading-relaxed text-text">{rec.recommendation}</p>

                <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 border-t border-border pt-3 text-[12px] text-text-muted">
                  <span>
                    Scope:{' '}
                    <span className="font-medium text-text">
                      {INTERVENTION_SCOPE_LABEL[rec.intervention_scope] ?? rec.intervention_scope}
                    </span>
                  </span>
                  <span className="tabular-figures">Days to expiry: {formatNumber(rec.days_until_expiry)}</span>
                  <span className="tabular-figures">Excess: {formatNumber(rec.potential_excess_inventory, 1)}</span>
                  <span className="tabular-figures">Waste exposure: {formatNumber(rec.expected_waste_exposure, 1)}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 overflow-hidden rounded-2xl border border-border bg-surface">
            <Pagination
              page={data.page}
              totalPages={data.total_pages}
              totalRows={data.total_rows}
              pageSize={data.page_size}
              onPageChange={setPage}
              itemLabel={`${activeTab.toLowerCase()} risk batches`}
            />
          </div>
        </>
      )}
    </div>
  )
}

import { ChartCard } from '@/components/ui/ChartCard'
import { InterventionScopeChart } from '@/components/charts/InterventionScopeChart'
import { RiskDistributionChart } from '@/components/charts/RiskDistributionChart'
import { SpoilageRateChart } from '@/components/charts/SpoilageRateChart'
import { ErrorState } from '@/components/ui/ErrorState'
import { KpiCard } from '@/components/ui/KpiCard'
import { ChartCardSkeleton, KpiCardSkeleton } from '@/components/ui/LoadingSkeleton'
import { PageHeader } from '@/components/ui/PageHeader'
import { useSummary } from '@/hooks/useApiQueries'
import { formatNumber, formatPercent } from '@/theme/risk'

export function OverviewPage() {
  const { data, isLoading, isError, error, refetch } = useSummary()

  return (
    <div>
      <PageHeader
        title="Executive Overview"
        description="Portfolio-level view of expiry risk, model calibration, and intervention scope across all assessed batches."
      />

      {isError ? (
        <ErrorState message={error instanceof Error ? error.message : 'Unknown error'} onRetry={() => refetch()} />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {isLoading || !data ? (
              Array.from({ length: 4 }).map((_, i) => <KpiCardSkeleton key={i} />)
            ) : (
              <>
                <KpiCard label="Total batches assessed" value={formatNumber(data.total_batches)} />
                <KpiCard
                  label="High + Critical risk"
                  value={formatNumber(data.high_critical_batches)}
                  subValue={`${formatPercent(data.high_critical_pct_of_total)} of total`}
                  tone="danger"
                />
                <KpiCard
                  label="Total expected waste exposure"
                  value={formatNumber(data.total_expected_waste_exposure)}
                  subValue="units, across all batches"
                />
                <KpiCard
                  label="Simulated waste reduction"
                  value={formatPercent(data.base_scenario_waste_reduction_pct)}
                  subValue="base scenario vs. baseline"
                  tone="success"
                />
              </>
            )}
          </div>

          <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
            {isLoading || !data ? (
              <>
                <ChartCardSkeleton />
                <ChartCardSkeleton />
              </>
            ) : (
              <>
                <ChartCard title="Risk distribution" caption="Batch count and share by risk level">
                  <RiskDistributionChart data={data.risk_distribution} />
                </ChartCard>
                <ChartCard
                  title="Spoilage rate by risk level"
                  caption="Observed spoilage rate — validates that higher risk levels correspond to higher actual spoilage"
                >
                  <SpoilageRateChart data={data.spoilage_rate_by_risk_level} />
                </ChartCard>
              </>
            )}
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
            {isLoading || !data ? (
              <ChartCardSkeleton height={200} />
            ) : (
              <ChartCard title="Intervention scope summary" caption="Where recommended action applies">
                <InterventionScopeChart data={data.intervention_scope_summary} />
              </ChartCard>
            )}

            {!isLoading && data && (
              <div className="rounded-2xl border border-border bg-surface p-5">
                <h3 className="text-[15px] font-semibold text-text">What this means</h3>
                <ul className="mt-3 space-y-2.5 text-[13.5px] leading-relaxed text-text-muted">
                  <li>
                    <span className="font-semibold text-text">
                      {formatNumber(data.high_critical_batches)} of {formatNumber(data.total_batches)} batches
                    </span>{' '}
                    ({formatPercent(data.high_critical_pct_of_total)}) are currently at High or Critical risk of
                    expiry-driven waste.
                  </li>
                  <li>
                    Observed spoilage rate rises monotonically from Low to Critical risk level, indicating the risk
                    score tracks real outcomes.
                  </li>
                  <li>
                    <span className="font-semibold text-text">
                      {formatNumber(data.intervention_scope_summary.batch_level)} batches
                    </span>{' '}
                    require a direct batch-level action; the rest need only replenishment adjustment or no action.
                  </li>
                </ul>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

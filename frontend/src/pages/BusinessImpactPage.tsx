import { BusinessValueChart } from '@/components/charts/BusinessValueChart'
import { ChartCard } from '@/components/ui/ChartCard'
import { ErrorState } from '@/components/ui/ErrorState'
import { ChartCardSkeleton, KpiCardSkeleton } from '@/components/ui/LoadingSkeleton'
import { KpiCard } from '@/components/ui/KpiCard'
import { PageHeader } from '@/components/ui/PageHeader'
import { useBusinessValue, useSummary } from '@/hooks/useApiQueries'
import { formatNumber, formatPercent } from '@/theme/risk'

export function BusinessImpactPage() {
  const { data, isLoading, isError, error, refetch } = useBusinessValue()
  const { data: summary } = useSummary()

  const baseScenario = data?.scenarios.find((s) => s.scenario === 'Base')

  return (
    <div>
      <PageHeader
        title="Business Impact"
        description="Simulated waste and spoilage-rate reduction from AI-assisted intervention, across three scenarios."
      />

      {isError ? (
        <ErrorState message={error instanceof Error ? error.message : 'Unknown error'} onRetry={() => refetch()} />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {isLoading || !baseScenario ? (
              Array.from({ length: 4 }).map((_, i) => <KpiCardSkeleton key={i} />)
            ) : (
              <>
                <KpiCard
                  label="Waste reduction (base scenario)"
                  value={formatPercent(baseScenario.waste_reduction_pct)}
                  tone="success"
                />
                <KpiCard
                  label="Spoilage rate reduction"
                  value={`${baseScenario.spoilage_rate_reduction_pp.toFixed(2)} pp`}
                  subValue="percentage points"
                />
                <KpiCard
                  label="Baseline waste units"
                  value={formatNumber(baseScenario.baseline_waste_units)}
                  subValue={`vs. ${formatNumber(baseScenario.ai_assisted_waste_units)} AI-assisted`}
                />
                <KpiCard
                  label="Forward-looking exposure"
                  value={summary ? formatNumber(summary.total_expected_waste_exposure) : '—'}
                  subValue="total expected waste exposure, units"
                />
              </>
            )}
          </div>

          <div className="mt-6">
            {isLoading || !data ? (
              <ChartCardSkeleton />
            ) : (
              <ChartCard
                title="Baseline vs. AI-assisted waste"
                caption="Simulated waste units per scenario — lower is better"
              >
                <BusinessValueChart data={data.scenarios} />
              </ChartCard>
            )}
          </div>

          <div className="mt-6">
            <h2 className="mb-3 text-[15px] font-semibold text-text">Scenario comparison</h2>
            {isLoading || !data ? (
              <div className="h-48 animate-pulse rounded-2xl bg-border" />
            ) : (
              <div className="overflow-x-auto rounded-2xl border border-border bg-surface">
                <table className="w-full min-w-[720px] border-collapse text-left text-[13px]">
                  <thead>
                    <tr className="border-b border-border bg-surface-sunken/60 text-text-muted">
                      <th className="px-4 py-2.5 font-semibold">Scenario</th>
                      <th className="px-4 py-2.5 font-semibold">Baseline waste</th>
                      <th className="px-4 py-2.5 font-semibold">AI-assisted waste</th>
                      <th className="px-4 py-2.5 font-semibold">Waste reduction</th>
                      <th className="px-4 py-2.5 font-semibold">Baseline spoilage rate</th>
                      <th className="px-4 py-2.5 font-semibold">AI-assisted spoilage rate</th>
                      <th className="px-4 py-2.5 font-semibold">Interventions (H+C)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.scenarios.map((s) => (
                      <tr key={s.scenario} className="border-b border-border last:border-b-0">
                        <td className="px-4 py-2.5 font-semibold text-text">{s.scenario}</td>
                        <td className="tabular-figures px-4 py-2.5">{formatNumber(s.baseline_waste_units)}</td>
                        <td className="tabular-figures px-4 py-2.5">{formatNumber(s.ai_assisted_waste_units)}</td>
                        <td className="tabular-figures px-4 py-2.5 font-semibold text-[color:var(--color-success)]">
                          {formatPercent(s.waste_reduction_pct)}
                        </td>
                        <td className="tabular-figures px-4 py-2.5">{formatPercent(s.baseline_spoilage_rate * 100)}</td>
                        <td className="tabular-figures px-4 py-2.5">{formatPercent(s.ai_assisted_spoilage_rate * 100)}</td>
                        <td className="tabular-figures px-4 py-2.5">{formatNumber(s.intervention_count_high_critical)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

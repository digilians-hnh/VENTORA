import { Link } from 'react-router-dom'
import type { ColumnDef } from '@tanstack/react-table'

import { RiskDistributionChart } from '@/components/charts/RiskDistributionChart'
import { ChartCard } from '@/components/ui/ChartCard'
import { DataTable } from '@/components/ui/DataTable'
import { KpiCard } from '@/components/ui/KpiCard'
import { RiskBadge } from '@/components/ui/RiskBadge'
import { formatNumber, formatProbability } from '@/theme/risk'
import type { RiskLevel, ScoredBatchRecord, ScoreResponse } from '@/types/api'

const columns: ColumnDef<ScoredBatchRecord, unknown>[] = [
  {
    header: 'Risk',
    accessorKey: 'risk_level',
    cell: ({ getValue }) => {
      const level = getValue() as RiskLevel | null
      return level ? <RiskBadge level={level} size="sm" /> : <span className="text-text-muted">—</span>
    },
  },
  { header: 'Batch ID', accessorKey: 'batch_id', cell: ({ getValue }) => <span className="tabular-figures">{getValue() as string}</span> },
  { header: 'Item', accessorKey: 'item_id', cell: ({ getValue }) => <span className="tabular-figures">{getValue() as string}</span> },
  { header: 'Category', accessorKey: 'category' },
  {
    header: 'Spoilage prob.',
    accessorKey: 'spoilage_probability',
    cell: ({ getValue }) => <span className="tabular-figures">{formatProbability(getValue() as number)}</span>,
  },
  {
    header: 'Waste exposure',
    accessorKey: 'expected_waste_exposure',
    cell: ({ getValue }) => <span className="tabular-figures">{formatNumber(getValue() as number, 1)}</span>,
  },
  {
    header: 'Risk score',
    accessorKey: 'risk_score',
    cell: ({ getValue }) => <span className="tabular-figures font-semibold">{formatProbability(getValue() as number)}</span>,
  },
  { header: 'Recommendation', accessorKey: 'recommendation', cell: ({ getValue }) => (
    <span className="block max-w-xs truncate" title={getValue() as string}>{getValue() as string}</span>
  ) },
]

export function ScoreResultsPanel({ result }: { result: ScoreResponse }) {
  const { summary } = result

  return (
    <div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Records scored" value={formatNumber(summary.total_records_scored)} />
        <KpiCard
          label="High + Critical"
          value={formatNumber(summary.high_critical_count)}
          tone="danger"
        />
        <KpiCard
          label="Avg. risk score"
          value={summary.average_risk_score !== null ? formatProbability(summary.average_risk_score) : '—'}
        />
        <KpiCard
          label="Total waste exposure"
          value={summary.total_expected_waste_exposure !== null ? formatNumber(summary.total_expected_waste_exposure, 1) : '—'}
          subValue="units"
        />
      </div>

      <div className="mt-4 rounded-xl border border-[color:var(--color-warning)]/40 bg-[color:var(--color-warning)]/10 px-4 py-3 text-[13px] text-text">
        {result.methodology_note}
      </div>

      {summary.unresolved_count > 0 && (
        <div className="mt-3 rounded-xl border border-border-strong bg-surface-sunken/60 px-4 py-3 text-[13px] text-text-muted">
          {summary.unresolved_count} record{summary.unresolved_count === 1 ? '' : 's'} could not be scored (see the
          "—" rows below) — typically an item_id the models weren't trained on.
        </div>
      )}

      <div className="mt-6">
        <ChartCard title="Risk distribution" caption="Across the batches scored in this run">
          <RiskDistributionChart data={summary.risk_distribution} />
        </ChartCard>
      </div>

      <div className="mt-6">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-[15px] font-semibold text-text">Scored batches</h3>
          <Link
            to="/recommendations"
            className="text-[12.5px] font-medium text-[color:var(--color-brand-green)] hover:underline"
          >
            View Recommendations →
          </Link>
        </div>
        <div className="overflow-hidden rounded-2xl border border-border bg-surface">
          <DataTable data={result.rows} columns={columns} getRowId={(r) => r.batch_id} />
        </div>
      </div>
    </div>
  )
}

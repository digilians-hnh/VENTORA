import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { INTERVENTION_SCOPE_COLOR } from '@/theme/risk'
import type { InterventionScopeSummary } from '@/types/api'

interface ScopeDatum {
  key: string
  label: string
  count: number
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: { payload: ScopeDatum }[] }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="rounded-lg border border-border bg-surface px-3 py-2 text-[12.5px] shadow-[var(--shadow-card-hover)]">
      <p className="font-semibold text-text">{d.label}</p>
      <p className="tabular-figures text-text-muted">{d.count.toLocaleString()} batches</p>
    </div>
  )
}

export function InterventionScopeChart({ data }: { data: InterventionScopeSummary }) {
  const rows: ScopeDatum[] = [
    { key: 'batch-level', label: 'Batch-level action', count: data.batch_level },
    { key: 'replenishment-only (future batches)', label: 'Replenishment only', count: data.replenishment_only },
    { key: 'none', label: 'No action needed', count: data.none },
  ]

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={rows} layout="vertical" margin={{ top: 0, right: 24, left: 0, bottom: 0 }} barCategoryGap="30%">
        <CartesianGrid horizontal={false} stroke="var(--color-border)" />
        <XAxis type="number" tick={{ fontSize: 11.5, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} />
        <YAxis
          type="category"
          dataKey="label"
          width={140}
          tick={{ fontSize: 12.5, fill: 'var(--color-text)' }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip cursor={{ fill: 'var(--color-surface-sunken)' }} content={<ChartTooltip />} />
        <Bar dataKey="count" radius={[0, 6, 6, 0]} maxBarSize={28}>
          {rows.map((r) => (
            <Cell key={r.key} fill={INTERVENTION_SCOPE_COLOR[r.key]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

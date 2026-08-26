import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { RISK_COLOR, RISK_LABEL } from '@/theme/risk'
import type { RiskDistributionEntry } from '@/types/api'

interface TooltipPayloadItem {
  payload: RiskDistributionEntry
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: TooltipPayloadItem[] }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="rounded-lg border border-border bg-surface px-3 py-2 text-[12.5px] shadow-[var(--shadow-card-hover)]">
      <p className="font-semibold text-text">{RISK_LABEL[d.risk_level]}</p>
      <p className="tabular-figures text-text-muted">
        {d.count.toLocaleString()} batches · {d.pct_of_total.toFixed(1)}%
      </p>
    </div>
  )
}

export function RiskDistributionChart({ data }: { data: RiskDistributionEntry[] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 12, left: -12, bottom: 0 }} barCategoryGap="28%">
        <CartesianGrid vertical={false} stroke="var(--color-border)" />
        <XAxis
          dataKey="risk_level"
          tickFormatter={(v: string) => RISK_LABEL[v as keyof typeof RISK_LABEL]}
          tick={{ fontSize: 12.5, fill: 'var(--color-text-muted)' }}
          axisLine={{ stroke: 'var(--color-border)' }}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11.5, fill: 'var(--color-text-muted)' }}
          axisLine={false}
          tickLine={false}
          width={44}
        />
        <Tooltip cursor={{ fill: 'var(--color-surface-sunken)' }} content={<ChartTooltip />} />
        <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={64}>
          {data.map((entry) => (
            <Cell key={entry.risk_level} fill={RISK_COLOR[entry.risk_level]} />
          ))}
          <LabelList
            dataKey="pct_of_total"
            position="top"
            formatter={(v: unknown) => `${Number(v).toFixed(1)}%`}
            style={{ fontSize: 11, fill: 'var(--color-text-muted)', fontWeight: 600 }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

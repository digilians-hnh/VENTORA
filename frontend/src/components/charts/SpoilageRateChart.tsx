import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { RISK_COLOR, RISK_LABEL } from '@/theme/risk'
import type { SpoilageRateEntry } from '@/types/api'

interface TooltipPayloadItem {
  payload: SpoilageRateEntry
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: TooltipPayloadItem[] }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="rounded-lg border border-border bg-surface px-3 py-2 text-[12.5px] shadow-[var(--shadow-card-hover)]">
      <p className="font-semibold text-text">{RISK_LABEL[d.risk_level]}</p>
      <p className="tabular-figures text-text-muted">
        {(d.observed_spoilage_rate * 100).toFixed(1)}% observed spoilage
      </p>
    </div>
  )
}

export function SpoilageRateChart({ data }: { data: SpoilageRateEntry[] }) {
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
          tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
          tick={{ fontSize: 11.5, fill: 'var(--color-text-muted)' }}
          axisLine={false}
          tickLine={false}
          width={44}
        />
        <Tooltip cursor={{ fill: 'var(--color-surface-sunken)' }} content={<ChartTooltip />} />
        <Bar dataKey="observed_spoilage_rate" radius={[6, 6, 0, 0]} maxBarSize={64}>
          {data.map((entry) => (
            <Cell key={entry.risk_level} fill={RISK_COLOR[entry.risk_level]} fillOpacity={0.85} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

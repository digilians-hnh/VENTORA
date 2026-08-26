import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import type { BusinessValueScenario } from '@/types/api'

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: { name: string; value: number; color: string }[]
  label?: string
}) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-border bg-surface px-3 py-2 text-[12.5px] shadow-[var(--shadow-card-hover)]">
      <p className="font-semibold text-text">{label}</p>
      {payload.map((p) => (
        <p key={p.name} className="tabular-figures text-text-muted">
          <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: p.color, marginRight: 6 }} />
          {p.name}: {p.value.toLocaleString(undefined, { maximumFractionDigits: 0 })} units
        </p>
      ))}
    </div>
  )
}

export function BusinessValueChart({ data }: { data: BusinessValueScenario[] }) {
  const rows = data.map((s) => ({
    scenario: s.scenario,
    Baseline: s.baseline_waste_units,
    'AI-Assisted': s.ai_assisted_waste_units,
  }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={rows} margin={{ top: 8, right: 12, left: -8, bottom: 0 }} barCategoryGap="24%" barGap={4}>
        <CartesianGrid vertical={false} stroke="var(--color-border)" />
        <XAxis dataKey="scenario" tick={{ fontSize: 12.5, fill: 'var(--color-text-muted)' }} axisLine={{ stroke: 'var(--color-border)' }} tickLine={false} />
        <YAxis tick={{ fontSize: 11.5, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} width={50} />
        <Tooltip cursor={{ fill: 'var(--color-surface-sunken)' }} content={<ChartTooltip />} />
        <Legend wrapperStyle={{ fontSize: 12.5 }} iconType="circle" iconSize={8} />
        <Bar dataKey="Baseline" fill="#82908a" radius={[6, 6, 0, 0]} maxBarSize={48} />
        <Bar dataKey="AI-Assisted" fill="#2e7926" radius={[6, 6, 0, 0]} maxBarSize={48} />
      </BarChart>
    </ResponsiveContainer>
  )
}

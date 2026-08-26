import { RISK_COLOR, RISK_COLOR_SOFT, RISK_LABEL } from '@/theme/risk'
import type { RiskLevel } from '@/types/api'

export function RiskBadge({ level, size = 'md' }: { level: RiskLevel; size?: 'sm' | 'md' }) {
  const color = RISK_COLOR[level]
  const bg = RISK_COLOR_SOFT[level]
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-semibold ${
        size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs'
      }`}
      style={{ color, backgroundColor: bg }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: color }} aria-hidden="true" />
      {RISK_LABEL[level]}
    </span>
  )
}

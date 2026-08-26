import type { ReactNode } from 'react'

interface KpiCardProps {
  label: string
  value: string
  subValue?: string
  tone?: 'default' | 'success' | 'danger'
  helpText?: string
  icon?: ReactNode
}

const toneClasses: Record<NonNullable<KpiCardProps['tone']>, string> = {
  default: 'text-text',
  success: 'text-[color:var(--color-success)]',
  danger: 'text-[color:var(--color-danger)]',
}

export function KpiCard({ label, value, subValue, tone = 'default', helpText, icon }: KpiCardProps) {
  return (
    <div className="group relative rounded-2xl border border-border bg-surface p-5 shadow-[var(--shadow-card)] transition-shadow hover:shadow-[var(--shadow-card-hover)]">
      <div className="flex items-start justify-between gap-2">
        <p className="text-[13px] font-medium text-text-muted">{label}</p>
        {icon && <div className="text-text-muted/70">{icon}</div>}
      </div>
      <p className={`tabular-figures mt-2 text-[28px] font-semibold leading-none ${toneClasses[tone]}`}>
        {value}
      </p>
      {subValue && <p className="mt-2 text-[13px] text-text-muted">{subValue}</p>}
      {helpText && (
        <p className="mt-2 border-t border-border pt-2 text-[12px] leading-snug text-text-muted/80">
          {helpText}
        </p>
      )}
    </div>
  )
}

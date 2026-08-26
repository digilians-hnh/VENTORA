import type { ReactNode } from 'react'

interface ChartCardProps {
  title: string
  caption?: string
  children: ReactNode
  action?: ReactNode
}

export function ChartCard({ title, caption, children, action }: ChartCardProps) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5 shadow-[var(--shadow-card)]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-[15px] font-semibold text-text">{title}</h3>
          {caption && <p className="mt-0.5 text-[13px] text-text-muted">{caption}</p>}
        </div>
        {action}
      </div>
      <div className="mt-4">{children}</div>
    </div>
  )
}

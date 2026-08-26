function Bone({ className = '', style }: { className?: string; style?: React.CSSProperties }) {
  return <div className={`animate-pulse rounded-md bg-border ${className}`} style={style} />
}

export function KpiCardSkeleton() {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <Bone className="h-3 w-24" />
      <Bone className="mt-3 h-7 w-20" />
      <Bone className="mt-3 h-3 w-32" />
    </div>
  )
}

export function ChartCardSkeleton({ height = 280 }: { height?: number }) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <Bone className="h-4 w-40" />
      <Bone className="mt-2 h-3 w-56" />
      <Bone className="mt-4 w-full" style={{ height }} />
    </div>
  )
}

export function TableSkeleton({ rows = 8, cols = 6 }: { rows?: number; cols?: number }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-surface">
      <div className="border-b border-border p-3">
        <Bone className="h-4 w-full max-w-md" />
      </div>
      <div className="divide-y divide-border">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="flex items-center gap-4 px-4 py-3">
            {Array.from({ length: cols }).map((__, c) => (
              <Bone key={c} className="h-3 flex-1" />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

export function MetricDisplay({
  label,
  value,
  emphasis = false,
}: {
  label: string
  value: string
  emphasis?: boolean
}) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-2">
      <span className="text-[13px] text-text-muted">{label}</span>
      <span
        className={`tabular-figures text-right text-[14px] ${
          emphasis ? 'font-semibold text-text' : 'font-medium text-text'
        }`}
      >
        {value}
      </span>
    </div>
  )
}

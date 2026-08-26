import { RISK_COLOR, RISK_LABEL } from '@/theme/risk'
import type { RiskLevel } from '@/types/api'

const CATEGORY_OPTIONS = ['FOODS_1', 'FOODS_2', 'FOODS_3']

export interface RiskExplorerFilters {
  riskLevels: RiskLevel[]
  categories: string[]
  minDaysToExpiry: number | undefined
  maxDaysToExpiry: number | undefined
  minExcess: number | undefined
}

interface FilterBarProps {
  filters: RiskExplorerFilters
  onChange: (filters: RiskExplorerFilters) => void
  onReset: () => void
}

const RISK_LEVELS: RiskLevel[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

export function FilterBar({ filters, onChange, onReset }: FilterBarProps) {
  function toggleRiskLevel(level: RiskLevel) {
    const has = filters.riskLevels.includes(level)
    onChange({
      ...filters,
      riskLevels: has ? filters.riskLevels.filter((l) => l !== level) : [...filters.riskLevels, level],
    })
  }

  function toggleCategory(cat: string) {
    const has = filters.categories.includes(cat)
    onChange({
      ...filters,
      categories: has ? filters.categories.filter((c) => c !== cat) : [...filters.categories, cat],
    })
  }

  const hasActiveFilters =
    filters.riskLevels.length > 0 ||
    filters.categories.length > 0 ||
    filters.minDaysToExpiry !== undefined ||
    filters.maxDaysToExpiry !== undefined ||
    filters.minExcess !== undefined

  return (
    <div className="rounded-2xl border border-border bg-surface p-4">
      <div className="flex flex-wrap items-start gap-x-8 gap-y-4">
        <fieldset>
          <legend className="mb-2 text-[12px] font-semibold uppercase tracking-wide text-text-muted">
            Risk level
          </legend>
          <div className="flex flex-wrap gap-1.5">
            {RISK_LEVELS.map((level) => {
              const active = filters.riskLevels.includes(level)
              return (
                <button
                  key={level}
                  type="button"
                  aria-pressed={active}
                  onClick={() => toggleRiskLevel(level)}
                  className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[12.5px] font-medium transition-colors"
                  style={
                    active
                      ? { borderColor: RISK_COLOR[level], backgroundColor: `${RISK_COLOR[level]}1a`, color: RISK_COLOR[level] }
                      : { borderColor: 'var(--color-border-strong)', color: 'var(--color-text-muted)' }
                  }
                >
                  <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: RISK_COLOR[level] }} />
                  {RISK_LABEL[level]}
                </button>
              )
            })}
          </div>
        </fieldset>

        <fieldset>
          <legend className="mb-2 text-[12px] font-semibold uppercase tracking-wide text-text-muted">
            Category
          </legend>
          <div className="flex flex-wrap gap-1.5">
            {CATEGORY_OPTIONS.map((cat) => {
              const active = filters.categories.includes(cat)
              return (
                <button
                  key={cat}
                  type="button"
                  aria-pressed={active}
                  onClick={() => toggleCategory(cat)}
                  className={`rounded-full border px-3 py-1.5 text-[12.5px] font-medium transition-colors ${
                    active
                      ? 'border-[color:var(--color-brand-green)] bg-[color:var(--color-brand-green)]/10 text-[color:var(--color-brand-green)]'
                      : 'border-border-strong text-text-muted'
                  }`}
                >
                  {cat}
                </button>
              )
            })}
          </div>
        </fieldset>

        <fieldset className="flex gap-3">
          <legend className="mb-2 w-full text-[12px] font-semibold uppercase tracking-wide text-text-muted">
            Days to expiry
          </legend>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] text-text-muted">Min</span>
            <input
              type="number"
              min={0}
              value={filters.minDaysToExpiry ?? ''}
              onChange={(e) =>
                onChange({
                  ...filters,
                  minDaysToExpiry: e.target.value === '' ? undefined : Number(e.target.value),
                })
              }
              className="w-20 rounded-lg border border-border-strong bg-surface px-2.5 py-1.5 text-[13px] tabular-figures focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--color-brand-green)]"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] text-text-muted">Max</span>
            <input
              type="number"
              min={0}
              value={filters.maxDaysToExpiry ?? ''}
              onChange={(e) =>
                onChange({
                  ...filters,
                  maxDaysToExpiry: e.target.value === '' ? undefined : Number(e.target.value),
                })
              }
              className="w-20 rounded-lg border border-border-strong bg-surface px-2.5 py-1.5 text-[13px] tabular-figures focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--color-brand-green)]"
            />
          </label>
        </fieldset>

        <fieldset>
          <legend className="mb-2 text-[12px] font-semibold uppercase tracking-wide text-text-muted">
            Min. excess
          </legend>
          <input
            type="number"
            min={0}
            value={filters.minExcess ?? ''}
            onChange={(e) =>
              onChange({ ...filters, minExcess: e.target.value === '' ? undefined : Number(e.target.value) })
            }
            className="w-24 rounded-lg border border-border-strong bg-surface px-2.5 py-1.5 text-[13px] tabular-figures focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--color-brand-green)]"
          />
        </fieldset>

        {hasActiveFilters && (
          <button
            type="button"
            onClick={onReset}
            className="ml-auto self-end text-[12.5px] font-medium text-text-muted underline decoration-dotted underline-offset-4 hover:text-text"
          >
            Clear filters
          </button>
        )}
      </div>
    </div>
  )
}

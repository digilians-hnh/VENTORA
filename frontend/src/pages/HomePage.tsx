import { Link } from 'react-router-dom'

import { ArrowRightIcon } from '@/components/ui/icons'
import { LogoFull } from '@/components/layout/Logo'
import { useSummary } from '@/hooks/useApiQueries'
import { formatNumber, formatPercent } from '@/theme/risk'

const VALUE_FLOW = [
  {
    step: '1',
    title: 'Forecast Demand',
    description: 'Predict expected demand per item before each batch reaches its expiry window.',
  },
  {
    step: '2',
    title: 'Predict Spoilage',
    description: 'Estimate spoilage probability for every batch using trained demand and shelf-life signals.',
  },
  {
    step: '3',
    title: 'Assess Expiry Risk',
    description: 'Combine spoilage probability and potential excess into a single risk score and level.',
  },
  {
    step: '4',
    title: 'Recommend Intervention',
    description: 'Translate each risk level into a concrete, scoped action — batch, replenishment, or none.',
  },
]

export function HomePage() {
  const { data: summary } = useSummary()

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl border border-border bg-[color:var(--color-deep-forest)] px-6 py-14 sm:px-12 sm:py-20">
        <div
          className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full opacity-20 blur-3xl"
          style={{ background: 'radial-gradient(circle, var(--color-signature-lime), transparent 70%)' }}
          aria-hidden="true"
        />
        <div className="relative mx-auto max-w-2xl text-center">
          <div className="mb-6 flex justify-center">
            <div className="rounded-2xl bg-[color:var(--color-off-white)] px-7 py-5 shadow-lg">
              <LogoFull width={190} />
            </div>
          </div>
          <p className="text-[15px] font-semibold text-[color:var(--color-signature-lime)]">
            AI-Driven Inventory Intelligence
          </p>
          <p className="mx-auto mt-5 max-w-xl text-[15px] leading-relaxed text-text-on-dark-muted">
            VENTORA helps food retailers identify expiry risk, understand potential spoilage, prioritize
            interventions, and quantify business impact — before waste happens.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              to="/risk-explorer"
              className="inline-flex items-center gap-2 rounded-xl bg-[color:var(--color-signature-lime)] px-5 py-3 text-[14px] font-semibold text-[color:var(--color-deep-forest)] transition-transform hover:scale-[1.02] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              Explore Inventory Risk
              <ArrowRightIcon />
            </Link>
            <Link
              to="/business-impact"
              className="inline-flex items-center gap-2 rounded-xl border border-white/25 px-5 py-3 text-[14px] font-semibold text-white transition-colors hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              View Business Impact
            </Link>
          </div>
        </div>
      </section>

      {/* Value flow */}
      <section className="mt-12">
        <h2 className="text-center text-[13px] font-semibold uppercase tracking-wide text-text-muted">
          How it works
        </h2>
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {VALUE_FLOW.map((item, i) => (
            <div key={item.step} className="relative rounded-2xl border border-border bg-surface p-5">
              <span className="tabular-figures text-[12px] font-bold text-[color:var(--color-brand-green)]">
                {item.step.padStart(2, '0')}
              </span>
              <h3 className="mt-2 text-[15px] font-semibold text-text">{item.title}</h3>
              <p className="mt-1.5 text-[13px] leading-relaxed text-text-muted">{item.description}</p>
              {i < VALUE_FLOW.length - 1 && (
                <div className="absolute right-[-18px] top-1/2 hidden -translate-y-1/2 text-border-strong lg:block">
                  <ArrowRightIcon width={16} height={16} />
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Credibility / live data section */}
      <section className="mt-12 rounded-2xl border border-border bg-surface p-6 sm:p-8">
        <h2 className="text-[13px] font-semibold uppercase tracking-wide text-text-muted">
          Verified against real inventory data
        </h2>
        <div className="mt-4 grid grid-cols-2 gap-6 sm:grid-cols-4">
          <div>
            <p className="tabular-figures text-[26px] font-bold text-text">
              {summary ? formatNumber(summary.total_batches) : '—'}
            </p>
            <p className="text-[12.5px] text-text-muted">Batches assessed</p>
          </div>
          <div>
            <p className="tabular-figures text-[26px] font-bold text-[color:var(--color-danger)]">
              {summary ? formatNumber(summary.high_critical_batches) : '—'}
            </p>
            <p className="text-[12.5px] text-text-muted">High + Critical risk</p>
          </div>
          <div>
            <p className="tabular-figures text-[26px] font-bold text-[color:var(--color-success)]">
              {summary ? formatPercent(summary.base_scenario_waste_reduction_pct) : '—'}
            </p>
            <p className="text-[12.5px] text-text-muted">Simulated waste reduction (base scenario)</p>
          </div>
          <div>
            <p className="tabular-figures text-[26px] font-bold text-text">
              {summary ? formatNumber(summary.total_expected_waste_exposure, 0) : '—'}
            </p>
            <p className="text-[12.5px] text-text-muted">Total expected waste exposure (units)</p>
          </div>
        </div>
      </section>
    </div>
  )
}

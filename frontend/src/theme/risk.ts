import type { RiskLevel } from '@/types/api'

export const RISK_LEVEL_ORDER: RiskLevel[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

export const RISK_COLOR: Record<RiskLevel, string> = {
  LOW: '#2e9b62',
  MEDIUM: '#e3b93f',
  HIGH: '#e47a32',
  CRITICAL: '#c83c32',
}

export const RISK_COLOR_SOFT: Record<RiskLevel, string> = {
  LOW: '#e7f4ec',
  MEDIUM: '#fbf1dc',
  HIGH: '#fbe8d9',
  CRITICAL: '#f8e0dd',
}

export const RISK_LABEL: Record<RiskLevel, string> = {
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
  CRITICAL: 'Critical',
}

export const INTERVENTION_SCOPE_LABEL: Record<string, string> = {
  'batch-level': 'Batch-level action',
  'batch-level (monitor only)': 'Monitor only',
  'replenishment-only (future batches)': 'Replenishment only',
  none: 'No action needed',
}

export const INTERVENTION_SCOPE_COLOR: Record<string, string> = {
  'batch-level': '#c83c32',
  'batch-level (monitor only)': '#e47a32',
  'replenishment-only (future batches)': '#e3b93f',
  none: '#82908a',
}

export function formatNumber(value: number | null | undefined, fractionDigits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return value.toLocaleString('en-US', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  })
}

export function formatPercent(value: number | null | undefined, fractionDigits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return `${value.toLocaleString('en-US', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  })}%`
}

export function formatProbability(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

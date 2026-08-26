import { useState } from 'react'
import type { ColumnDef } from '@tanstack/react-table'

import { exportRowsToCsv } from '@/api/csvExport'
import { BatchDetailDrawer } from '@/components/ui/BatchDetailDrawer'
import { DataTable } from '@/components/ui/DataTable'
import { EmptyState } from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/ErrorState'
import { FilterBar, type RiskExplorerFilters } from '@/components/ui/FilterBar'
import { DownloadIcon } from '@/components/ui/icons'
import { Pagination } from '@/components/ui/Pagination'
import { PageHeader } from '@/components/ui/PageHeader'
import { RiskBadge } from '@/components/ui/RiskBadge'
import { TableSkeleton } from '@/components/ui/LoadingSkeleton'
import { useRiskDf } from '@/hooks/useApiQueries'
import { formatNumber, formatProbability } from '@/theme/risk'
import type { BatchRecord } from '@/types/api'

const PAGE_SIZE = 25

const DEFAULT_FILTERS: RiskExplorerFilters = {
  riskLevels: [],
  categories: [],
  minDaysToExpiry: undefined,
  maxDaysToExpiry: undefined,
  minExcess: undefined,
}

const columns: ColumnDef<BatchRecord, unknown>[] = [
  {
    header: 'Risk',
    accessorKey: 'risk_level',
    cell: ({ getValue }) => <RiskBadge level={getValue() as BatchRecord['risk_level']} size="sm" />,
  },
  { header: 'Batch ID', accessorKey: 'batch_id', cell: ({ getValue }) => <span className="tabular-figures">{getValue() as string}</span> },
  { header: 'Item', accessorKey: 'item_id', cell: ({ getValue }) => <span className="tabular-figures">{getValue() as string}</span> },
  { header: 'Category', accessorKey: 'category' },
  {
    header: 'Days to expiry',
    accessorKey: 'days_until_expiry',
    cell: ({ getValue }) => <span className="tabular-figures">{formatNumber(getValue() as number)}</span>,
  },
  {
    header: 'Current inv.',
    accessorKey: 'current_inventory',
    cell: ({ getValue }) => <span className="tabular-figures">{formatNumber(getValue() as number)}</span>,
  },
  {
    header: 'Excess',
    accessorKey: 'potential_excess_inventory',
    cell: ({ getValue }) => <span className="tabular-figures">{formatNumber(getValue() as number, 1)}</span>,
  },
  {
    header: 'Spoilage prob.',
    accessorKey: 'spoilage_probability',
    cell: ({ getValue }) => <span className="tabular-figures">{formatProbability(getValue() as number)}</span>,
  },
  {
    header: 'Waste exposure',
    accessorKey: 'expected_waste_exposure',
    cell: ({ getValue }) => <span className="tabular-figures">{formatNumber(getValue() as number, 1)}</span>,
  },
  {
    header: 'Risk score',
    accessorKey: 'risk_score',
    cell: ({ getValue }) => <span className="tabular-figures font-semibold">{formatProbability(getValue() as number)}</span>,
  },
]

export function RiskExplorerPage() {
  const [filters, setFilters] = useState<RiskExplorerFilters>(DEFAULT_FILTERS)
  const [page, setPage] = useState(1)
  const [selectedBatch, setSelectedBatch] = useState<BatchRecord | null>(null)

  const { data, isLoading, isFetching, isError, error, refetch } = useRiskDf({
    risk_level: filters.riskLevels.length ? filters.riskLevels : undefined,
    category: filters.categories.length ? filters.categories : undefined,
    min_days_to_expiry: filters.minDaysToExpiry,
    max_days_to_expiry: filters.maxDaysToExpiry,
    min_excess: filters.minExcess,
    page,
    page_size: PAGE_SIZE,
  })

  function handleFiltersChange(next: RiskExplorerFilters) {
    setFilters(next)
    setPage(1)
  }

  function handleExportCurrentPage() {
    if (!data?.rows.length) return
    exportRowsToCsv(
      data.rows,
      [
        { key: 'batch_id', header: 'Batch ID' },
        { key: 'item_id', header: 'Item ID' },
        { key: 'category', header: 'Category' },
        { key: 'food_category', header: 'Food Category' },
        { key: 'days_until_expiry', header: 'Days To Expiry' },
        { key: 'current_inventory', header: 'Current Inventory' },
        { key: 'expected_demand_before_expiry', header: 'Expected Demand' },
        { key: 'potential_excess_inventory', header: 'Potential Excess' },
        { key: 'spoilage_probability', header: 'Spoilage Probability' },
        { key: 'expected_waste_exposure', header: 'Expected Waste Exposure' },
        { key: 'risk_score', header: 'Risk Score' },
        { key: 'risk_level', header: 'Risk Level' },
        { key: 'intervention_scope', header: 'Intervention Scope' },
        { key: 'recommendation', header: 'Recommendation' },
      ],
      `ventora_risk_explorer_page-${data.page}.csv`,
    )
  }

  return (
    <div>
      <PageHeader
        title="Risk Explorer"
        description="Search and filter every assessed batch by risk level, category, expiry window, and excess inventory."
        actions={
          <button
            type="button"
            onClick={handleExportCurrentPage}
            disabled={!data?.rows.length}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border-strong px-3.5 py-2 text-[13px] font-medium text-text transition-colors hover:bg-surface-sunken disabled:cursor-not-allowed disabled:opacity-40"
          >
            <DownloadIcon width={16} height={16} />
            Export page (CSV)
          </button>
        }
      />

      <div className="mb-4">
        <FilterBar filters={filters} onChange={handleFiltersChange} onReset={() => handleFiltersChange(DEFAULT_FILTERS)} />
      </div>

      {isError ? (
        <ErrorState message={error instanceof Error ? error.message : 'Unknown error'} onRetry={() => refetch()} />
      ) : isLoading || !data ? (
        <TableSkeleton rows={10} cols={10} />
      ) : data.rows.length === 0 ? (
        <EmptyState
          title="No batches match these filters"
          description="Try widening the risk level, category, or expiry range."
          action={
            <button
              type="button"
              onClick={() => handleFiltersChange(DEFAULT_FILTERS)}
              className="rounded-lg border border-border-strong px-4 py-2 text-[13px] font-medium text-text hover:bg-surface-sunken"
            >
              Clear filters
            </button>
          }
        />
      ) : (
        <div className={`overflow-hidden rounded-2xl border border-border bg-surface transition-opacity ${isFetching ? 'opacity-60' : ''}`}>
          <DataTable data={data.rows} columns={columns} onRowClick={setSelectedBatch} getRowId={(r) => r.batch_id} />
          <Pagination
            page={data.page}
            totalPages={data.total_pages}
            totalRows={data.total_rows}
            pageSize={data.page_size}
            onPageChange={setPage}
          />
        </div>
      )}

      <BatchDetailDrawer batch={selectedBatch} onClose={() => setSelectedBatch(null)} />
    </div>
  )
}

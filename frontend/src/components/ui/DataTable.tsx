import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table'
import { useState } from 'react'

interface DataTableProps<T> {
  data: T[]
  columns: ColumnDef<T, unknown>[]
  onRowClick?: (row: T) => void
  getRowId?: (row: T) => string
}

export function DataTable<T>({ data, columns, onRowClick, getRowId }: DataTableProps<T>) {
  const [sorting, setSorting] = useState<SortingState>([])

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getRowId,
  })

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-left text-[13px]">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id} className="border-b border-border bg-surface-sunken/60">
              {headerGroup.headers.map((header) => {
                const sortable = header.column.getCanSort()
                const sortDir = header.column.getIsSorted()
                return (
                  <th key={header.id} className="whitespace-nowrap px-4 py-2.5 font-semibold text-text-muted">
                    {header.isPlaceholder ? null : sortable ? (
                      <button
                        type="button"
                        onClick={header.column.getToggleSortingHandler()}
                        className="flex items-center gap-1 text-left hover:text-text focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[color:var(--color-brand-green)]"
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        <span className="text-[10px] text-text-muted/70">
                          {sortDir === 'asc' ? '▲' : sortDir === 'desc' ? '▼' : ''}
                        </span>
                      </button>
                    ) : (
                      flexRender(header.column.columnDef.header, header.getContext())
                    )}
                  </th>
                )
              })}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              onClick={onRowClick ? () => onRowClick(row.original) : undefined}
              className={`border-b border-border last:border-b-0 ${
                onRowClick ? 'cursor-pointer transition-colors hover:bg-surface-sunken' : ''
              }`}
              tabIndex={onRowClick ? 0 : undefined}
              role={onRowClick ? 'button' : undefined}
              onKeyDown={
                onRowClick
                  ? (e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        onRowClick(row.original)
                      }
                    }
                  : undefined
              }
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="whitespace-nowrap px-4 py-2.5 text-text">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

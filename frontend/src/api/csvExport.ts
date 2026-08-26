export function exportRowsToCsv<T>(
  rows: T[],
  columns: { key: keyof T; header: string }[],
  filename: string,
): void {
  const escape = (value: unknown): string => {
    if (value === null || value === undefined) return ''
    const str = String(value)
    return /[",\n]/.test(str) ? `"${str.replace(/"/g, '""')}"` : str
  }

  const header = columns.map((c) => escape(c.header)).join(',')
  const lines = rows.map((row) => columns.map((c) => escape(row[c.key])).join(','))
  const csv = [header, ...lines].join('\n')

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

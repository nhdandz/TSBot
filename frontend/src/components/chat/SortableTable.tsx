import { useState, useMemo } from 'react'
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react'

interface SortableTableProps {
  headers: string[]
  rows: string[][]
}

type SortDir = 'asc' | 'desc' | null

export function SortableTable({ headers, rows }: SortableTableProps) {
  const [sortCol, setSortCol] = useState<number | null>(null)
  const [sortDir, setSortDir] = useState<SortDir>(null)

  function handleHeaderClick(idx: number) {
    if (sortCol !== idx) {
      setSortCol(idx)
      setSortDir('asc')
    } else if (sortDir === 'asc') {
      setSortDir('desc')
    } else {
      setSortCol(null)
      setSortDir(null)
    }
  }

  const sortedRows = useMemo(() => {
    if (sortCol === null || sortDir === null) return rows
    return [...rows].sort((a, b) => {
      const va = a[sortCol] ?? ''
      const vb = b[sortCol] ?? ''
      // Try numeric sort (handles scores like 26.4, 27.75)
      const na = parseFloat(va.replace(/,/g, '.'))
      const nb = parseFloat(vb.replace(/,/g, '.'))
      const cmp = !isNaN(na) && !isNaN(nb)
        ? na - nb
        : va.localeCompare(vb, 'vi', { sensitivity: 'base' })
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [rows, sortCol, sortDir])

  return (
    <div className="overflow-x-auto my-3 rounded-xl border border-border/40">
      <table className="min-w-full">
        <thead className="bg-muted/30">
          <tr>
            {headers.map((h, i) => (
              <th
                key={i}
                onClick={() => handleHeaderClick(i)}
                className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground cursor-pointer select-none hover:bg-muted/60 transition-colors group"
              >
                <span className="flex items-center gap-1">
                  {h}
                  {sortCol === i ? (
                    sortDir === 'asc'
                      ? <ChevronUp className="w-3 h-3 text-primary shrink-0" />
                      : <ChevronDown className="w-3 h-3 text-primary shrink-0" />
                  ) : (
                    <ChevronsUpDown className="w-3 h-3 opacity-30 group-hover:opacity-60 shrink-0 transition-opacity" />
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row, ri) => (
            <tr
              key={ri}
              className="border-b border-border/40 last:border-0 hover:bg-muted/10 transition-colors"
            >
              {headers.map((_, ci) => (
                <td key={ci} className="px-4 py-2 text-sm text-foreground/80">
                  {row[ci] ?? ''}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

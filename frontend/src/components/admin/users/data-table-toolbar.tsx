import { Table } from "@tanstack/react-table"
import { X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { DataTableFacetedFilter } from "./data-table-faceted-filter"

interface DataTableToolbarProps<TData> {
  table: Table<TData>
}

const statuses = [
  { value: "active", label: "Hoạt động", color: "bg-emerald-500" },
  { value: "inactive", label: "Không hoạt động", color: "bg-gray-500" },
  { value: "suspended", label: "Đình chỉ", color: "bg-red-500" },
]

const roles = [
  { value: "admin", label: "Admin" },
  { value: "editor", label: "Editor" },
  { value: "viewer", label: "Viewer" },
]

export function DataTableToolbar<TData>({
  table,
}: DataTableToolbarProps<TData>) {
  const isFiltered = table.getState().columnFilters.length > 0

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div className="flex flex-1 items-center gap-2 flex-wrap">
        <Input
          placeholder="Tìm kiếm theo tên..."
          value={(table.getColumn("username")?.getFilterValue() as string) ?? ""}
          onChange={(event) =>
            table.getColumn("username")?.setFilterValue(event.target.value)
          }
          className="h-9 w-[200px] lg:w-[280px] bg-white dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]"
        />
        {table.getColumn("status") && (
          <DataTableFacetedFilter
            column={table.getColumn("status")}
            title="Trạng thái"
            options={statuses}
          />
        )}
        {table.getColumn("role") && (
          <DataTableFacetedFilter
            column={table.getColumn("role")}
            title="Vai trò"
            options={roles}
          />
        )}
        {isFiltered && (
          <Button
            variant="ghost"
            onClick={() => table.resetColumnFilters()}
            className="h-9 px-2 lg:px-3 text-gray-600 dark:text-gray-400"
          >
            Xóa bộ lọc
            <X className="ml-2 h-4 w-4" />
          </Button>
        )}
      </div>
      <div className="flex items-center gap-2">
        {table.getFilteredSelectedRowModel().rows.length > 0 && (
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Đã chọn {table.getFilteredSelectedRowModel().rows.length} / {table.getFilteredRowModel().rows.length}
          </div>
        )}
      </div>
    </div>
  )
}

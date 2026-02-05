import * as React from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { DataTable } from "@/components/admin/users/data-table"
import { columns } from "@/components/admin/users/columns"
import { UserCommandPalette } from "@/components/admin/users/user-command-palette"
import { mockUsers } from "@/data/mock-users"
import type { User } from "@/types/user"

export default function UsersPage() {
  const [data] = React.useState<User[]>(mockUsers)
  const tableRef = React.useRef<any>(null)

  const handleFilterStatus = (status: string | null) => {
    // This would need to be connected to the DataTable's internal state
    // For now, we'll just log it
    console.log("Filter status:", status)
  }

  const handleSelectUser = (user: User) => {
    // Handle user selection from command palette
    console.log("Selected user:", user)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Quản lý Người dùng</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Quản lý tài khoản người dùng hệ thống
          </p>
        </div>
        <UserCommandPalette
          users={data}
          onFilterStatus={handleFilterStatus}
          onSelectUser={handleSelectUser}
        />
      </div>

      <Card className="bg-white dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.06]">
        <CardHeader>
          <CardTitle className="text-gray-900 dark:text-white">
            Danh sách người dùng ({data.length})
          </CardTitle>
          <CardDescription className="text-gray-500 dark:text-gray-400">
            Xem và quản lý tất cả người dùng trong hệ thống. Sử dụng{" "}
            <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border border-gray-200 dark:border-white/[0.08] bg-gray-100 dark:bg-white/[0.04] px-1.5 font-mono text-[10px] font-medium text-gray-500 dark:text-gray-400">
              <span className="text-xs">⌘</span>K
            </kbd>{" "}
            để tìm kiếm nhanh.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable columns={columns} data={data} />
        </CardContent>
      </Card>
    </div>
  )
}

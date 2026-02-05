import { Row } from "@tanstack/react-table"
import { MoreHorizontal, Pencil, Ban, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

import type { User } from "@/types/user"

interface UserRowActionsProps {
  row: Row<User>
}

export function UserRowActions({ row }: UserRowActionsProps) {
  const user = row.original

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="flex h-8 w-8 p-0 data-[state=open]:bg-gray-100 dark:data-[state=open]:bg-white/[0.06]"
        >
          <MoreHorizontal className="h-4 w-4" />
          <span className="sr-only">Mở menu</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[160px] bg-white dark:bg-[#0c0c14] border-gray-200 dark:border-white/[0.08]">
        <DropdownMenuItem className="hover:bg-gray-100 dark:hover:bg-white/[0.06]">
          <Pencil className="mr-2 h-3.5 w-3.5 text-gray-500" />
          Chỉnh sửa
        </DropdownMenuItem>
        <DropdownMenuItem className="hover:bg-gray-100 dark:hover:bg-white/[0.06]">
          <Ban className="mr-2 h-3.5 w-3.5 text-gray-500" />
          {user.status === "suspended" ? "Bỏ đình chỉ" : "Đình chỉ"}
        </DropdownMenuItem>
        <DropdownMenuSeparator className="bg-gray-200 dark:bg-white/[0.06]" />
        <DropdownMenuItem className="text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10">
          <Trash2 className="mr-2 h-3.5 w-3.5" />
          Xóa
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

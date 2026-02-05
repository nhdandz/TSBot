import { Column } from "@tanstack/react-table"
import { ArrowDown, ArrowUp, ChevronsUpDown, EyeOff } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface DataTableColumnHeaderProps<TData, TValue>
  extends React.HTMLAttributes<HTMLDivElement> {
  column: Column<TData, TValue>
  title: string
}

export function DataTableColumnHeader<TData, TValue>({
  column,
  title,
  className,
}: DataTableColumnHeaderProps<TData, TValue>) {
  if (!column.getCanSort()) {
    return <div className={cn(className)}>{title}</div>
  }

  return (
    <div className={cn("flex items-center space-x-2", className)}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="-ml-3 h-8 data-[state=open]:bg-accent hover:bg-gray-100 dark:hover:bg-white/[0.06]"
          >
            <span>{title}</span>
            {column.getIsSorted() === "desc" ? (
              <ArrowDown className="ml-2 h-4 w-4" />
            ) : column.getIsSorted() === "asc" ? (
              <ArrowUp className="ml-2 h-4 w-4" />
            ) : (
              <ChevronsUpDown className="ml-2 h-4 w-4" />
            )}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="bg-white dark:bg-[#0c0c14] border-gray-200 dark:border-white/[0.08]">
          <DropdownMenuItem onClick={() => column.toggleSorting(false)} className="hover:bg-gray-100 dark:hover:bg-white/[0.06]">
            <ArrowUp className="mr-2 h-3.5 w-3.5 text-gray-500" />
            Tăng dần
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => column.toggleSorting(true)} className="hover:bg-gray-100 dark:hover:bg-white/[0.06]">
            <ArrowDown className="mr-2 h-3.5 w-3.5 text-gray-500" />
            Giảm dần
          </DropdownMenuItem>
          <DropdownMenuSeparator className="bg-gray-200 dark:bg-white/[0.06]" />
          <DropdownMenuItem onClick={() => column.toggleVisibility(false)} className="hover:bg-gray-100 dark:hover:bg-white/[0.06]">
            <EyeOff className="mr-2 h-3.5 w-3.5 text-gray-500" />
            Ẩn cột
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}

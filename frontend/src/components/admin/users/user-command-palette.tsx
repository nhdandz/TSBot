import * as React from "react"
import { useNavigate } from "react-router-dom"
import {
  Users,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  AlertCircle,
} from "lucide-react"

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command"

import type { User } from "@/types/user"

interface UserCommandPaletteProps {
  users: User[]
  onFilterStatus: (status: string | null) => void
  onSelectUser: (user: User) => void
}

export function UserCommandPalette({
  users,
  onFilterStatus,
  onSelectUser,
}: UserCommandPaletteProps) {
  const [open, setOpen] = React.useState(false)
  const navigate = useNavigate()

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((open) => !open)
      }
    }

    document.addEventListener("keydown", down)
    return () => document.removeEventListener("keydown", down)
  }, [])

  const runCommand = React.useCallback((command: () => void) => {
    setOpen(false)
    command()
  }, [])

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-2 px-3 py-1.5 text-sm text-gray-500 dark:text-gray-400 bg-white dark:bg-white/[0.04] border border-gray-200 dark:border-white/[0.08] rounded-lg hover:bg-gray-50 dark:hover:bg-white/[0.06] transition-colors"
      >
        <Search className="h-4 w-4" />
        <span>Tìm kiếm nhanh...</span>
        <kbd className="pointer-events-none hidden h-5 select-none items-center gap-1 rounded border border-gray-200 dark:border-white/[0.08] bg-gray-100 dark:bg-white/[0.04] px-1.5 font-mono text-[10px] font-medium text-gray-500 dark:text-gray-400 sm:flex">
          <span className="text-xs">⌘</span>K
        </kbd>
      </button>
      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput placeholder="Tìm kiếm người dùng hoặc lọc..." />
        <CommandList>
          <CommandEmpty>Không tìm thấy kết quả.</CommandEmpty>
          <CommandGroup heading="Bộ lọc nhanh">
            <CommandItem
              onSelect={() => runCommand(() => onFilterStatus("active"))}
            >
              <CheckCircle2 className="mr-2 h-4 w-4 text-emerald-500" />
              <span>Lọc: Đang hoạt động</span>
            </CommandItem>
            <CommandItem
              onSelect={() => runCommand(() => onFilterStatus("inactive"))}
            >
              <XCircle className="mr-2 h-4 w-4 text-gray-500" />
              <span>Lọc: Không hoạt động</span>
            </CommandItem>
            <CommandItem
              onSelect={() => runCommand(() => onFilterStatus("suspended"))}
            >
              <AlertCircle className="mr-2 h-4 w-4 text-red-500" />
              <span>Lọc: Đã đình chỉ</span>
            </CommandItem>
            <CommandItem
              onSelect={() => runCommand(() => onFilterStatus(null))}
            >
              <Filter className="mr-2 h-4 w-4" />
              <span>Xóa tất cả bộ lọc</span>
            </CommandItem>
          </CommandGroup>
          <CommandSeparator />
          <CommandGroup heading="Người dùng">
            {users.slice(0, 10).map((user) => (
              <CommandItem
                key={user.id}
                value={`${user.username} ${user.email}`}
                onSelect={() => runCommand(() => onSelectUser(user))}
              >
                <Users className="mr-2 h-4 w-4" />
                <span className="font-medium">{user.username}</span>
                <span className="ml-2 text-gray-500 dark:text-gray-400">
                  {user.email}
                </span>
              </CommandItem>
            ))}
          </CommandGroup>
        </CommandList>
      </CommandDialog>
    </>
  )
}

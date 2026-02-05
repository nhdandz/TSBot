import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { ThemeToggle } from '@/components/ui/theme-toggle'
import {
  LayoutDashboard,
  School,
  GraduationCap,
  BarChart3,
  LogOut,
  Shield,
  Menu,
  Users,
} from 'lucide-react'
import { useState } from 'react'

const navItems = [
  {
    title: 'Dashboard',
    href: '/admin/dashboard',
    icon: LayoutDashboard,
  },
  {
    title: 'Người dùng',
    href: '/admin/users',
    icon: Users,
  },
  {
    title: 'Trường',
    href: '/admin/truong',
    icon: School,
  },
  {
    title: 'Ngành',
    href: '/admin/nganh',
    icon: GraduationCap,
  },
  {
    title: 'Điểm chuẩn',
    href: '/admin/diem-chuan',
    icon: BarChart3,
  },
]

export default function AdminLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const handleLogout = () => {
    logout()
    navigate('/admin/login')
  }

  return (
    <div className="flex h-screen bg-[#fafafa] dark:bg-[#08080c]">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-20'
        } border-r border-gray-200 dark:border-white/[0.06] bg-white/80 dark:bg-[#0c0c14]/80 backdrop-blur-2xl transition-all duration-300 flex flex-col`}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-200 dark:border-white/[0.06]">
          <div className="flex items-center justify-between">
            {sidebarOpen ? (
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-500/25">
                  <Shield className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="font-bold text-sm text-gray-900 dark:text-white">TSBot Admin</h2>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Quản trị hệ thống</p>
                </div>
              </div>
            ) : (
              <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-lg flex items-center justify-center mx-auto shadow-lg shadow-indigo-500/25">
                <Shield className="w-5 h-5 text-white" />
              </div>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className={`text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/[0.06] ${sidebarOpen ? '' : 'mx-auto mt-2'}`}
            >
              <Menu className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.href
            return (
              <Link key={item.href} to={item.href}>
                <Button
                  variant={isActive ? 'default' : 'ghost'}
                  className={`w-full justify-start gap-3 transition-all duration-200 ${
                    isActive
                      ? 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-500/25'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/[0.06] hover:text-gray-900 dark:hover:text-white'
                  } ${!sidebarOpen ? 'justify-center' : ''}`}
                >
                  <Icon className="w-5 h-5" />
                  {sidebarOpen && <span>{item.title}</span>}
                </Button>
              </Link>
            )
          })}
        </nav>

        <Separator className="bg-gray-200 dark:bg-white/[0.06]" />

        {/* User info */}
        <div className="p-4">
          {sidebarOpen ? (
            <div className="mb-3">
              <p className="text-sm font-medium text-gray-900 dark:text-white">{user?.username}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">{user?.role}</p>
            </div>
          ) : null}
          <Button
            variant="destructive"
            className="w-full gap-2 bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400 border border-red-500/20"
            onClick={handleLogout}
            size={sidebarOpen ? 'default' : 'icon'}
          >
            <LogOut className="w-4 h-4" />
            {sidebarOpen && <span>Đăng xuất</span>}
          </Button>
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top header bar */}
        <header className="h-14 border-b border-gray-200 dark:border-white/[0.06] bg-white/80 dark:bg-[#0c0c14]/80 backdrop-blur-2xl flex items-center justify-end px-6">
          <ThemeToggle />
        </header>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}

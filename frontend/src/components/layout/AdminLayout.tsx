import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import {
  LayoutDashboard,
  School,
  GraduationCap,
  BarChart3,
  LogOut,
  Shield,
  Menu,
  FileText,
} from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'

const navItems = [
  {
    title: 'Dashboard',
    href: '/admin/dashboard',
    icon: LayoutDashboard,
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
  {
    title: 'Văn bản',
    href: '/admin/documents',
    icon: FileText,
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
    <div className="flex h-screen bg-background">
      {/* Sidebar - Dark Navy */}
      <aside
        className={cn(
          'border-r border-sidebar-border bg-sidebar transition-all duration-300 ease-apple flex flex-col',
          sidebarOpen ? 'w-[260px]' : 'w-[72px]'
        )}
      >
        {/* Logo area */}
        <div className="p-4 h-16 flex items-center">
          {sidebarOpen ? (
            <div className="flex items-center gap-3 w-full">
              <div className="w-8 h-8 bg-gradient-military rounded-lg flex items-center justify-center shadow-soft-sm">
                <Shield className="w-4 h-4 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="text-sm font-semibold text-white tracking-tight">TSBot Admin</h2>
              </div>
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-1.5 rounded-lg text-sidebar-foreground hover:text-white hover:bg-sidebar-accent transition-colors"
              >
                <Menu className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3 w-full">
              <div className="w-8 h-8 bg-gradient-military rounded-lg flex items-center justify-center">
                <Shield className="w-4 h-4 text-white" />
              </div>
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-1.5 rounded-lg text-sidebar-foreground hover:text-white hover:bg-sidebar-accent transition-colors"
              >
                <Menu className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-2 space-y-0.5">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.href
            return (
              <Link key={item.href} to={item.href}>
                <div
                  className={cn(
                    'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium',
                    'transition-all duration-200 ease-apple',
                    isActive
                      ? 'bg-sidebar-accent text-white'
                      : 'text-sidebar-foreground hover:text-white hover:bg-sidebar-accent/50',
                    !sidebarOpen && 'justify-center px-0'
                  )}
                >
                  <Icon className="w-[18px] h-[18px] shrink-0" />
                  {sidebarOpen && <span>{item.title}</span>}
                </div>
              </Link>
            )
          })}
        </nav>

        {/* User section */}
        <div className="p-3 border-t border-sidebar-border">
          {sidebarOpen ? (
            <div className="flex items-center gap-3 px-2 py-1.5">
              <div className="w-7 h-7 rounded-lg bg-sidebar-accent flex items-center justify-center text-xs font-bold text-white">
                {user?.username?.[0]?.toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-white truncate">{user?.username}</p>
                <p className="text-[10px] text-sidebar-foreground capitalize">{user?.role}</p>
              </div>
              <button
                onClick={handleLogout}
                className="p-1.5 rounded-lg text-sidebar-foreground hover:text-white hover:bg-sidebar-accent transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center p-2 rounded-lg text-sidebar-foreground hover:text-white hover:bg-sidebar-accent transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          )}
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto scrollbar-thin">
        <div className="max-w-6xl mx-auto p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

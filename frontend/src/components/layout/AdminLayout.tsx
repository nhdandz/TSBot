import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
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
      {/* Sidebar */}
      <aside
        className={`${sidebarOpen ? 'w-64' : 'w-20'
          } border-r bg-card transition-all duration-300 flex flex-col`}
      >
        {/* Header */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            {sidebarOpen ? (
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-military-gradient rounded-lg flex items-center justify-center">
                  <Shield className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="font-bold text-sm">TSBot Admin</h2>
                  <p className="text-xs text-muted-foreground">Quản trị hệ thống</p>
                </div>
              </div>
            ) : (
              <div className="w-8 h-8 bg-military-gradient rounded-lg flex items-center justify-center mx-auto">
                <Shield className="w-5 h-5 text-white" />
              </div>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className={sidebarOpen ? '' : 'mx-auto mt-2'}
            >
              <Menu className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.href
            return (
              <Link key={item.href} to={item.href}>
                <Button
                  variant={isActive ? 'default' : 'ghost'}
                  className={`w-full justify-start gap-3 ${isActive ? 'bg-military-600 hover:bg-military-700' : ''
                    } ${!sidebarOpen ? 'justify-center' : ''}`}
                >
                  <Icon className="w-5 h-5" />
                  {sidebarOpen && <span>{item.title}</span>}
                </Button>
              </Link>
            )
          })}
        </nav>

        <Separator />

        {/* User info */}
        <div className="p-4">
          {sidebarOpen ? (
            <div className="mb-3">
              <p className="text-sm font-medium">{user?.username}</p>
              <p className="text-xs text-muted-foreground capitalize">{user?.role}</p>
            </div>
          ) : null}
          <Button
            variant="destructive"
            className="w-full gap-2"
            onClick={handleLogout}
            size={sidebarOpen ? 'default' : 'icon'}
          >
            <LogOut className="w-4 h-4" />
            {sidebarOpen && <span>Đăng xuất</span>}
          </Button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <div className="container mx-auto p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

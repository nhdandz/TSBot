import { Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from '@/components/ui/toaster'
import LandingPage from '@/pages/LandingPage'
import ChatPage from '@/pages/ChatPage'
import LoginPage from '@/pages/admin/LoginPage'
import DashboardPage from '@/pages/admin/DashboardPage'
import UsersPage from '@/pages/admin/UsersPage'
import TruongPage from '@/pages/admin/TruongPage'
import NganhPage from '@/pages/admin/NganhPage'
import DiemChuanPage from '@/pages/admin/DiemChuanPage'
import AdminLayout from '@/components/layout/AdminLayout'
import { useAuthStore } from '@/stores/authStore'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  if (!isAuthenticated) {
    return <Navigate to="/admin/login" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <>
      <Routes>
        {/* Public pages */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/chat" element={<ChatPage />} />

        {/* Admin routes */}
        <Route path="/admin/login" element={<LoginPage />} />
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/admin/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="truong" element={<TruongPage />} />
          <Route path="nganh" element={<NganhPage />} />
          <Route path="diem-chuan" element={<DiemChuanPage />} />
        </Route>
      </Routes>
      <Toaster />
    </>
  )
}

export default App

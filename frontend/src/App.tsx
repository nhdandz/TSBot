import { Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from '@/components/ui/toaster'
import ChatPage from '@/pages/ChatPage'
import LoginPage from '@/pages/admin/LoginPage'
import DashboardPage from '@/pages/admin/DashboardPage'
import TruongPage from '@/pages/admin/TruongPage'
import NganhPage from '@/pages/admin/NganhPage'
import DiemChuanPage from '@/pages/admin/DiemChuanPage'
import DocumentsPage from '@/pages/admin/DocumentsPage'
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
        {/* Public chat interface */}
        <Route path="/" element={<ChatPage />} />

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
          <Route path="truong" element={<TruongPage />} />
          <Route path="nganh" element={<NganhPage />} />
          <Route path="diem-chuan" element={<DiemChuanPage />} />
          <Route path="documents" element={<DocumentsPage />} />
        </Route>
      </Routes>
      <Toaster />
    </>
  )
}

export default App


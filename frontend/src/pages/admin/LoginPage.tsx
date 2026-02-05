import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ThemeToggle } from '@/components/ui/theme-toggle'
import { Shield, Loader2 } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

export default function LoginPage() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const { login, isAuthenticated, isLoading, error, clearError } = useAuthStore()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/admin/dashboard')
    }
  }, [isAuthenticated, navigate])

  useEffect(() => {
    if (error) {
      toast({
        title: 'Lỗi đăng nhập',
        description: error,
        variant: 'destructive',
      })
      clearError()
    }
  }, [error, toast, clearError])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const success = await login({ username, password })
    if (success) {
      toast({
        title: 'Đăng nhập thành công',
        description: 'Chào mừng quay trở lại!',
      })
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#fafafa] dark:bg-[#08080c] noise-bg relative">
      {/* Theme toggle - top right */}
      <div className="absolute top-6 right-6">
        <ThemeToggle />
      </div>

      {/* Ambient glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-indigo-500/20 dark:bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none" />

      {/* Card with gradient border */}
      <div className="relative z-10 p-px rounded-2xl bg-gradient-to-b from-gray-200 dark:from-white/[0.08] to-transparent">
        <Card className="w-full max-w-md bg-white dark:bg-[#0c0c14] border-0 rounded-2xl shadow-xl dark:shadow-none">
          <CardHeader className="text-center pt-8">
            <div className="mx-auto w-16 h-16 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-indigo-500/25">
              <Shield className="w-10 h-10 text-white" />
            </div>
            <CardTitle className="text-2xl font-bold text-gray-900 dark:text-white">TSBot Admin</CardTitle>
            <CardDescription className="text-gray-500 dark:text-gray-400">
              Đăng nhập vào hệ thống quản trị
            </CardDescription>
          </CardHeader>
          <CardContent className="pb-8">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username" className="text-gray-700 dark:text-gray-300">Tên đăng nhập</Label>
                <Input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Nhập tên đăng nhập"
                  required
                  disabled={isLoading}
                  className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08] focus:border-indigo-500 dark:focus:border-indigo-500 focus:ring-indigo-500/20"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password" className="text-gray-700 dark:text-gray-300">Mật khẩu</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Nhập mật khẩu"
                  required
                  disabled={isLoading}
                  className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08] focus:border-indigo-500 dark:focus:border-indigo-500 focus:ring-indigo-500/20"
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-500/25 transition-all duration-200"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Đang đăng nhập...
                  </>
                ) : (
                  'Đăng nhập'
                )}
              </Button>
            </form>
            <div className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
              <p>Chỉ dành cho quản trị viên hệ thống</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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
    <div className="min-h-screen flex items-center justify-center bg-gradient-chat p-4">
      <div className="w-full max-w-[380px] animate-fade-in-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="mx-auto w-14 h-14 bg-gradient-military rounded-2xl flex items-center justify-center shadow-soft-md mb-5">
            <Shield className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-xl font-bold tracking-tighter text-foreground">TSBot Admin</h1>
          <p className="text-sm text-muted-foreground mt-1">Đăng nhập vào hệ thống quản trị</p>
        </div>

        {/* Form Card */}
        <div className="rounded-2xl border border-border/50 bg-card shadow-soft-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="username">Tên đăng nhập</Label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Nhập tên đăng nhập"
                required
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Mật khẩu</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Nhập mật khẩu"
                required
                disabled={isLoading}
              />
            </div>
            <Button
              type="submit"
              className="w-full h-11"
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
        </div>

        <p className="text-center text-xs text-muted-foreground/60 mt-6">
          Chỉ dành cho quản trị viên hệ thống
        </p>
      </div>
    </div>
  )
}

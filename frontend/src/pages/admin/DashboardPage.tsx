import { useQuery } from '@tanstack/react-query'
import { adminService } from '@/services/adminService'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { School, GraduationCap, BarChart3, MessageSquare, TrendingUp, Users } from 'lucide-react'

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: adminService.getStats,
  })

  const statCards = [
    {
      title: 'Trường quân đội',
      value: stats?.total_schools || 0,
      icon: School,
    },
    {
      title: 'Ngành đào tạo',
      value: stats?.total_majors || 0,
      icon: GraduationCap,
    },
    {
      title: 'Điểm chuẩn',
      value: stats?.total_scores || 0,
      icon: BarChart3,
    },
    {
      title: 'Tổng cuộc trò chuyện',
      value: stats?.total_chats || 0,
      icon: MessageSquare,
    },
    {
      title: 'Trò chuyện gần đây',
      value: stats?.recent_chats || 0,
      icon: TrendingUp,
    },
    {
      title: 'Đánh giá trung bình',
      value: stats?.avg_feedback_rating ? stats.avg_feedback_rating.toFixed(1) : 'N/A',
      icon: Users,
    },
  ]

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tighter">Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Tổng quan hệ thống tư vấn tuyển sinh quân đội
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.title} className="group hover:shadow-soft-md">
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className="w-9 h-9 rounded-xl bg-muted/50 flex items-center justify-center group-hover:scale-105 transition-transform duration-300 ease-apple">
                    <Icon className="w-4 h-4 text-muted-foreground" />
                  </div>
                </div>
                <p className="text-2xl font-bold tracking-tighter">
                  {isLoading ? (
                    <span className="shimmer inline-block w-12 h-7 rounded-lg" />
                  ) : (
                    stat.value
                  )}
                </p>
                <p className="text-xs text-muted-foreground mt-1">{stat.title}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Thông tin hệ thống</CardTitle>
            <CardDescription>
              Trạng thái và cấu hình hiện tại
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { label: 'Backend API', status: 'Hoạt động' },
              { label: 'Database', status: 'Kết nối' },
              { label: 'Vector DB', status: 'Sẵn sàng' },
              { label: 'AI Model', status: 'Đang chạy' },
            ].map((item, i) => (
              <div key={item.label} className={`flex justify-between py-2 ${i < 3 ? 'border-b border-border/40' : ''}`}>
                <span className="text-sm text-muted-foreground">{item.label}</span>
                <div className="flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-success" />
                  <span className="text-sm font-medium text-foreground">{item.status}</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Hoạt động gần đây</CardTitle>
            <CardDescription>
              Các thay đổi và cập nhật mới nhất
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-muted-foreground">
              <p>Chưa có hoạt động gần đây</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Hướng dẫn sử dụng</CardTitle>
          <CardDescription>
            Quản lý dữ liệu tuyển sinh quân đội
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2.5 text-sm text-muted-foreground">
            {[
              'Sử dụng menu bên trái để điều hướng đến các trang quản lý',
              'Trang "Trường" để quản lý danh sách các trường quân đội',
              'Trang "Ngành" để quản lý danh sách các ngành đào tạo',
              'Trang "Điểm chuẩn" để quản lý điểm chuẩn tuyển sinh theo năm',
              'Dữ liệu sẽ được sử dụng bởi chatbot AI để tư vấn cho thí sinh',
            ].map((text) => (
              <li key={text} className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-olive mt-1.5 shrink-0" />
                <span>{text}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}

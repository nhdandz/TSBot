import { useEffect } from 'react'
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
      color: 'text-primary-600',
      bgColor: 'bg-primary-100',
    },
    {
      title: 'Ngành đào tạo',
      value: stats?.total_majors || 0,
      icon: GraduationCap,
      color: 'text-military-600',
      bgColor: 'bg-military-100',
    },
    {
      title: 'Điểm chuẩn',
      value: stats?.total_scores || 0,
      icon: BarChart3,
      color: 'text-warning-600',
      bgColor: 'bg-warning-100',
    },
    {
      title: 'Tổng cuộc trò chuyện',
      value: stats?.total_chats || 0,
      icon: MessageSquare,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: 'Trò chuyện gần đây',
      value: stats?.recent_chats || 0,
      icon: TrendingUp,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Đánh giá trung bình',
      value: stats?.avg_feedback_rating ? stats.avg_feedback_rating.toFixed(1) : 'N/A',
      icon: Users,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Tổng quan hệ thống tư vấn tuyển sinh quân đội
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-sm font-medium">
                  {stat.title}
                </CardTitle>
                <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                  <Icon className={`w-4 h-4 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {isLoading ? '...' : stat.value}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Thông tin hệ thống</CardTitle>
            <CardDescription>
              Trạng thái và cấu hình hiện tại
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between border-b pb-2">
              <span className="text-sm text-muted-foreground">Backend API</span>
              <span className="text-sm font-medium text-success-600">Hoạt động</span>
            </div>
            <div className="flex justify-between border-b pb-2">
              <span className="text-sm text-muted-foreground">Database</span>
              <span className="text-sm font-medium text-success-600">Kết nối</span>
            </div>
            <div className="flex justify-between border-b pb-2">
              <span className="text-sm text-muted-foreground">Vector DB</span>
              <span className="text-sm font-medium text-success-600">Sẵn sàng</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">AI Model</span>
              <span className="text-sm font-medium text-success-600">Đang chạy</span>
            </div>
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
          <ul className="list-disc list-inside space-y-2 text-sm text-muted-foreground">
            <li>Sử dụng menu bên trái để điều hướng đến các trang quản lý</li>
            <li>Trang "Trường" để quản lý danh sách các trường quân đội</li>
            <li>Trang "Ngành" để quản lý danh sách các ngành đào tạo</li>
            <li>Trang "Điểm chuẩn" để quản lý điểm chuẩn tuyển sinh theo năm</li>
            <li>Dữ liệu sẽ được sử dụng bởi chatbot AI để tư vấn cho thí sinh</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}

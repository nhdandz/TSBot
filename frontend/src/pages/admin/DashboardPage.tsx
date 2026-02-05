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
      color: 'text-indigo-600 dark:text-indigo-400',
      bgColor: 'bg-indigo-100 dark:bg-indigo-500/10',
    },
    {
      title: 'Ngành đào tạo',
      value: stats?.total_majors || 0,
      icon: GraduationCap,
      color: 'text-violet-600 dark:text-violet-400',
      bgColor: 'bg-violet-100 dark:bg-violet-500/10',
    },
    {
      title: 'Điểm chuẩn',
      value: stats?.total_scores || 0,
      icon: BarChart3,
      color: 'text-amber-600 dark:text-amber-400',
      bgColor: 'bg-amber-100 dark:bg-amber-500/10',
    },
    {
      title: 'Tổng cuộc trò chuyện',
      value: stats?.total_chats || 0,
      icon: MessageSquare,
      color: 'text-purple-600 dark:text-purple-400',
      bgColor: 'bg-purple-100 dark:bg-purple-500/10',
    },
    {
      title: 'Trò chuyện gần đây',
      value: stats?.recent_chats || 0,
      icon: TrendingUp,
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-100 dark:bg-blue-500/10',
    },
    {
      title: 'Đánh giá trung bình',
      value: stats?.avg_feedback_rating ? stats.avg_feedback_rating.toFixed(1) : 'N/A',
      icon: Users,
      color: 'text-emerald-600 dark:text-emerald-400',
      bgColor: 'bg-emerald-100 dark:bg-emerald-500/10',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Tổng quan hệ thống tư vấn tuyển sinh quân đội
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.title} className="bg-white dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.06]">
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  {stat.title}
                </CardTitle>
                <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                  <Icon className={`w-4 h-4 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {isLoading ? '...' : stat.value}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.06]">
          <CardHeader>
            <CardTitle className="text-gray-900 dark:text-white">Thông tin hệ thống</CardTitle>
            <CardDescription className="text-gray-500 dark:text-gray-400">
              Trạng thái và cấu hình hiện tại
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between border-b border-gray-200 dark:border-white/[0.06] pb-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">Backend API</span>
              <span className="text-sm font-medium text-emerald-600 dark:text-emerald-400">Hoạt động</span>
            </div>
            <div className="flex justify-between border-b border-gray-200 dark:border-white/[0.06] pb-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">Database</span>
              <span className="text-sm font-medium text-emerald-600 dark:text-emerald-400">Kết nối</span>
            </div>
            <div className="flex justify-between border-b border-gray-200 dark:border-white/[0.06] pb-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">Vector DB</span>
              <span className="text-sm font-medium text-emerald-600 dark:text-emerald-400">Sẵn sàng</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500 dark:text-gray-400">AI Model</span>
              <span className="text-sm font-medium text-emerald-600 dark:text-emerald-400">Đang chạy</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.06]">
          <CardHeader>
            <CardTitle className="text-gray-900 dark:text-white">Hoạt động gần đây</CardTitle>
            <CardDescription className="text-gray-500 dark:text-gray-400">
              Các thay đổi và cập nhật mới nhất
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              <p>Chưa có hoạt động gần đây</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-white dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.06]">
        <CardHeader>
          <CardTitle className="text-gray-900 dark:text-white">Hướng dẫn sử dụng</CardTitle>
          <CardDescription className="text-gray-500 dark:text-gray-400">
            Quản lý dữ liệu tuyển sinh quân đội
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="list-disc list-inside space-y-2 text-sm text-gray-500 dark:text-gray-400">
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

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminService } from '@/services/adminService'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Plus, Trash2, Loader2 } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import type { DiemChuan } from '@/types'

export default function DiemChuanPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingScore, setEditingScore] = useState<any>(null)

  const [filters, setFilters] = useState({
    year: new Date().getFullYear(),
    school_id: '',
    major_code: '',
  })

  const [formData, setFormData] = useState<Omit<DiemChuan, 'id'>>({
    school_id: '',
    major_code: '',
    block_code: '',
    year: new Date().getFullYear(),
    gender: 'CHUNG',
    region: 'TOAN_QUOC',
    score: 0,
    tieu_chi_phu: '',
    ghi_chu: '',
  })

  // Fetch data
  const { data: scores, isLoading } = useQuery({
    queryKey: ['diem-chuan', filters],
    queryFn: () => adminService.getDiemChuan(filters),
  })

  const { data: schools } = useQuery({
    queryKey: ['truong'],
    queryFn: adminService.getTruong,
  })

  const { data: majors } = useQuery({
    queryKey: ['nganh'],
    queryFn: adminService.getNganh,
  })

  const createMutation = useMutation({
    mutationFn: adminService.createDiemChuan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['diem-chuan'] })
      toast({ title: 'Thành công', description: 'Đã thêm điểm chuẩn mới' })
      setIsDialogOpen(false)
      resetForm()
    },
    onError: (error: any) => {
      toast({ title: 'Lỗi', description: error.detail || 'Không thể thêm điểm chuẩn', variant: 'destructive' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: adminService.deleteDiemChuan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['diem-chuan'] })
      toast({ title: 'Thành công', description: 'Đã xóa điểm chuẩn' })
    },
  })

  const resetForm = () => {
    setFormData({
      school_id: '',
      major_code: '',
      block_code: '',
      year: new Date().getFullYear(),
      gender: 'CHUNG',
      region: 'TOAN_QUOC',
      score: 0,
      tieu_chi_phu: '',
      ghi_chu: '',
    })
    setEditingScore(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate(formData)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Quản lý Điểm chuẩn</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Điểm chuẩn tuyển sinh các trường quân đội</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-500/25" onClick={resetForm}>
                <Plus className="w-4 h-4 mr-2" />
                Thêm điểm chuẩn
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl bg-white dark:bg-[#0c0c14] border-gray-200 dark:border-white/[0.08]">
              <DialogHeader>
                <DialogTitle className="text-gray-900 dark:text-white">Thêm điểm chuẩn mới</DialogTitle>
                <DialogDescription className="text-gray-500 dark:text-gray-400">Nhập thông tin điểm chuẩn tuyển sinh</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-gray-700 dark:text-gray-300">Trường *</Label>
                    <Select
                      value={formData.school_id}
                      onValueChange={(value) => setFormData({ ...formData, school_id: value, major_code: '' })}
                    >
                      <SelectTrigger className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]">
                        <SelectValue placeholder="Chọn trường" />
                      </SelectTrigger>
                      <SelectContent className="bg-white dark:bg-[#0c0c14] border-gray-200 dark:border-white/[0.08]">
                        {schools?.map((school) => (
                          <SelectItem key={`form-school-${school.id}`} value={school.school_id || `school-${school.id}`}>
                            {school.school_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-gray-700 dark:text-gray-300">Ngành *</Label>
                    <Select
                      value={formData.major_code}
                      onValueChange={(value) => setFormData({ ...formData, major_code: value })}
                    >
                      <SelectTrigger className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]">
                        <SelectValue placeholder="Chọn ngành" />
                      </SelectTrigger>
                      <SelectContent className="bg-white dark:bg-[#0c0c14] border-gray-200 dark:border-white/[0.08]">
                        {majors?.filter(m => !formData.school_id || m.school_name?.includes(formData.school_id)).map((major) => (
                          <SelectItem key={`form-${major.truong_id}-${major.major_code}`} value={major.id?.toString() || major.major_code}>
                            {major.school_name} - {major.major_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-gray-700 dark:text-gray-300">Khối thi *</Label>
                    <Select
                      value={formData.block_code}
                      onValueChange={(value) => setFormData({ ...formData, block_code: value })}
                    >
                      <SelectTrigger className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]">
                        <SelectValue placeholder="Chọn khối" />
                      </SelectTrigger>
                      <SelectContent className="bg-white dark:bg-[#0c0c14] border-gray-200 dark:border-white/[0.08]">
                        <SelectItem value="A00">A00 (Toán, Lý, Hóa)</SelectItem>
                        <SelectItem value="A01">A01 (Toán, Lý, Anh)</SelectItem>
                        <SelectItem value="D01">D01 (Toán, Văn, Anh)</SelectItem>
                        <SelectItem value="D07">D07 (Toán, Hóa, Anh)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-gray-700 dark:text-gray-300">Năm *</Label>
                    <Input
                      type="number"
                      value={formData.year}
                      onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) })}
                      min="2020"
                      max="2030"
                      required
                      className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label className="text-gray-700 dark:text-gray-300">Giới tính</Label>
                    <Select
                      value={formData.gender}
                      onValueChange={(value: any) => setFormData({ ...formData, gender: value })}
                    >
                      <SelectTrigger className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-white dark:bg-[#0c0c14] border-gray-200 dark:border-white/[0.08]">
                        <SelectItem value="NAM">Nam</SelectItem>
                        <SelectItem value="NU">Nữ</SelectItem>
                        <SelectItem value="CHUNG">Chung</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-gray-700 dark:text-gray-300">Khu vực</Label>
                    <Select
                      value={formData.region}
                      onValueChange={(value: any) => setFormData({ ...formData, region: value })}
                    >
                      <SelectTrigger className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-white dark:bg-[#0c0c14] border-gray-200 dark:border-white/[0.08]">
                        <SelectItem value="MIEN_BAC">Miền Bắc</SelectItem>
                        <SelectItem value="MIEN_NAM">Miền Nam</SelectItem>
                        <SelectItem value="TOAN_QUOC">Toàn quốc</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-gray-700 dark:text-gray-300">Điểm chuẩn *</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.score}
                      onChange={(e) => setFormData({ ...formData, score: parseFloat(e.target.value) })}
                      placeholder="VD: 25.5"
                      required
                      className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label className="text-gray-700 dark:text-gray-300">Tiêu chí phụ</Label>
                    <Input
                      value={formData.tieu_chi_phu || ''}
                      onChange={(e) => setFormData({ ...formData, tieu_chi_phu: e.target.value })}
                      placeholder="VD: Điểm toán >= 8"
                      className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-gray-700 dark:text-gray-300">Ghi chú</Label>
                  <Input
                    value={formData.ghi_chu || ''}
                    onChange={(e) => setFormData({ ...formData, ghi_chu: e.target.value })}
                    placeholder="Ghi chú thêm"
                    className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]"
                  />
                </div>

                <div className="flex gap-2 justify-end">
                  <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)} className="border-gray-200 dark:border-white/[0.08] text-gray-700 dark:text-gray-300">
                    Hủy
                  </Button>
                  <Button type="submit" className="bg-indigo-600 hover:bg-indigo-700 text-white" disabled={createMutation.isPending}>
                    {createMutation.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                    Thêm
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Filters */}
      <Card className="bg-white dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.06]">
        <CardHeader>
          <CardTitle className="text-gray-900 dark:text-white">Bộ lọc</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label className="text-gray-700 dark:text-gray-300">Năm</Label>
              <Input
                type="number"
                value={filters.year}
                onChange={(e) => setFilters({ ...filters, year: parseInt(e.target.value) })}
                className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-gray-700 dark:text-gray-300">Trường</Label>
              <Select value={filters.school_id || "all"} onValueChange={(value) => setFilters({ ...filters, school_id: value === "all" ? "" : value })}>
                <SelectTrigger className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]">
                  <SelectValue placeholder="Tất cả" />
                </SelectTrigger>
                <SelectContent className="bg-white dark:bg-[#0c0c14] border-gray-200 dark:border-white/[0.08]">
                  <SelectItem value="all">Tất cả</SelectItem>
                  {schools?.map((school) => (
                    <SelectItem key={`filter-${school.id}`} value={school.id?.toString() || ""}>
                      {school.school_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-gray-700 dark:text-gray-300">Ngành</Label>
              <Select value={filters.major_code || "all"} onValueChange={(value) => setFilters({ ...filters, major_code: value === "all" ? "" : value })}>
                <SelectTrigger className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]">
                  <SelectValue placeholder="Tất cả" />
                </SelectTrigger>
                <SelectContent className="bg-white dark:bg-[#0c0c14] border-gray-200 dark:border-white/[0.08]">
                  <SelectItem value="all">Tất cả</SelectItem>
                  {majors?.map((major) => (
                    <SelectItem key={`${major.truong_id}-${major.major_code}`} value={major.id?.toString() || `${major.truong_id}-${major.major_code}`}>
                      {major.school_name} - {major.major_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Data Table */}
      <Card className="bg-white dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.06]">
        <CardHeader>
          <CardTitle className="text-gray-900 dark:text-white">Danh sách điểm chuẩn ({scores?.total || 0})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center p-8">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : scores?.items && scores.items.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-gray-200 dark:border-white/[0.06]">
                    <TableHead className="text-gray-600 dark:text-gray-400">Năm</TableHead>
                    <TableHead className="text-gray-600 dark:text-gray-400">Trường</TableHead>
                    <TableHead className="text-gray-600 dark:text-gray-400">Ngành</TableHead>
                    <TableHead className="text-gray-600 dark:text-gray-400">Khối</TableHead>
                    <TableHead className="text-gray-600 dark:text-gray-400">Giới tính</TableHead>
                    <TableHead className="text-gray-600 dark:text-gray-400">Khu vực</TableHead>
                    <TableHead className="text-right text-gray-600 dark:text-gray-400">Điểm</TableHead>
                    <TableHead className="text-right text-gray-600 dark:text-gray-400">Thao tác</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {scores.items.map((score: any) => (
                    <TableRow key={score.id} className="border-gray-200 dark:border-white/[0.06]">
                      <TableCell className="text-gray-900 dark:text-white">{score.nam}</TableCell>
                      <TableCell className="font-medium text-gray-900 dark:text-white">{score.truong?.ten_truong}</TableCell>
                      <TableCell className="text-gray-900 dark:text-white">{score.nganh?.ten_nganh}</TableCell>
                      <TableCell className="font-mono text-gray-900 dark:text-white">{score.khoi_thi?.ma_khoi}</TableCell>
                      <TableCell className="text-gray-600 dark:text-gray-400">{score.gioi_tinh || '-'}</TableCell>
                      <TableCell className="text-gray-600 dark:text-gray-400">{score.khu_vuc || '-'}</TableCell>
                      <TableCell className="text-right font-bold text-indigo-600 dark:text-indigo-400">
                        {score.diem_chuan}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="destructive"
                          size="icon"
                          onClick={() => {
                            if (confirm('Xóa điểm chuẩn này?')) {
                              deleteMutation.mutate(score.id)
                            }
                          }}
                          className="bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400 border border-red-500/20"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="text-center p-8 text-gray-500 dark:text-gray-400">
              Không tìm thấy dữ liệu với bộ lọc hiện tại
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

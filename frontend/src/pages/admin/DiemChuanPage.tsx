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
import { Plus, Pencil, Trash2, Loader2, Upload, Download } from 'lucide-react'
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
          <h1 className="text-3xl font-bold">Quản lý Điểm chuẩn</h1>
          <p className="text-muted-foreground mt-1">Điểm chuẩn tuyển sinh các trường quân đội</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-military-600 hover:bg-military-700" onClick={resetForm}>
                <Plus className="w-4 h-4 mr-2" />
                Thêm điểm chuẩn
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Thêm điểm chuẩn mới</DialogTitle>
                <DialogDescription>Nhập thông tin điểm chuẩn tuyển sinh</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Trường *</Label>
                    <Select
                      value={formData.school_id}
                      onValueChange={(value) => setFormData({ ...formData, school_id: value, major_code: '' })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Chọn trường" />
                      </SelectTrigger>
                      <SelectContent>
                        {schools?.map((school) => (
                          <SelectItem key={`form-school-${school.id}`} value={school.school_id || `school-${school.id}`}>
                            {school.school_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Ngành *</Label>
                    <Select
                      value={formData.major_code}
                      onValueChange={(value) => setFormData({ ...formData, major_code: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Chọn ngành" />
                      </SelectTrigger>
                      <SelectContent>
                        {majors?.filter(m => !formData.school_id || m.school_name?.includes(formData.school_id)).map((major) => (
                          <SelectItem key={`form-${major.truong_id}-${major.major_code}`} value={major.id?.toString() || major.major_code}>
                            {major.school_name} - {major.major_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Khối thi *</Label>
                    <Select
                      value={formData.block_code}
                      onValueChange={(value) => setFormData({ ...formData, block_code: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Chọn khối" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="A00">A00 (Toán, Lý, Hóa)</SelectItem>
                        <SelectItem value="A01">A01 (Toán, Lý, Anh)</SelectItem>
                        <SelectItem value="D01">D01 (Toán, Văn, Anh)</SelectItem>
                        <SelectItem value="D07">D07 (Toán, Hóa, Anh)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Năm *</Label>
                    <Input
                      type="number"
                      value={formData.year}
                      onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) })}
                      min="2020"
                      max="2030"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Giới tính</Label>
                    <Select
                      value={formData.gender}
                      onValueChange={(value: any) => setFormData({ ...formData, gender: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="NAM">Nam</SelectItem>
                        <SelectItem value="NU">Nữ</SelectItem>
                        <SelectItem value="CHUNG">Chung</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Khu vực</Label>
                    <Select
                      value={formData.region}
                      onValueChange={(value: any) => setFormData({ ...formData, region: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="MIEN_BAC">Miền Bắc</SelectItem>
                        <SelectItem value="MIEN_NAM">Miền Nam</SelectItem>
                        <SelectItem value="TOAN_QUOC">Toàn quốc</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Điểm chuẩn *</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.score}
                      onChange={(e) => setFormData({ ...formData, score: parseFloat(e.target.value) })}
                      placeholder="VD: 25.5"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Tiêu chí phụ</Label>
                    <Input
                      value={formData.tieu_chi_phu || ''}
                      onChange={(e) => setFormData({ ...formData, tieu_chi_phu: e.target.value })}
                      placeholder="VD: Điểm toán >= 8"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Ghi chú</Label>
                  <Input
                    value={formData.ghi_chu || ''}
                    onChange={(e) => setFormData({ ...formData, ghi_chu: e.target.value })}
                    placeholder="Ghi chú thêm"
                  />
                </div>

                <div className="flex gap-2 justify-end">
                  <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                    Hủy
                  </Button>
                  <Button type="submit" className="bg-military-600 hover:bg-military-700" disabled={createMutation.isPending}>
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
      <Card>
        <CardHeader>
          <CardTitle>Bộ lọc</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Năm</Label>
              <Input
                type="number"
                value={filters.year}
                onChange={(e) => setFilters({ ...filters, year: parseInt(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label>Trường</Label>
              <Select value={filters.school_id || "all"} onValueChange={(value) => setFilters({ ...filters, school_id: value === "all" ? "" : value })}>
                <SelectTrigger>
                  <SelectValue placeholder="Tất cả" />
                </SelectTrigger>
                <SelectContent>
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
              <Label>Ngành</Label>
              <Select value={filters.major_code || "all"} onValueChange={(value) => setFilters({ ...filters, major_code: value === "all" ? "" : value })}>
                <SelectTrigger>
                  <SelectValue placeholder="Tất cả" />
                </SelectTrigger>
                <SelectContent>
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
      <Card>
        <CardHeader>
          <CardTitle>Danh sách điểm chuẩn ({scores?.total || 0})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center p-8">
              <Loader2 className="w-8 h-8 animate-spin text-military-600" />
            </div>
          ) : scores?.items && scores.items.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Năm</TableHead>
                    <TableHead>Trường</TableHead>
                    <TableHead>Ngành</TableHead>
                    <TableHead>Khối</TableHead>
                    <TableHead>Giới tính</TableHead>
                    <TableHead>Khu vực</TableHead>
                    <TableHead className="text-right">Điểm</TableHead>
                    <TableHead className="text-right">Thao tác</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {scores.items.map((score: any) => (
                    <TableRow key={score.id}>
                      <TableCell>{score.nam}</TableCell>
                      <TableCell className="font-medium">{score.truong?.ten_truong}</TableCell>
                      <TableCell>{score.nganh?.ten_nganh}</TableCell>
                      <TableCell className="font-mono">{score.khoi_thi?.ma_khoi}</TableCell>
                      <TableCell>{score.gioi_tinh || '-'}</TableCell>
                      <TableCell>{score.khu_vuc || '-'}</TableCell>
                      <TableCell className="text-right font-bold text-military-600">
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
            <div className="text-center p-8 text-muted-foreground">
              Không tìm thấy dữ liệu với bộ lọc hiện tại
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

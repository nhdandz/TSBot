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

interface DiemChuanFormData {
  truong_id: number | null
  nganh_id: number | null
  khoi_thi_id: number | null
  nam: number
  diem_chuan: number
  gioi_tinh: string | null
  khu_vuc: string | null
  chi_tieu: number | null
  ghi_chu: string
}

export default function DiemChuanPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingScore, setEditingScore] = useState<any>(null)

  const [filters, setFilters] = useState<{
    year: number | null
    school_id: string
  }>({
    year: null, // null = tất cả các năm
    school_id: '',
  })

  const [formData, setFormData] = useState<DiemChuanFormData>({
    truong_id: null,
    nganh_id: null,
    khoi_thi_id: null,
    nam: new Date().getFullYear(),
    diem_chuan: 0,
    gioi_tinh: null,
    khu_vuc: null,
    chi_tieu: null,
    ghi_chu: '',
  })

  // Fetch schools
  const { data: schools } = useQuery({
    queryKey: ['truong'],
    queryFn: adminService.getTruong,
  })

  // Fetch all majors initially (for filter dropdown)
  const { data: allMajors } = useQuery({
    queryKey: ['nganh'],
    queryFn: () => adminService.getNganh(),
  })

  // Fetch majors filtered by selected school in the form
  const { data: filteredMajors } = useQuery({
    queryKey: ['nganh', formData.truong_id],
    queryFn: () => adminService.getNganh(formData.truong_id || undefined),
    enabled: !!formData.truong_id,
  })

  // Fetch exam blocks
  const { data: khoiThiList } = useQuery({
    queryKey: ['khoi-thi'],
    queryFn: adminService.getKhoiThi,
  })

  // Fetch scores with filters
  const { data: scores, isLoading } = useQuery({
    queryKey: ['diem-chuan', filters],
    queryFn: () => adminService.getDiemChuan(filters),
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => adminService.createDiemChuan(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['diem-chuan'] })
      toast({ title: 'Thành công', description: 'Đã thêm điểm chuẩn mới' })
      setIsDialogOpen(false)
      resetForm()
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || error?.detail || error?.message || 'Không thể thêm điểm chuẩn'
      toast({ title: 'Lỗi', description: errorMsg, variant: 'destructive' })
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
      truong_id: null,
      nganh_id: null,
      khoi_thi_id: null,
      nam: new Date().getFullYear(),
      diem_chuan: 0,
      gioi_tinh: null,
      khu_vuc: null,
      chi_tieu: null,
      ghi_chu: '',
    })
    setEditingScore(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.nganh_id || !formData.khoi_thi_id) {
      toast({ title: 'Lỗi', description: 'Vui lòng chọn ngành và khối thi', variant: 'destructive' })
      return
    }

    // Prepare data for API - only include non-null values
    const apiData: any = {
      nganh_id: formData.nganh_id,
      khoi_thi_id: formData.khoi_thi_id,
      nam: formData.nam,
      diem_chuan: formData.diem_chuan,
    }

    if (formData.gioi_tinh) {
      apiData.gioi_tinh = formData.gioi_tinh
    }
    if (formData.khu_vuc) {
      apiData.khu_vuc = formData.khu_vuc
    }
    if (formData.chi_tieu) {
      apiData.chi_tieu = formData.chi_tieu
    }
    if (formData.ghi_chu) {
      apiData.ghi_chu = formData.ghi_chu
    }

    createMutation.mutate(apiData)
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
                      value={formData.truong_id?.toString() || ''}
                      onValueChange={(value) => setFormData({ ...formData, truong_id: parseInt(value), nganh_id: null })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Chọn trường" />
                      </SelectTrigger>
                      <SelectContent>
                        {schools?.map((school) => (
                          <SelectItem key={`form-school-${school.id}`} value={school.id?.toString() || ''}>
                            {school.school_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Ngành *</Label>
                    <Select
                      value={formData.nganh_id?.toString() || ''}
                      onValueChange={(value) => setFormData({ ...formData, nganh_id: parseInt(value) })}
                      disabled={!formData.truong_id}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder={formData.truong_id ? "Chọn ngành" : "Chọn trường trước"} />
                      </SelectTrigger>
                      <SelectContent>
                        {filteredMajors?.map((major) => (
                          <SelectItem key={`form-major-${major.id}`} value={major.id?.toString() || ''}>
                            {major.major_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Khối thi *</Label>
                    <Select
                      value={formData.khoi_thi_id?.toString() || ''}
                      onValueChange={(value) => setFormData({ ...formData, khoi_thi_id: parseInt(value) })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Chọn khối" />
                      </SelectTrigger>
                      <SelectContent>
                        {khoiThiList?.map((khoi) => (
                          <SelectItem key={`form-khoi-${khoi.id}`} value={khoi.id.toString()}>
                            {khoi.ma_khoi} ({khoi.mon_hoc})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Năm *</Label>
                    <Input
                      type="number"
                      value={formData.nam}
                      onChange={(e) => setFormData({ ...formData, nam: parseInt(e.target.value) })}
                      min="2020"
                      max="2030"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Giới tính</Label>
                    <Select
                      value={formData.gioi_tinh || 'none'}
                      onValueChange={(value) => setFormData({ ...formData, gioi_tinh: value === 'none' ? null : value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Không phân biệt</SelectItem>
                        <SelectItem value="nam">Nam</SelectItem>
                        <SelectItem value="nu">Nữ</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Khu vực</Label>
                    <Select
                      value={formData.khu_vuc || 'none'}
                      onValueChange={(value) => setFormData({ ...formData, khu_vuc: value === 'none' ? null : value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Không phân biệt</SelectItem>
                        <SelectItem value="KV1">KV1</SelectItem>
                        <SelectItem value="KV2">KV2</SelectItem>
                        <SelectItem value="KV2-NT">KV2-NT</SelectItem>
                        <SelectItem value="KV3">KV3</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Điểm chuẩn *</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.diem_chuan}
                      onChange={(e) => setFormData({ ...formData, diem_chuan: parseFloat(e.target.value) || 0 })}
                      placeholder="VD: 25.5"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Chỉ tiêu</Label>
                    <Input
                      type="number"
                      value={formData.chi_tieu || ''}
                      onChange={(e) => setFormData({ ...formData, chi_tieu: e.target.value ? parseInt(e.target.value) : null })}
                      placeholder="Số lượng tuyển"
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Năm</Label>
              <Select
                value={filters.year?.toString() || "all"}
                onValueChange={(value) => setFilters({ ...filters, year: value === "all" ? null : parseInt(value) })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Tất cả các năm" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả các năm</SelectItem>
                  {/* Generate years from current year back to 2020 */}
                  {Array.from({ length: new Date().getFullYear() - 2019 }, (_, i) => new Date().getFullYear() - i).map((year) => (
                    <SelectItem key={`year-${year}`} value={year.toString()}>
                      {year}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
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

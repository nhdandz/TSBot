import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminService } from '@/services/adminService'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Plus, Trash2, Loader2 } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

interface DiemChuanFormData {
  truong_id: number | null
  nganh_id: number | null
  khoi_thi_ids: number[]
  nam: number
  diem_chuan: number
  gioi_tinh: string | null
  khu_vuc: string | null
  chi_tieu: number | null
  ghi_chu: string
}

const KHU_VUC_LABEL: Record<string, string> = {
  mien_bac: 'Miền Bắc',
  mien_nam: 'Miền Nam',
}

export default function DiemChuanPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingScore, setEditingScore] = useState<any>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [filters, setFilters] = useState<{
    year: number | null
    school_id: string
  }>({
    year: null,
    school_id: '',
  })

  const [formData, setFormData] = useState<DiemChuanFormData>({
    truong_id: null,
    nganh_id: null,
    khoi_thi_ids: [],
    nam: new Date().getFullYear(),
    diem_chuan: 0,
    gioi_tinh: null,
    khu_vuc: null,
    chi_tieu: null,
    ghi_chu: '',
  })

  const { data: schools } = useQuery({
    queryKey: ['truong'],
    queryFn: adminService.getTruong,
  })

  const { data: filteredMajors } = useQuery({
    queryKey: ['nganh', formData.truong_id],
    queryFn: () => adminService.getNganh(formData.truong_id || undefined),
    enabled: !!formData.truong_id,
  })

  const { data: khoiThiList } = useQuery({
    queryKey: ['khoi-thi'],
    queryFn: adminService.getKhoiThi,
  })

  const { data: scores, isLoading } = useQuery({
    queryKey: ['diem-chuan', filters],
    queryFn: () => adminService.getDiemChuan(filters),
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => adminService.createDiemChuan(data),
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
      khoi_thi_ids: [],
      nam: new Date().getFullYear(),
      diem_chuan: 0,
      gioi_tinh: null,
      khu_vuc: null,
      chi_tieu: null,
      ghi_chu: '',
    })
    setEditingScore(null)
  }

  const toggleKhoiThi = (id: number, checked: boolean) => {
    setFormData((prev) => ({
      ...prev,
      khoi_thi_ids: checked
        ? [...prev.khoi_thi_ids, id]
        : prev.khoi_thi_ids.filter((k) => k !== id),
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.nganh_id || formData.khoi_thi_ids.length === 0) {
      toast({ title: 'Lỗi', description: 'Vui lòng chọn ngành và ít nhất 1 khối thi', variant: 'destructive' })
      return
    }

    const baseData: any = {
      nganh_id: formData.nganh_id,
      nam: formData.nam,
      diem_chuan: formData.diem_chuan,
    }
    if (formData.gioi_tinh) baseData.gioi_tinh = formData.gioi_tinh
    if (formData.khu_vuc) baseData.khu_vuc = formData.khu_vuc
    if (formData.chi_tieu) baseData.chi_tieu = formData.chi_tieu
    if (formData.ghi_chu) baseData.ghi_chu = formData.ghi_chu

    setIsSubmitting(true)
    try {
      await Promise.all(
        formData.khoi_thi_ids.map((khoi_id) =>
          createMutation.mutateAsync({ ...baseData, khoi_thi_id: khoi_id }),
        ),
      )
      queryClient.invalidateQueries({ queryKey: ['diem-chuan'] })
      toast({
        title: 'Thành công',
        description: `Đã thêm ${formData.khoi_thi_ids.length} điểm chuẩn`,
      })
      setIsDialogOpen(false)
      resetForm()
    } catch {
      // lỗi đã được xử lý trong onError của mutation
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tighter">Quản lý Điểm chuẩn</h1>
          <p className="text-sm text-muted-foreground mt-1">Điểm chuẩn tuyển sinh các trường quân đội</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={resetForm}>
              <Plus className="w-4 h-4" />
              Thêm điểm chuẩn
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Thêm điểm chuẩn mới</DialogTitle>
              <DialogDescription>Nhập thông tin điểm chuẩn tuyển sinh</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-5">
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
                      <SelectValue placeholder={formData.truong_id ? 'Chọn ngành' : 'Chọn trường trước'} />
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
                      <SelectItem value="mien_bac">Miền Bắc</SelectItem>
                      <SelectItem value="mien_nam">Miền Nam</SelectItem>
                    </SelectContent>
                  </Select>
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

              <div className="space-y-2">
                <Label>Khối thi * <span className="text-muted-foreground font-normal">(chọn nhiều khối có cùng mức điểm)</span></Label>
                <div className="border rounded-md p-3 max-h-44 overflow-y-auto space-y-2 bg-muted/30">
                  {khoiThiList && khoiThiList.length > 0 ? (
                    khoiThiList.map((khoi) => (
                      <div key={`khoi-${khoi.id}`} className="flex items-center gap-2.5">
                        <Checkbox
                          id={`khoi-${khoi.id}`}
                          checked={formData.khoi_thi_ids.includes(khoi.id)}
                          onCheckedChange={(checked) => toggleKhoiThi(khoi.id, checked)}
                        />
                        <label
                          htmlFor={`khoi-${khoi.id}`}
                          className="text-sm cursor-pointer leading-none select-none"
                        >
                          <span className="font-mono font-medium">{khoi.ma_khoi}</span>
                          <span className="text-muted-foreground ml-1">({khoi.mon_hoc})</span>
                        </label>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">Đang tải...</p>
                  )}
                </div>
                {formData.khoi_thi_ids.length > 0 && (
                  <p className="text-xs text-muted-foreground">
                    Đã chọn {formData.khoi_thi_ids.length} khối → sẽ tạo {formData.khoi_thi_ids.length} bản ghi
                  </p>
                )}
              </div>

              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>Hủy</Button>
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                  Thêm
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-base">Bộ lọc</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Năm</Label>
              <Select
                value={filters.year?.toString() || 'all'}
                onValueChange={(value) => setFilters({ ...filters, year: value === 'all' ? null : parseInt(value) })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Tất cả các năm" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả các năm</SelectItem>
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
              <Select value={filters.school_id || 'all'} onValueChange={(value) => setFilters({ ...filters, school_id: value === 'all' ? '' : value })}>
                <SelectTrigger>
                  <SelectValue placeholder="Tất cả" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả</SelectItem>
                  {schools?.map((school) => (
                    <SelectItem key={`filter-${school.id}`} value={school.id?.toString() || ''}>
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
        <CardHeader className="pb-4">
          <CardTitle className="text-base">Danh sách ({scores?.total || 0})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex justify-center p-8">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : scores?.items && scores.items.length > 0 ? (
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
                    <TableCell className="font-mono text-xs">{score.nam}</TableCell>
                    <TableCell className="font-medium">{score.truong?.ten_truong}</TableCell>
                    <TableCell>{score.nganh?.ten_nganh}</TableCell>
                    <TableCell className="font-mono text-xs">{score.khoi_thi?.ma_khoi}</TableCell>
                    <TableCell className="text-muted-foreground">{score.gioi_tinh || '-'}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {KHU_VUC_LABEL[score.khu_vuc] ?? '-'}
                    </TableCell>
                    <TableCell className="text-right font-bold text-primary">
                      {score.diem_chuan}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 rounded-lg text-destructive hover:text-destructive hover:bg-destructive/10"
                        onClick={() => {
                          if (confirm('Xóa điểm chuẩn này?')) {
                            deleteMutation.mutate(score.id)
                          }
                        }}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center p-8 text-sm text-muted-foreground">
              Không tìm thấy dữ liệu với bộ lọc hiện tại
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

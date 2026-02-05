import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminService } from '@/services/adminService'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Plus, Pencil, Trash2, Loader2 } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import type { Nganh } from '@/types'

export default function NganhPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingMajor, setEditingMajor] = useState<Nganh | null>(null)
  const [formData, setFormData] = useState({
    major_code: '',
    major_name: '',
    description: '',
  })

  const { data: majors, isLoading } = useQuery({
    queryKey: ['nganh'],
    queryFn: adminService.getNganh,
  })

  const createMutation = useMutation({
    mutationFn: adminService.createNganh,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nganh'] })
      toast({ title: 'Thành công', description: 'Đã thêm ngành mới' })
      setIsDialogOpen(false)
      resetForm()
    },
    onError: (error: any) => {
      toast({ title: 'Lỗi', description: error.detail || 'Không thể thêm ngành', variant: 'destructive' })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ majorCode, data }: { majorCode: string; data: Partial<Nganh> }) =>
      adminService.updateNganh(majorCode, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nganh'] })
      toast({ title: 'Thành công', description: 'Đã cập nhật ngành' })
      setIsDialogOpen(false)
      resetForm()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: adminService.deleteNganh,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nganh'] })
      toast({ title: 'Thành công', description: 'Đã xóa ngành' })
    },
  })

  const resetForm = () => {
    setFormData({ major_code: '', major_name: '', description: '' })
    setEditingMajor(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (editingMajor) {
      updateMutation.mutate({ majorCode: editingMajor.major_code, data: formData })
    } else {
      createMutation.mutate(formData)
    }
  }

  const handleEdit = (major: Nganh) => {
    setEditingMajor(major)
    setFormData({
      major_code: major.major_code,
      major_name: major.major_name,
      description: major.description || '',
    })
    setIsDialogOpen(true)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Quản lý Ngành</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Danh sách các ngành đào tạo</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-500/25" onClick={resetForm}>
              <Plus className="w-4 h-4 mr-2" />
              Thêm ngành
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-white dark:bg-[#0c0c14] border-gray-200 dark:border-white/[0.08]">
            <DialogHeader>
              <DialogTitle className="text-gray-900 dark:text-white">{editingMajor ? 'Chỉnh sửa ngành' : 'Thêm ngành mới'}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label className="text-gray-700 dark:text-gray-300">Mã ngành *</Label>
                <Input
                  value={formData.major_code}
                  onChange={(e) => setFormData({ ...formData, major_code: e.target.value })}
                  placeholder="VD: CNTT"
                  required
                  disabled={!!editingMajor}
                  className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-gray-700 dark:text-gray-300">Tên ngành *</Label>
                <Input
                  value={formData.major_name}
                  onChange={(e) => setFormData({ ...formData, major_name: e.target.value })}
                  placeholder="VD: Công nghệ thông tin"
                  required
                  className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-gray-700 dark:text-gray-300">Mô tả</Label>
                <Input
                  value={formData.description || ''}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Mô tả ngành học"
                  className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)} className="border-gray-200 dark:border-white/[0.08] text-gray-700 dark:text-gray-300">Hủy</Button>
                <Button type="submit" className="bg-indigo-600 hover:bg-indigo-700 text-white">
                  {editingMajor ? 'Cập nhật' : 'Thêm'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card className="bg-white dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.06]">
        <CardHeader>
          <CardTitle className="text-gray-900 dark:text-white">Danh sách ngành ({majors?.length || 0})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center p-8">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : majors && majors.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow className="border-gray-200 dark:border-white/[0.06]">
                  <TableHead className="text-gray-600 dark:text-gray-400">Trường</TableHead>
                  <TableHead className="text-gray-600 dark:text-gray-400">Mã ngành</TableHead>
                  <TableHead className="text-gray-600 dark:text-gray-400">Tên ngành</TableHead>
                  <TableHead className="text-gray-600 dark:text-gray-400">Mô tả</TableHead>
                  <TableHead className="text-right text-gray-600 dark:text-gray-400">Thao tác</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {majors.map((major) => (
                  <TableRow key={`${major.truong_id}-${major.major_code}`} className="border-gray-200 dark:border-white/[0.06]">
                    <TableCell className="font-medium text-gray-900 dark:text-white">{major.school_name || '-'}</TableCell>
                    <TableCell className="font-mono text-gray-900 dark:text-white">{major.major_code}</TableCell>
                    <TableCell className="text-gray-900 dark:text-white">{major.major_name}</TableCell>
                    <TableCell className="text-gray-600 dark:text-gray-400">{major.description || '-'}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex gap-2 justify-end">
                        <Button variant="outline" size="icon" onClick={() => handleEdit(major)} className="border-gray-200 dark:border-white/[0.08] hover:bg-gray-100 dark:hover:bg-white/[0.06]">
                          <Pencil className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="destructive"
                          size="icon"
                          onClick={() => {
                            if (confirm('Xóa ngành này?')) deleteMutation.mutate(major.major_code)
                          }}
                          className="bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400 border border-red-500/20"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center p-8 text-gray-500 dark:text-gray-400">Chưa có dữ liệu</div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

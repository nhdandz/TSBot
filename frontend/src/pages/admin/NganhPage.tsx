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

  const { data: majors = [], isLoading } = useQuery({
    queryKey: ['nganh'],
    queryFn: () => adminService.getNganh(),
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
          <h1 className="text-3xl font-bold">Quản lý Ngành</h1>
          <p className="text-muted-foreground mt-1">Danh sách các ngành đào tạo</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-military-600 hover:bg-military-700" onClick={resetForm}>
              <Plus className="w-4 h-4 mr-2" />
              Thêm ngành
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingMajor ? 'Chỉnh sửa ngành' : 'Thêm ngành mới'}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>Mã ngành *</Label>
                <Input
                  value={formData.major_code}
                  onChange={(e) => setFormData({ ...formData, major_code: e.target.value })}
                  placeholder="VD: CNTT"
                  required
                  disabled={!!editingMajor}
                />
              </div>
              <div className="space-y-2">
                <Label>Tên ngành *</Label>
                <Input
                  value={formData.major_name}
                  onChange={(e) => setFormData({ ...formData, major_name: e.target.value })}
                  placeholder="VD: Công nghệ thông tin"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Mô tả</Label>
                <Input
                  value={formData.description || ''}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Mô tả ngành học"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>Hủy</Button>
                <Button type="submit" className="bg-military-600 hover:bg-military-700">
                  {editingMajor ? 'Cập nhật' : 'Thêm'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Danh sách ngành ({majors?.length || 0})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center p-8">
              <Loader2 className="w-8 h-8 animate-spin text-military-600" />
            </div>
          ) : majors && majors.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Trường</TableHead>
                  <TableHead>Mã ngành</TableHead>
                  <TableHead>Tên ngành</TableHead>
                  <TableHead>Mô tả</TableHead>
                  <TableHead className="text-right">Thao tác</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {majors.map((major) => (
                  <TableRow key={`${major.truong_id}-${major.major_code}`}>
                    <TableCell className="font-medium">{major.school_name || '-'}</TableCell>
                    <TableCell className="font-mono">{major.major_code}</TableCell>
                    <TableCell>{major.major_name}</TableCell>
                    <TableCell>{major.description || '-'}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex gap-2 justify-end">
                        <Button variant="outline" size="icon" onClick={() => handleEdit(major)}>
                          <Pencil className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="destructive"
                          size="icon"
                          onClick={() => {
                            if (confirm('Xóa ngành này?')) deleteMutation.mutate(major.major_code)
                          }}
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
            <div className="text-center p-8 text-muted-foreground">Chưa có dữ liệu</div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

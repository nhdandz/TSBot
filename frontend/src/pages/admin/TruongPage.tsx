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
import type { Truong } from '@/types'

export default function TruongPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingSchool, setEditingSchool] = useState<Truong | null>(null)

  const [formData, setFormData] = useState({
    school_id: '',
    school_name: '',
    alias: '',
    location: '',
    website: '',
  })

  // Fetch schools
  const { data: schools, isLoading } = useQuery({
    queryKey: ['truong'],
    queryFn: adminService.getTruong,
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: adminService.createTruong,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['truong'] })
      toast({ title: 'Thành công', description: 'Đã thêm trường mới' })
      setIsDialogOpen(false)
      resetForm()
    },
    onError: (error: any) => {
      toast({
        title: 'Lỗi',
        description: error.detail || 'Không thể thêm trường',
        variant: 'destructive',
      })
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ schoolId, data }: { schoolId: string; data: Partial<Truong> }) =>
      adminService.updateTruong(schoolId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['truong'] })
      toast({ title: 'Thành công', description: 'Đã cập nhật trường' })
      setIsDialogOpen(false)
      resetForm()
    },
    onError: (error: any) => {
      toast({
        title: 'Lỗi',
        description: error.detail || 'Không thể cập nhật trường',
        variant: 'destructive',
      })
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: adminService.deleteTruong,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['truong'] })
      toast({ title: 'Thành công', description: 'Đã xóa trường' })
    },
    onError: (error: any) => {
      toast({
        title: 'Lỗi',
        description: error.detail || 'Không thể xóa trường',
        variant: 'destructive',
      })
    },
  })

  const resetForm = () => {
    setFormData({
      school_id: '',
      school_name: '',
      alias: '',
      location: '',
      website: '',
    })
    setEditingSchool(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (editingSchool) {
      updateMutation.mutate({
        schoolId: editingSchool.school_id,
        data: formData,
      })
    } else {
      createMutation.mutate(formData)
    }
  }

  const handleEdit = (school: Truong) => {
    setEditingSchool(school)
    setFormData({
      school_id: school.school_id,
      school_name: school.school_name,
      alias: school.alias || '',
      location: school.location || '',
      website: school.website || '',
    })
    setIsDialogOpen(true)
  }

  const handleDelete = (schoolId: string) => {
    if (confirm('Bạn có chắc muốn xóa trường này?')) {
      deleteMutation.mutate(schoolId)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Quản lý Trường</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Danh sách các trường quân đội tuyển sinh
          </p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button
              className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-500/25"
              onClick={resetForm}
            >
              <Plus className="w-4 h-4 mr-2" />
              Thêm trường
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-white dark:bg-[#0c0c14] border-gray-200 dark:border-white/[0.08]">
            <DialogHeader>
              <DialogTitle className="text-gray-900 dark:text-white">
                {editingSchool ? 'Chỉnh sửa trường' : 'Thêm trường mới'}
              </DialogTitle>
              <DialogDescription className="text-gray-500 dark:text-gray-400">
                {editingSchool
                  ? 'Cập nhật thông tin trường quân đội'
                  : 'Nhập thông tin trường quân đội mới'}
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="school_id" className="text-gray-700 dark:text-gray-300">Mã trường *</Label>
                <Input
                  id="school_id"
                  value={formData.school_id}
                  onChange={(e) =>
                    setFormData({ ...formData, school_id: e.target.value })
                  }
                  placeholder="VD: MTA"
                  required
                  disabled={!!editingSchool}
                  className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="school_name" className="text-gray-700 dark:text-gray-300">Tên trường *</Label>
                <Input
                  id="school_name"
                  value={formData.school_name}
                  onChange={(e) =>
                    setFormData({ ...formData, school_name: e.target.value })
                  }
                  placeholder="VD: Học viện Kỹ thuật Quân sự"
                  required
                  className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="alias" className="text-gray-700 dark:text-gray-300">Tên viết tắt</Label>
                <Input
                  id="alias"
                  value={formData.alias}
                  onChange={(e) =>
                    setFormData({ ...formData, alias: e.target.value })
                  }
                  placeholder="VD: Học viện KT"
                  className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="location" className="text-gray-700 dark:text-gray-300">Khu vực</Label>
                <Input
                  id="location"
                  value={formData.location}
                  onChange={(e) =>
                    setFormData({ ...formData, location: e.target.value })
                  }
                  placeholder="VD: Miền Bắc"
                  className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="website" className="text-gray-700 dark:text-gray-300">Website</Label>
                <Input
                  id="website"
                  type="url"
                  value={formData.website}
                  onChange={(e) =>
                    setFormData({ ...formData, website: e.target.value })
                  }
                  placeholder="VD: https://mta.edu.vn"
                  className="bg-gray-50 dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.08]"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsDialogOpen(false)}
                  className="border-gray-200 dark:border-white/[0.08] text-gray-700 dark:text-gray-300"
                >
                  Hủy
                </Button>
                <Button
                  type="submit"
                  className="bg-indigo-600 hover:bg-indigo-700 text-white"
                  disabled={createMutation.isPending || updateMutation.isPending}
                >
                  {createMutation.isPending || updateMutation.isPending ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : null}
                  {editingSchool ? 'Cập nhật' : 'Thêm'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card className="bg-white dark:bg-white/[0.04] border-gray-200 dark:border-white/[0.06]">
        <CardHeader>
          <CardTitle className="text-gray-900 dark:text-white">Danh sách trường ({schools?.length || 0})</CardTitle>
          <CardDescription className="text-gray-500 dark:text-gray-400">
            Quản lý thông tin các trường quân đội tuyển sinh
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : schools && schools.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow className="border-gray-200 dark:border-white/[0.06]">
                  <TableHead className="text-gray-600 dark:text-gray-400">Mã trường</TableHead>
                  <TableHead className="text-gray-600 dark:text-gray-400">Tên trường</TableHead>
                  <TableHead className="text-gray-600 dark:text-gray-400">Tên viết tắt</TableHead>
                  <TableHead className="text-gray-600 dark:text-gray-400">Khu vực</TableHead>
                  <TableHead className="text-right text-gray-600 dark:text-gray-400">Thao tác</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {schools.map((school) => (
                  <TableRow key={school.school_id} className="border-gray-200 dark:border-white/[0.06]">
                    <TableCell className="font-mono text-gray-900 dark:text-white">{school.school_id}</TableCell>
                    <TableCell className="font-medium text-gray-900 dark:text-white">{school.school_name}</TableCell>
                    <TableCell className="text-gray-600 dark:text-gray-400">{school.alias || '-'}</TableCell>
                    <TableCell className="text-gray-600 dark:text-gray-400">{school.location || '-'}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex gap-2 justify-end">
                        <Button
                          variant="outline"
                          size="icon"
                          onClick={() => handleEdit(school)}
                          className="border-gray-200 dark:border-white/[0.08] hover:bg-gray-100 dark:hover:bg-white/[0.06]"
                        >
                          <Pencil className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="destructive"
                          size="icon"
                          onClick={() => handleDelete(school.school_id)}
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
            <div className="text-center p-8 text-gray-500 dark:text-gray-400">
              Chưa có dữ liệu. Hãy thêm trường mới.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
